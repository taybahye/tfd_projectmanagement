# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt


# # ---------------iهذا الاخر مع ال checkbox ----------------------------------------------------------------.............>>>>>>>>>>>>>>>>>>

import frappe
from frappe import _, msgprint
import requests
from frappe.model.document import Document
import hashlib

KOBO_TOKEN = "ad756c586a221ff318cd228436a0321ad1f0504b"
HEADERS = {
    "Authorization": f"Token {KOBO_TOKEN}",
    "Accept": "application/json"
}

ASSETS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"
DATA_URL_BASE = "https://kc.kobotoolbox.org/api/v1/data"
FORM_DETAILS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

class kobo(Document):

    @frappe.whitelist()
    def get_kobo_forms1(self):
        self.import_kobo_form_data("aCBiRZuZjGSsaMpySR78v6", "CLTS_Questionnaire")

    @frappe.whitelist()
    def get_kobo_forms(self):
        try:
            response = requests.get(ASSETS_URL, headers=HEADERS)
            if response.status_code != 200:
                frappe.msgprint(f"Error {response.status_code}: {response.text}")
                raise Exception("Failed to fetch forms")

            forms = response.json().get("results", [])
            for asset in forms:
                self.get_kobo_form_data(asset.get('uid'), asset.get('name'))

            return forms
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_forms")
            frappe.throw("Failed to fetch forms from Kobo")

    @frappe.whitelist()
    def get_kobo_form_data(self, uid, name):
        try:
            url = f"{FORM_DETAILS_URL}{uid}/"
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                frappe.msgprint(f"Error {response.status_code}: {response.text}")
                raise Exception("Failed to fetch form data")

            form = response.json()
            survey = form.get("content", {}).get("survey", [])
            if not survey:
                frappe.throw("No survey questions found in this form.")
                
            submissions = self.get_submissions(uid)
            if self.is_form_empty(survey, submissions):
                frappe.msgprint(f"Form {name} is empty, skipping processing.")
                return

            self.create_doctype_from_kobo(uid, form.get("title"), name)
            return form
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_form_data")
            frappe.throw("Failed to fetch form data from Kobo")

    def map_question_to_field(self, q, choices_map=None, index=0):
        qtype = q.get("type", "")
        
        # Generate unique name with index fallback
        raw_name = q.get("name") or q.get("$autoname") or f"q{index}"
        name = self._sanitize_fieldname(raw_name)
        
        # label = self._safe_label(q.get("label", raw_name))
        label = self._safe_label(q.get("label", f"Question {index+1}"))
        fields = []

        qtype_parts = qtype.split()
        qtype = qtype_parts[0]
        list_name = (
            q.get("select_from_list_name")
            or (qtype_parts[1] if len(qtype_parts) > 1 else "")
        )
        options = choices_map.get(list_name, []) if choices_map else []

        if qtype.startswith("select_one"):
            options_str = "\n".join([f"{opt[1]}:{opt[0]}" for opt in options]) if options else ""
            field = {
                "fieldname": name,
                "label": label,
                "fieldtype": "Select",
                "reqd": 0,
                "default": "",
                "options": options_str
            }
            fields.append(field)

        elif qtype.startswith("select_multiple"):
            for opt in options:
                sub_fieldname = self._sanitize_fieldname(f"{name}_{opt[0]}")
                fields.append({
                    "fieldname": sub_fieldname,
                    "label": f"{label} - {self._safe_label(opt[1])}",
                    "fieldtype": "Check",
                    "reqd": 0,
                    "default": 0
                })

        elif qtype in ["text", "string"]:
            fields.append({
                "fieldname": name,
                "label": label,
                "fieldtype": "Data",
                "reqd": 0,
                "default": ""
            })

        elif qtype in ["integer", "decimal"]:
            fields.append({
                "fieldname": name,
                "label": label,
                "fieldtype": "Int" if qtype == "integer" else "Float",
                "reqd": 0,
                "default": ""
            })

        elif qtype == "note":
            fields.append({
                "fieldname": name,
                "label": label,
                "fieldtype": "Section Break",
                "reqd": 0,
                "default": ""
            })

        else:
            fields.append({
                "fieldname": name,
                "label": label,
                "fieldtype": "Data",
                "reqd": 0,
                "default": ""
            })

        return fields

    @frappe.whitelist()
    def create_doctype_from_kobo(self, uid, name, doctype_name=None):
        try:
            url = f"{FORM_DETAILS_URL}{uid}/"
            res = requests.get(url, headers=HEADERS)
            if res.status_code != 200:
                frappe.msgprint(f"Error {res.status_code}: {res.text}")
                raise Exception("Failed to fetch form details")

            form = res.json()
            raw_name = doctype_name or form.get("title", f"KoboForm_{name}")
            doctype_name = self._sanitize_doctype_name(raw_name)
            all_fields = []
            survey = form.get("content", {}).get("survey", [])
            
             # التحقق من وجود أسئلة
            if not survey :
                frappe.msgprint(f"Form {name} is empty, skipping creation.")
                return {"status": "skipped", "reason": "empty_form"}

			
			 
        
            choices_map = {}
            for choice in form.get("content", {}).get("choices", []):
                list_name = choice.get("list_name")
                if list_name not in choices_map:
                    choices_map[list_name] = []
                choices_map[list_name].append([
                    self._safe_label(choice.get("name")),
                    self._safe_label(choice.get("label"))
                ])


            for idx,q in enumerate(survey):
                fields = self.map_question_to_field(q, choices_map, idx)
                all_fields.extend(fields)

			# Add fieldname validation
            self.validate_fieldnames(all_fields)
            
            full_doctype_name = doctype_name
            existing_doctype = frappe.get_all("DocType", filters={"name": full_doctype_name})

            if existing_doctype:
                frappe.delete_doc("DocType", full_doctype_name, force=1)
                frappe.msgprint(f"Deleted existing Doctype: {full_doctype_name}")

            doctype_doc = frappe.get_doc({
                "doctype": "DocType",
                "name": full_doctype_name,
                "module": "TFD Kobotoolbox",
                "custom": 1,
                "is_custom": 1,
                "fields": [],
                "permissions": [
                    {
                        "role": "System Manager",
                        "read": 1,
                        "write": 1,
                        "create": 1,
                        "delete": 1
                    }
                ],
                "editable_grid": 1,
                "track_changes": 1
            })

            for field in all_fields:
                doctype_doc.append("fields", field)

            doctype_doc.insert()
            frappe.msgprint(f"Doctype {full_doctype_name} created successfully.")
            return {"status": "success", "doctype": full_doctype_name}

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in create_doctype_from_kobo")
            frappe.throw("Failed to create or update Doctype from Kobo form.")
            
    def validate_fieldnames(self, fields):
        """Prevent duplicate fieldnames"""
        seen = set()
        for field in fields:
            if field['fieldname'] in seen:
                frappe.throw(f"Duplicate fieldname detected: {field['fieldname']}")
            seen.add(field['fieldname'])
    
            
    def _safe_label(self, label):
        if isinstance(label, list):
            for l in label:
                if l:
                    return str(l)
            return ""
        return str(label or "")

    def _sanitize_doctype_name(self, name):
        import re
        name = re.sub(r"[^\w\s\-]", "", name)
        name = name.strip().replace(" ", "_")
        if not name or not name[0].isalpha():
            name = "Doc_" + name
        return name

    def _sanitize_fieldname(self, name):
        import re
        # Clean special characters
        clean_name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
        
        # Add hash suffix for long names
        if len(clean_name) > 55:
            suffix = hashlib.md5(clean_name.encode()).hexdigest()[:6]
            clean_name = clean_name[:49] + '_' + suffix
            
        # Final cleanup and truncation
        clean_name = clean_name.strip("_")[:64]
        return clean_name.lower()  # Force lowercase for consistency
        # name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
        # name = name.strip("_")
        # if len(name) > 64:
        #     name = name[:60] + "_fld"
            
        # return name

    @frappe.whitelist()
    def import_kobo_form_data(self, uid, doctype_name):
        try:
            submissions = []
            used_method = ""
            
            
            try:
                v2_url = f"https://kf.kobotoolbox.org/api/v2/assets/{uid}/data.json"
                res_v2 = requests.get(v2_url, headers=HEADERS)
                if res_v2.status_code == 200:
                    submissions = res_v2.json().get("results", [])
                    if submissions:
                        used_method = "v2"
                        # ------------------this is the new recoer -------
                if not submissions:
                    frappe.msgprint(f"No data found for {doctype_name}, creating sample entry.")
                    self.create_sample_entry(doctype_name)
                    return {"status": "sample_created"}
                         # ------------------this is the new recoer -------
            except Exception:
                pass

            if not submissions:
                asset_details_url = f"{FORM_DETAILS_URL}{uid}/"
                res = requests.get(asset_details_url, headers=HEADERS)
                if res.status_code != 200:
                    frappe.throw(f"Failed to fetch asset details: {res.text}")
                asset_data = res.json()
                form_url = asset_data.get("deployment__url")
                if form_url:
                    import re
                    match = re.search(r"/data/(\d+)", form_url)
                    if match:
                        form_numeric_id = match.group(1)
                        v1_url = f"{DATA_URL_BASE}/{form_numeric_id}.json"
                        res_v1 = requests.get(v1_url, headers=HEADERS)
                        if res_v1.status_code == 200:
                            submissions = res_v1.json()
                            if submissions:
                                used_method = "v1"

            if not submissions:
                frappe.throw("No submissions found for this form.")

            count = 0
            for submission in submissions:
                doc_data = {}
                for key, value in submission.items():
                    if key.startswith("_"):
                        continue
                    sanitized_key = self._sanitize_fieldname(key)
                    if isinstance(value, str) and ' ' in value:
                        selected_options = value.split()
                        for opt in selected_options:
                            opt_sanitized = self._sanitize_fieldname(opt)
                            checkbox_field = f"{sanitized_key}_{opt_sanitized}"
                            doc_data[checkbox_field] = 1
                    else:
                        doc_data[sanitized_key] = value
                doc = frappe.get_doc({
                    "doctype": doctype_name,
                    **doc_data
                })
                doc.insert(ignore_permissions=True)
                count += 1

            frappe.msgprint(f"Successfully imported {count} responses into {doctype_name} via {used_method}.")
            return {"status": "success", "count": count}
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in import_kobo_form_data")
            frappe.throw("Error importing data from Kobo")
            
            
    
    
    
    def is_form_empty(self, survey, submissions):
        """تحقق إذا كانت الاستمارة فارغة"""
        return not survey and not submissions
    
    
    
    def create_sample_entry(self, doctype_name):
        """إنشاء إدخال نموذجي عند عدم وجود بيانات"""
        sample_data = {
			"title": "Sample Entry",
			"status": "Draft",
			"notes": "Automatically created sample entry"
		}
        frappe.get_doc({
			"doctype": doctype_name,
			**sample_data
		}).insert(ignore_permissions=True)
        
        
    def get_submissions(self, uid):
        """Fetch submissions for a form using KoBoToolbox API v2 or fallback to v1"""
        submissions = []
        v2_url = f"{ASSETS_URL}{uid}/data.json"
        response_v2 = requests.get(v2_url, headers=HEADERS)
        
        if response_v2.status_code == 200:
            submissions = response_v2.json().get("results", [])
            
        if not submissions:
            asset_details_url = f"{FORM_DETAILS_URL}{uid}/"
            res = requests.get(asset_details_url, headers=HEADERS)
            
            if res.status_code == 200:
                asset_data = res.json()
                form_url = asset_data.get("deployment__url", "")
                
                if form_url:
                    import re
                    match = re.search(r"/data/(\d+)", form_url)
                    if match:
                        form_id = match.group(1)
                        v1_url = f"{DATA_URL_BASE}/{form_id}.json"
                        response_v1 = requests.get(v1_url, headers=HEADERS)
                        if response_v1.status_code == 200:
                            submissions = response_v1.json()
        return submissions
    

        
    
	
	
# # -------------------------------------------------------------------------------.............>>>>>>>>>>>>>>>>>>
# # ---------------iهذا الاخر مع ال checkbox ----------------------------------------------------------------.............>>>>>>>>>>>>>>>>>>


# import frappe
# from frappe import _, msgprint
# import requests
# from frappe.model.document import Document

# KOBO_TOKEN = "ad756c586a221ff318cd228436a0321ad1f0504b"
# HEADERS = {
#     "Authorization": f"Token {KOBO_TOKEN}",
#     "Accept": "application/json"
# }

# ASSETS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"
# DATA_URL_BASE = "https://kc.kobotoolbox.org/api/v1/data"
# FORM_DETAILS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

# class kobo(Document):


	 
#          # Clone_of_CLTS_Questionnaire ----===== aXPyKqnFJbbJnj6WagBMs3
            
#             # CLTS_Questionnaire ----===== aCBiRZuZjGSsaMpySR78v6
            
#             # Doc_123 ----===== aCq6Wbvg6ms4sTUvfUwgi9
#             # self.import_kobo_form_data(uid, full_doctype_name)
        
#     @frappe.whitelist()
#     def get_kobo_forms1(self):
#         self.import_kobo_form_data("aCBiRZuZjGSsaMpySR78v6", "CLTS_Questionnaire")
        
    
    
    
#     @frappe.whitelist()
#     def get_kobo_forms(self):
#         try:
#             response = requests.get(ASSETS_URL, headers=HEADERS)
#             if response.status_code != 200:
#                 frappe.msgprint(f"Error {response.status_code}: {response.text}")
#                 raise Exception("Failed to fetch forms")

#             forms = response.json().get("results", [])
#             for asset in forms:
#                 # msgprint(f"Asset Name: {asset.get('name')}")
#                 # msgprint(f"Owner: {asset.get('owner__username')}")
#                 # msgprint(f"Type: {asset.get('asset_type')}")
#                 # msgprint(f"Deployment Status: {asset.get('deployment_status')}")
#                 labels = asset.get('summary', {}).get('labels', [])
#                 # msgprint(f"Questions: {', '.join(labels)}")
#                 # msgprint(f"UID: {asset.get('uid')}")
#                 self.get_kobo_form_data(asset.get('uid'), asset.get('name'))

#             return forms
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_forms")
#             frappe.throw("Failed to fetch forms from Kobo")

#     @frappe.whitelist()
#     def get_kobo_form_data(self, uid, name):
#         try:
#             url = f"{FORM_DETAILS_URL}{uid}/"
#             response = requests.get(url, headers=HEADERS)
#             if response.status_code != 200:
#                 frappe.msgprint(f"Error {response.status_code}: {response.text}")
#                 raise Exception("Failed to fetch form data")

#             form = response.json()
#             survey = form.get("content", {}).get("survey", [])
#             if not survey:
#                 frappe.throw("No survey questions found in this form.")

#             for question in survey:
#                 msgprint(str(question))

#             self.create_doctype_from_kobo(uid, form.get("title"), name)
#             return form
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_form_data")
#             frappe.throw("Failed to fetch form data from Kobo")

#     def map_question_to_field(self, q, choices_map=None):
#         qtype = q.get("type", "")
#         raw_name = q.get("name") or q.get("$autoname") or "unnamed"
#         name = self._sanitize_fieldname(raw_name)
#         label = self._safe_label(q.get("label", raw_name))
#         fields = []
#         frappe.msgprint(f"qtype----->>>>>>>{qtype}")
#         frappe.msgprint(f"raw_name----->>>>>>>{raw_name}")
#         frappe.msgprint(f"name----->>>>>>>{name}")
#         frappe.msgprint(f"label----->>>>>>>{label}")
        
#         qtype_full = q.get("type", "")
#         qtype_parts = qtype_full.split()
#         qtype = qtype_parts[0]
#         list_name = (
# 			q.get("select_from_list_name")
# 			or (qtype_parts[1] if len(qtype_parts) > 1 else "")
# 		)
#         options = choices_map.get(list_name, []) if choices_map else []
#         frappe.msgprint(f"Options: {options}")

        
		
  
#         frappe.msgprint(f"Processing question: {label} ({name}) of type: {qtype}")
# 		# frappe.msgprint("f")
# 	 	# frappe.msgprint(f"Processing question: {label} ({name}) of type: {qtype}")

# 		# if qtype == "select_one":
# 		# 	field = {
# 		# 		"fieldname": name,
# 		# 		"label": label,
# 		# 		"fieldtype": "Select",
# 		# 		"reqd": 0,
# 		# 		"default": "",
# 		# 		"options": "\n".join(self._safe_label(opt[1]) for opt in options) if options else ""
# 		# 	}
# 		# 	fields.append(field)
		
		
#         if qtype.startswith("select_one"):
#             frappe.msgprint(f"Options ------------>")
#             frappe.msgprint(q.get("select_from_list_name"))
#             frappe.msgprint(qtype.split(" ")[1] if len(qtype.split(" ")) > 1 else "")
#             frappe.msgprint(f"Options ------------>")
            
             
            
#             list_name = q.get("select_from_list_name") or qtype.split(" ")[1] if len(qtype.split(" ")) > 1 else ""
#             options = choices_map.get(list_name, []) if choices_map else []
#             frappe.msgprint(f"uuuuuuuu{options}")
            
#             frappe.msgprint(f"select_from_list_name for {label}: {list_name}")
#             frappe.msgprint(f"Options for {label}: {options}")

#             # if not options:
#             #     frappe.msgprint(f"⚠️ No options found for list: {list_name} in question: {label}")

#             field = {
#                 "fieldname": name,
#                 "label": label,
#                 "fieldtype": "Select",
#                 "reqd": 0,
#                 "default": "",
#                 "options": "\n".join(self._safe_label(opt[1]) for opt in options) if options else ""
#                }
#             fields.append(field)

#         elif qtype.startswith("select_multiple"):
#             list_name = q.get("select_from_list_name") or qtype.split(" ")[1] if len(qtype.split(" ")) > 1 else ""
#             options = choices_map.get(list_name, []) if choices_map else []
#             for opt in options:
#                 sub_fieldname = self._sanitize_fieldname(f"{name}_{opt[0]}")
#                 fields.append({
#                     "fieldname": sub_fieldname,
#                     "label": f"{label} - {self._safe_label(opt[1])}",
#                     "fieldtype": "Check",
#                     "reqd": 0,
#                     "default": 0
#                 })
		
#         elif qtype in ["text", "string"]:
#             fields.append({
#                 "fieldname": name,
#                 "label": label,
#                 "fieldtype": "Data",
#                 "reqd": 0,
#                 "default": ""
#             })

#         elif qtype in ["integer", "decimal"]:
#             fields.append({
#                 "fieldname": name,
#                 "label": label,
#                 "fieldtype": "Int" if qtype == "integer" else "Float",
#                 "reqd": 0,
#                 "default": ""
#             })

#         elif qtype == "note":
#             fields.append({
#                 "fieldname": name,
#                 "label": label,
#                 "fieldtype": "Section Break",
#                 "reqd": 0,
#                 "default": ""
#             })

#         else:
#             fields.append({
#                 "fieldname": name,
#                 "label": label,
#                 "fieldtype": "Data",
#                 "reqd": 0,
#                 "default": ""
#             })

#         return fields


	
#     @frappe.whitelist()
#     def create_doctype_from_kobo(self, uid, name, doctype_name=None):
#         try:
#             url = f"{FORM_DETAILS_URL}{uid}/"
#             res = requests.get(url, headers=HEADERS)
#             if res.status_code != 200:
#                 frappe.msgprint(f"Error {res.status_code}: {res.text}")
#                 raise Exception("Failed to fetch form details")

#             form = res.json()
#             raw_name = doctype_name or form.get("title", f"KoboForm_{name}")
#             doctype_name = self._sanitize_doctype_name(raw_name)
#             all_fields = []
#             survey = form.get("content", {}).get("survey", [])
#             if not survey:
#                 frappe.throw("No survey questions found in this form.")

#             choices_map = {}
#             for choice in form.get("content", {}).get("choices", []):
#                 list_name = choice.get("list_name")
#                 if list_name not in choices_map:
#                     choices_map[list_name] = []
#                 choices_map[list_name].append([
#                     self._safe_label(choice.get("name")),
#                     self._safe_label(choice.get("label"))
#                 ])

#             for q in survey:
#                 if "name" in q or "$autoname" in q:
#                     frappe.msgprint(f"ssssssssssssss ------------>")
#                     frappe.msgprint(f" {choices_map}")
#                     frappe.msgprint(f"------------------------------")
#                     frappe.msgprint(f" {q}")
#                     fields = self.map_question_to_field(q, choices_map)
#                     all_fields.extend(fields)

#             full_doctype_name = doctype_name
#             existing_doctype = frappe.get_all("DocType", filters={"name": full_doctype_name})

#             if existing_doctype:
#                 frappe.delete_doc("DocType", full_doctype_name, force=1)
#                 frappe.msgprint(f"Deleted existing Doctype: {full_doctype_name}")

#             doctype_doc = frappe.get_doc({
#                 "doctype": "DocType",
#                 "name": full_doctype_name,
#                 "module": "TFD Kobotoolbox",
#                 "custom": 1,
#                 "is_custom": 1,
#                 "fields": [],
#                 "permissions": [
#                     {
#                         "role": "System Manager",
#                         "read": 1,
#                         "write": 1,
#                         "create": 1,
#                         "delete": 1
#                     }
#                 ],
#                 "editable_grid": 1,
#                 "track_changes": 1
#             })

#             for field in all_fields:
#                 doctype_doc.append("fields", field)

#             doctype_doc.insert()
#             frappe.msgprint(f"Doctype {full_doctype_name} created successfully.")
#             # Clone_of_CLTS_Questionnaire ----===== aXPyKqnFJbbJnj6WagBMs3
            
#             # CLTS_Questionnaire ----===== aCBiRZuZjGSsaMpySR78v6
            
#             # Doc_123 ----===== aCq6Wbvg6ms4sTUvfUwgi9
#             # self.import_kobo_form_data(uid, full_doctype_name)
#             # frappe.msgprint(f"------------------------------")
#             # frappe.msgprint(f" {full_doctype_name} ----===== {uid}")
#             return {"status": "success", "doctype": full_doctype_name}

#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in create_doctype_from_kobo")
#             frappe.throw("Failed to create or update Doctype from Kobo form.")

#     def _safe_label(self, label):
#         if isinstance(label, list):
#             return " / ".join(str(l) for l in label if l)
#         return str(label or "")

#     def _sanitize_doctype_name(self, name):
#         import re
#         name = re.sub(r"[^\w\s\-]", "", name)
#         name = name.strip().replace(" ", "_")
#         if not name or not name[0].isalpha():
#             name = "Doc_" + name
#         return name

#     def _sanitize_fieldname(self, name):
#         import re
#         name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
#         name = name.strip("_")
#         if len(name) > 64:
#             name = name[:60] + "_fld"
#         return name
    
    
#     @frappe.whitelist()
#     def import_kobo_form_data(self, uid, doctype_name):
#         try:
#             submissions = []
#             used_method = ""
#             try:
#                 v2_url = f"https://kf.kobotoolbox.org/api/v2/assets/{uid}/data.json"
#                 res_v2 = requests.get(v2_url, headers=HEADERS)
#                 if res_v2.status_code == 200:
#                     v2_json = res_v2.json()
#                     submissions = v2_json.get("results", [])
#                     frappe.msgprint(f"ssssssssssssss ------------>")
#                     frappe.msgprint(f"{submissions}")
#                     if submissions:
#                         used_method = "v2"
#                         frappe.msgprint(f"✅ Fetched {len(submissions)} submissions via v2 (no deployment)")
#             except Exception:
#                 pass  # Continue to v1
#             if not submissions:
#                 asset_details_url = f"{FORM_DETAILS_URL}{uid}/"
#                 res = requests.get(asset_details_url, headers=HEADERS)
#                 if res.status_code != 200:
#                     frappe.throw(f"Failed to fetch asset details: {res.text}")
#                     asset_data = res.json()
                    
#                 form_url = asset_data.get("deployment__url")
#                 if form_url:
#                     import re
#                     match = re.search(r"/data/(\d+)", form_url)
#                     if match:
#                         form_numeric_id = match.group(1)
#                         v1_url = f"{DATA_URL_BASE}/{form_numeric_id}.json"
#                         res_v1 = requests.get(v1_url, headers=HEADERS)
#                         if res_v1.status_code == 200:
#                             submissions = res_v1.json()
#                             if submissions:
#                                 used_method = "v1"
#                                 frappe.msgprint(f"✅ Fetched {len(submissions)} submissions via v1 (deployed form)")
#                 else:
#                     frappe.msgprint("⚠️ النموذج غير منشور. سيتم الاكتفاء بمحاولة v2 فقط.")
#             if not submissions:
#                 frappe.throw("🚫 لا توجد استجابات لهذا النموذج حتى الآن. تأكد من إرسال رد واحد على الأقل.")
#             count = 0
#             for submission in submissions:
#                 doc_data = {}
#                 for key, value in submission.items():
#                     if key.startswith("_"):
#                         continue
#                     sanitized_key = self._sanitize_fieldname(key)
#                     doc_data[sanitized_key] = value
#                 doc = frappe.get_doc({
# 					"doctype": doctype_name,
# 					**doc_data
# 				})
#                 doc.insert(ignore_permissions=True)
#                 count += 1
#             frappe.msgprint(f"🎉 {count} استجابة تم استيرادها بنجاح إلى {doctype_name} (عن طريق {used_method})")
#             return {"status": "success", "count": count}
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in smart import_kobo_form_data")
#             frappe.throw("حدث خطأ أثناء استيراد البيانات من Kobo")
    
    



# # -------------------------------------------------------------------------------.............>>>>>>>>>>>>>>>>>>

# choices_map
# {'qn33c92': [['Yes', 'Yes / نعم'], ['No', 'No / لا']], 'yi5dn42': [['Lahj', 'Lahj / لحج'], ['Taiz', 'Taiz / تعز']], 'zb7cu60': [['Al_Musaymeer_1', 'Al Musaymeer / المسيمير'], ['Al_Mudharabah_1', 'Al Mudharabah / المضاربة']], 'ge3mn64': [['Jabal_Habashee', 'Jabal Habashee / جبل حبشي'], ['Al_Muaset', 'Al Muaset / المواسط']], 'uq5wv52': [["Sha'atha", "Sha'atha / شعثاء"], ['Makhran', 'Makhran / مخران']], 'tu16g44': [['Al_Haimah', 'Al Haimah / الحيمة']], 'by5bp05': [['Haraz', 'Haraz / حراز']], 'nx1gk07': [['Al_Aswadi', 'Al Aswadi / الأسودي'], ['Hazman_Al_Asfal', 'Hazman Al Asfal / حزمان الاسفل'], ['bani_jaber', 'Bani Jaber / بني جار']], 'rl42k45': [['يزيد_علي_سيف_ثابت', 'يزيد علي سيف ثابت / يزيد علي سيف ثابت'], ['حاشد_محمد_علوان_سالم', 'حاشد محمد علوان سالم / حاشد محمد علوان سالم'], ['رشاد_محسن_ناصر_مثنى', 'رشاد محسن ناصر مثنى / رشاد محسن ناصر مثنى'], ['علي_احمد_سفيان_احمد', 'علي احمد سفيان احمد / علي احمد سفيان احمد'], ['عبد_الوهاب_محمود_علي_ناصر', 'عبد الوهاب محمود علي ناصر / عبد الوهاب محمود علي ناصر'], ['مسؤلة_قايد_صالح_احمد', 'مسؤلة قايد صالح احمد / مسؤلة قايد صالح احمد']], 'vd17l78': [['محمد_عبدالعليم_نعمان', 'محمد عبدالعليم نعمان / محمد عبدالعليم نعمان'], ['عبدالغني_محمد_علي_قائد', 'عبدالغني محمد علي قائد / عبدالغني محمد علي قائد'], ['امين_عبد_عبدالله_سعيد', 'ابوبكر سلطان محمد مهيوب / ابوبكر سلطان محمد مهيوب'], ['جابر_احمد_يعيد_محمد', 'عبدالحبيب عبدالله شرف / عبدالحبيب عبدالله شرف'], ['اسماعيل_حسن_مصلح', 'اسماعيل حسن مصلح / اسماعيل حسن مصلح'], ['سامية_عبدالله_عبده', 'سامية عبدالله عبده / سامية عبدالله عبده'], ['محمد_عبده_محمد_حسن', 'محمد عبده محمد حسن / محمد عبده محمد حسن'], ['طاهر_علي_محمد_سيف', 'طاهر علي محمد سيف / طاهر علي محمد سيف']], 'kl7bu11': [['1', 'Less than 18 years / أصغر من 18 سنة'], ['2', '18-20 years / 18-20 سنوات'], ['3', '21-29 years / 21-29 سنوات'], ['4', '30-39 years / 30-39 سنوات'], ['5', '40-49 years / 40-49 سنوات'], ['6', '50& above / 50 سنة وأكبر']], 'wc9uy05': [['Male', 'Male / ذكر'], ['Female', 'Female / انثى']], 'fo62q34': [['Single', 'Single / عازب'], ['Married', 'Married / متزوج'], ['Divorced', 'Divorced / مطلق'], ['Widow', 'Widow / ارمل']], 'lx6rw36': [['Host_Community', 'Host Community / مجتمع مضيف'], ['IDP', 'IDP / نازح داخلي']], 'xs6ux07': [['Visual_disability', 'Visual disability / الإعاقة البصرية'], ['hearing_disability', 'hearing disability / إعاقة السمع'], ['mental_disability', 'mental disability / إعاقة ذهنية'], ['physical_disability', 'physical disability / إعاقة جسدية']], 'tq3pu07': [['Yes', 'Yes / نعم'], ['No', 'No / لا']], 'gd1pd33': [['Animals', 'Animals / حيوانات'], ['Humen', 'Humen / انسان']], 'wy33t88': [['Increase_the_disease', 'Increase the disease / زيادة المرض'], ['Causes_an_unpleasant_odor', 'Causes an unpleasant odor / يسبب رائحة كريهة'], ['The_area_is_polluted_and_flies_spread', 'The area is polluted and flies spread / المنطقة ملوثة وينتشر الذباب'], ['Contributes_to_water_pollution', 'Contributes to water pollution / يساهم في تلوث المياه'], ['Other', 'Other / آخرى']], 'yp3et95': [['Yes', 'Yes / نعم'], ['No', 'No / لا']], 'ee9uu14': [['Latrine_with_cesspit_1', 'Latrine with cesspit / مرحاض مع حفرة تصريف'], ['Latrine_with_out_cesspit_1', 'Latrine with out cesspit / مرحاض بدون حفرة تصريف'], ['Open_Hole', 'Open Hole / حفرة مفتوحة'], ['Other', 'Other / آخر']], 'yq5xg56': [['Only_my_HH', 'Only my HH / فقط اسرتي'], ['My_HH_&_nieghbours', 'My HH & nieghbours / اسرتي وجيراني'], ['Other', 'Other / آخرى']], 'sx42a09': [['yes', 'Yes / نعم'], ['no', 'No / لا'], ['i_don_t_use_it_at_all___but_my', "I don't use it at all , but my household does. / أنا لا أستخدمه على الإطلاق، لكن عائلتي تستخدمه."], ['i_don_t_use_it_at_all___and_my', "I don't use it at all , and my household neither / أنا لا أستخدمه على الإطلاق، ولا عائلتي أيضًا"]], 'lb6tz70': [['Habite', 'Habite / العادة'], ['Not_suitable_for_my_community', 'Not suitable for my community / غير مناسب لمجتمعي'], ['Not_comfortable', 'Not comfortable / غير مريح']], 'qq8sp66': [['Sometimes', 'Sometimes / أحيانا'], ['Alwayes', 'Alwayes / دائما']], 'sj3oe29': [['You', 'You / انت'], ['eldurly_people', ' eldurly people / كبار السن'], ['Male_children', 'Male children / الذكور من الاطفال'], ['Female_children', 'Female children / الاناث من الاطفال'], ['Women', 'Women / النساء'], ['Men', 'Men / الرجال']], 'rl58g28': [['Any_time', 'Any time / في اي وقت'], ['Only_in_the_evening', 'Only in the evening / فقط في المساء']], 'go3tx99': [['open_air', 'Open air / في العراء'], ['puplic_latrine', 'Puplic Latrine / مراحيض عامة'], ['nieghbours_latrine', 'Nieghbours latrine / مرحاض الجيران']], 'jo7jv89': [['Sometimes', 'Sometimes / احيانا'], ['Always_(_when_ever_they_need_to_use_latr', 'Always ( when ever they need to use latrine) / (دائما (في اي وقت يحتاجون لاستخدامه']], 'ra12c57': [['Masjed', 'Masjed / مسجد'], ['Schools', 'Schools / مدارس'], ['Other', 'Other / اخرى']], 'fm9mq88': [['Yes,_Sometimes_.', 'Yes, Sometimes . / نعم,احيانا'], ['Yes,_Alaways_.', 'Yes, Alaways . / نعم, دائما'], ['No', 'No / لا']], 'pe6gh96': [['by_stone', 'by stone / بأستخدام الحجر'], ['by_tree_leaves', 'by tree leaves / بأوراق الاشجار'], ['water', 'water / الماء'], ['other', 'other / اخرى']], 'ff8bz03': [['Yes', 'Yes / نعم'], ['No', 'No / لا']], 'no5ei52': [['Lack_of_sanitation_facilities', 'Lack of sanitation facilities / عدم وجود مرافق الصرف الصحي'], ['Facilities_are_overcrowded', 'Facilities are overcrowded / المرافق مكتظة'], ['Health_facilities_are_not_functioning_or', 'Health facilities are not functioning or full / المرافق الصحية لا تعمل أو ممتلئة'], ['Sanitary_facilities_lack_a_sewage_system', 'Sanitary facilities lack a sewage system / تفتقر المرافق الصحية إلى نظام الصرف الصحي'], ['There_are_sewers_in_the_street', 'There are sewers in the street / هناك مجاري في الشارع'], ['Sanitary_facilities_are_not_clean', 'Sanitary facilities are not clean / المرافق الصحية ليست نظيفة'], ['Health_facilities_are_not_separated_for_', 'Health facilities are not separated for men and women / لا يوجد فصل المرافق الصحية للرجال والنساء'], ['Health_facilities_are_difficult_to_acces', 'Health facilities are difficult to access / من الصعب الوصول إلى المرافق الصحية']], 'hw6nt08': [['Treating_water_for_drinking', 'Treating water for drinking / معالجة المياه للشرب'], ['cover_food', 'cover food / تغطية الطعام'], ['wash_hands_with_soap', 'wash hands with soap / غسل اليدين بالصابون'], ['Clean_house', 'Clean house / منزل نظيف'], ['Eat_clean_food', 'Eat clean food / تناول الطعام النظيف'], ['Never_defect_in_open_air', 'Never defect in open air / لا اتغوط أبدًا في العراء'], ['Never_defect_beside_water_sources', 'Never defect beside water sources / لا اتغوط أبدًا بجانب مصادر المياه']], 'to5ap18': [['Before_eating_1', 'Before eating / قبل الأكل'], ['Before_cooking_1', 'Before cooking / قبل الطهي'], ['After_defection_1', 'After defection / بعد التغوط'], ['Before_feeding_children_1', 'Before feeding children / قبل إطعام الأطفال'], ['After_changing_daipers_1', 'After changing daipers / بعد تغيير الحفاضات'], ['Before_breastfeeding_1', 'Before breastfeeding / قبل الرضاعة الطبيعية'], ['I_never_wash_my_hands_1', 'I never wash my hands / أنا لا أغسل يدي أبدا']], 'ad27z43': [['Only_water', 'Only water / فقط ماء'], ['Water_&_Soap', 'Water & Soap / الماء والصابون'], ['Water_&_sand', 'Water & sand / الماء والرمل'], ['Water_&_Ashes', 'Water & Ashes / الماء والرماد']], 'ty4zh31': [['Expensive', 'Expensive / غالي'], ['Not_available_in_the_market', 'Not available in the market / غير متوفر في السوق'], ['Not_necessory', 'Not necessory / ليس ضروريا'], ['Very_difficult_to_reach_to_the_market', 'Very difficult to reach to the market / من الصعب جدًا الوصول إلى السوق']], 'qh4eb51': [['Hand_Pump_/_Pumping_Well', 'Hand Pump / Pumping Well / مضخة يدوية / بئر ضخ'], ['Protected_Well', 'Protected Well / بئر محمي'], ['Tap_/_Water_Supply_Pipes', 'Tap / Water Supply Pipes / الحنفية / أنابيب إمدادات المياه'], ['Unprotected_Well', 'Unprotected Well / بئر غير محمية'], ['Water_Trucking', 'Water Trucking / نقل المياه بالشاحنات'], ['Others', 'Others / اخرى']], 'dq5jf13': [['Yes', 'Yes / نعم'], ['No', 'No / لا']], 'ni17l02': [['Hand_Pump_/_Pumping_Well', 'Treated Water / ماء معالج'], ['Protected_Well', 'Untreated water / ماء غير معالج']], 'cl3dn94': [['Boiling', 'Boiling / بالغلي'], ['Chlorination', 'Chlorination / بالكلورة'], ['Filtering', 'Filtering / تنقية'], ['other', 'Other / اخرى']]}
# ------------------------------
# q
# {'type': 'select_one', '$kuid': 'gx2st92', 'label': ['2.3 Social status ', '2.5 الحالة الاجتماعية'], '$qpath': 'group_js4oh60-_2_3_Social_status', '$xpath': 'group_js4oh60/_2_3_Social_status', 'required': True, '$autoname': '_2_3_Social_status', 'select_from_list_name': 'fo62q34'}
    

# # الكود الشغال كامل زززززززز
# import frappe
# from frappe import _, msgprint
# import requests
# import xml.etree.ElementTree as ET
# from frappe.model.document import Document

# # إعداد التوكن
# KOBO_TOKEN = "ad756c586a221ff318cd228436a0321ad1f0504b"
# HEADERS = {
#     "Authorization": f"Token {KOBO_TOKEN}",
#     "Accept": "application/json"
# }

# ASSETS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"
# DATA_URL_BASE = "https://kc.kobotoolbox.org/api/v1/data"
# FORM_DETAILS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

# class kobo(Document):

#     @frappe.whitelist()
#     def get_kobo_forms(self):
#         try:
#             response = requests.get(ASSETS_URL, headers=HEADERS)
#             if response.status_code != 200:
#                 frappe.msgprint(f"Error {response.status_code}: {response.text}")
#                 raise Exception("Failed to fetch forms")

#             forms = response.json().get("results", [])
#             for asset in forms:
#                 msgprint(f"Asset Name: {asset.get('name')}")
#                 msgprint(f"Owner: {asset.get('owner__username')}")
#                 msgprint(f"Type: {asset.get('asset_type')}")
#                 msgprint(f"Deployment Status: {asset.get('deployment_status')}")
#                 labels = asset.get('summary', {}).get('labels', [])
#                 msgprint(f"Questions: {', '.join(labels)}")
#                 msgprint(f"UID: {asset.get('uid')}")
#                 self.get_kobo_form_data(asset.get('uid'), asset.get('name'))

#             return forms
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_forms")
#             frappe.throw("Failed to fetch forms from Kobo")

#     @frappe.whitelist()
#     def get_kobo_form_data(self, uid, name):
#         try:
#             url = f"{FORM_DETAILS_URL}{uid}/"
#             response = requests.get(url, headers=HEADERS)
#             if response.status_code != 200:
#                 frappe.msgprint(f"Error {response.status_code}: {response.text}")
#                 raise Exception("Failed to fetch form data")

#             form = response.json()
#             survey = form.get("content", {}).get("survey", [])
#             if not survey:
#                 frappe.throw("No survey questions found in this form.")

#             for question in survey:
#                 msgprint(str(question))

#             self.create_doctype_from_kobo(uid, form.get("title"), name)
#             return form
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_form_data")
#             frappe.throw("Failed to fetch form data from Kobo")

#     def map_question_to_field(self, q, choices_map=None):
#         qtype = q.get("type", "")
#         fields = []

#         if qtype.startswith("select_one"):
#             parts = qtype.split(" ")
#             list_name = parts[1] if len(parts) > 1 else ""
#             options = choices_map.get(list_name, []) if choices_map else []
#             field = {
#                 "fieldname": q.get("name"),
#                 "label": self._safe_label(q.get("label", q.get("name"))),
#                 "fieldtype": "Select",
#                 "reqd": 0,
#                 "default": "",
#                 "options": "\n".join(self._safe_label(opt[1]) for opt in options) or "No Options"
#             }
#             fields.append(field)

#         elif qtype.startswith("select_multiple"):
#             parts = qtype.split(" ")
#             list_name = parts[1] if len(parts) > 1 else ""
#             options = choices_map.get(list_name, []) if choices_map else []
#             for opt in options:
#                 fields.append({
#                     "fieldname": f"{q.get('name')}_{opt[0]}",
#                     "label": f"{self._safe_label(q.get('label'))} - {self._safe_label(opt[1])}",
#                     "fieldtype": "Check",
#                     "reqd": 0,
#                     "default": 0
#                 })

#         elif qtype in ["text", "string"]:
#             field = {
#                 "fieldname": q.get("name"),
#                 "label": self._safe_label(q.get("label", q.get("name"))),
#                 "fieldtype": "Data",
#                 "reqd": 0,
#                 "default": ""
#             }
#             fields.append(field)

#         elif qtype in ["integer", "decimal"]:
#             field = {
#                 "fieldname": q.get("name"),
#                 "label": self._safe_label(q.get("label", q.get("name"))),
#                 "fieldtype": "Int" if qtype == "integer" else "Float",
#                 "reqd": 0,
#                 "default": ""
#             }
#             fields.append(field)

#         elif qtype == "note":
#             field = {
#                 "fieldname": q.get("name"),
#                 "label": self._safe_label(q.get("label", q.get("name"))),
#                 "fieldtype": "Section Break",
#                 "reqd": 0,
#                 "default": ""
#             }
#             fields.append(field)

#         else:
#             field = {
#                 "fieldname": q.get("name"),
#                 "label": self._safe_label(q.get("label", q.get("name"))),
#                 "fieldtype": "Data",
#                 "reqd": 0,
#                 "default": ""
#             }
#             fields.append(field)

#         return fields

#     @frappe.whitelist()
#     def create_doctype_from_kobo(self, uid, name, doctype_name=None):
#         try:
#             url = f"{FORM_DETAILS_URL}{uid}/"
#             res = requests.get(url, headers=HEADERS)
#             if res.status_code != 200:
#                 frappe.msgprint(f"Error {res.status_code}: {res.text}")
#                 raise Exception("Failed to fetch form details")

#             form = res.json()
#             raw_name = doctype_name or form.get("title", f"KoboForm_{name}")
#             doctype_name = self._sanitize_doctype_name(raw_name)
#             all_fields = []
#             survey = form.get("content", {}).get("survey", [])
#             if not survey:
#                 frappe.throw("No survey questions found in this form.")

#             choices_map = {}
#             for choice in form.get("content", {}).get("choices", []):
#                 list_name = choice.get("list_name")
#                 if list_name not in choices_map:
#                     choices_map[list_name] = []
#                 choices_map[list_name].append([
#                     self._safe_label(choice.get("name")),
#                     self._safe_label(choice.get("label"))
#                 ])

#             for q in survey:
#                 if "name" in q:
#                     fields = self.map_question_to_field(q, choices_map)
#                     all_fields.extend(fields)

#             full_doctype_name = doctype_name
#             existing_doctype = frappe.get_all("DocType", filters={"name": full_doctype_name})

#             if existing_doctype:
#                 frappe.delete_doc("DocType", full_doctype_name, force=1)
#                 frappe.msgprint(f"Deleted existing Doctype: {full_doctype_name}")

#             doctype_doc = frappe.get_doc({
#                 "doctype": "DocType",
#                 "name": full_doctype_name,
#                 "module": "TFD Kobotoolbox",
#                 "custom": 1,
#                 "is_custom": 1,
#                 "fields": [],
#                 "permissions": [
#                     {
#                         "role": "System Manager",
#                         "read": 1,
#                         "write": 1,
#                         "create": 1,
#                         "delete": 1
#                     }
#                 ],
#                 "editable_grid": 1,
#                 "track_changes": 1
#             })

#             for field in all_fields:
#                 doctype_doc.append("fields", field)

#             doctype_doc.insert()
#             frappe.msgprint(f"Doctype {full_doctype_name} created successfully.")
#             return {"status": "success", "doctype": full_doctype_name}

#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in create_doctype_from_kobo")
#             frappe.throw("Failed to create or update Doctype from Kobo form.")

#     def get_kobo_forms_fields(self):
#         try:
#             forms_response = requests.get(ASSETS_URL, headers=HEADERS)
#             forms_response.raise_for_status()
#             forms = forms_response.json().get('results', [])
#             forms_data = []

#             for form in forms:
#                 form_uid = form['uid']
#                 form_name = form['name']
#                 form_fields = []
#                 deployment_url = f"{ASSETS_URL}{form_uid}/deployment/"
#                 deployment_response = requests.get(deployment_url, headers=HEADERS)
#                 if deployment_response.status_code != 200:
#                     continue
#                 xform_url = deployment_response.json().get('source')
#                 if not xform_url:
#                     continue
#                 xform_response = requests.get(xform_url, headers=HEADERS)
#                 if xform_response.status_code != 200:
#                     continue
#                 root = ET.fromstring(xform_response.text)
#                 for elem in root.iter():
#                     if 'input' in elem.tag or 'select' in elem.tag or 'upload' in elem.tag:
#                         ref = elem.attrib.get('ref') or elem.attrib.get('name')
#                         if ref:
#                             field_name = ref.split('/')[-1]
#                             form_fields.append(field_name)
#                 forms_data.append({
#                     "form_name": form_name,
#                     "fields": form_fields
#                 })
#             return forms_data
#         except Exception:
#             frappe.log_error(title="Kobo Error", message=frappe.get_traceback())
#             return []

#     def _safe_label(self, label):
#         if isinstance(label, list):
#             return " / ".join(str(l) for l in label)
#         return str(label)

#     def _sanitize_doctype_name(self, name):
#         import re
#         name = re.sub(r"[^\w\s\-]", "", name)
#         name = name.strip().replace(" ", "_")
#         if not name or not name[0].isalpha():
#             name = "Doc_" + name
#         return name


# -------------------------------------------

# import frappe
# from frappe import _, msgprint
# import requests
# import xml.etree.ElementTree as ET
# from frappe.model.document import Document

# # إعداد التوكن
# KOBO_TOKEN = "ad756c586a221ff318cd228436a0321ad1f0504b"
# HEADERS = {
#     "Authorization": f"Token {KOBO_TOKEN}",
#     "Accept": "application/json"
# }

# ASSETS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"
# FORM_DETAILS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

# class kobo(Document):
#     @frappe.whitelist()
#     def get_kobo_forms(self):
#         try:
#             response = requests.get(ASSETS_URL, headers=HEADERS)
#             response.raise_for_status()
#             forms = response.json().get("results", [])

#             for asset in forms:
#                 msgprint(f"Asset Name: {asset.get('name')}")
#                 msgprint(f"Owner: {asset.get('owner__username')}")
#                 msgprint(f"Type: {asset.get('asset_type')}")
#                 msgprint(f"Deployment Status: {asset.get('deployment_status')}")
#                 labels = asset.get('summary', {}).get('labels', [])
#                 msgprint(f"Questions: {', '.join(labels)}")
#                 msgprint(f"UID: {asset.get('uid')}")
#                 self.get_kobo_form_data(asset.get('uid'), asset.get('name'))

#             return forms
#         except Exception as e:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_forms")
#             frappe.throw("Failed to fetch forms from Kobo")

#     @frappe.whitelist()
#     def get_kobo_form_data(self, uid, name):
#         try:
#             url = f"{FORM_DETAILS_URL}{uid}/"
#             response = requests.get(url, headers=HEADERS)
#             response.raise_for_status()
#             form = response.json()
#             survey = form.get("content", {}).get("survey", [])

#             if not survey:
#                 frappe.throw("No survey questions found in this form.")

#             for question in survey:
#                 msgprint(str(question))

#             self.create_doctype_from_kobo(uid, name, form.get("title"))
#             return form
#         except Exception as e:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_form_data")
#             frappe.throw("Failed to fetch form data from Kobo")

#     def map_question_to_field(self, q, choices_map=None):
#         qtype = q.get("type", "")
#         field = {
#             "fieldname": q.get("name") or q.get("$autoname"),
#             "label": self._safe_label(q.get("label", q.get("name"))),
#             "reqd": 0,
#             "default": "",
#         }

#         if qtype.startswith("select_one") or qtype.startswith("select_multiple"):
#             list_name = q.get("select_from_list_name")
#             options = choices_map.get(list_name, []) if choices_map else []
#             cleaned_options = [self._safe_label(opt[1]) for opt in options if opt and len(opt) > 1]
#             field.update({
#                 "fieldtype": "Select",
#                 "options": "\n".join(cleaned_options) if cleaned_options else "No Options"
#             })
#         elif qtype in ["text", "string"]:
#             field.update({"fieldtype": "Data"})
#         elif qtype in ["integer", "decimal"]:
#             field.update({"fieldtype": "Int" if qtype == "integer" else "Float"})
#         elif qtype == "note":
#             field.update({"fieldtype": "Section Break"})
#         else:
#             field.update({"fieldtype": "Data"})

#         return field

#     @frappe.whitelist()
#     def create_doctype_from_kobo(self, uid, name, doctype_name=None):
#         url = f"{FORM_DETAILS_URL}{uid}/"
#         res = requests.get(url, headers=HEADERS)
#         res.raise_for_status()
#         form = res.json()

#         doctype_name = doctype_name or form.get("title", f"KoboForm_{name}")
#         fields = []
#         survey = form.get("content", {}).get("survey", [])

#         if not survey:
#             frappe.throw("No survey questions found in this form.")

#         choices_map = {}
#         for choice in form.get("content", {}).get("choices", []):
#             list_name = choice.get("list_name")
#             label = choice.get("label")
#             name = choice.get("name")
#             if list_name not in choices_map:
#                 choices_map[list_name] = []
#             choices_map[list_name].append([
#                 self._safe_label(name),
#                 self._safe_label(label[0] if isinstance(label, list) else label)
#             ])

#         for q in survey:
#             if "name" in q or "$autoname" in q:
#                 fields.append(self.map_question_to_field(q, choices_map))

#         full_doctype_name = doctype_name
#         existing_doctype = frappe.get_all("DocType", filters={"name": full_doctype_name})

#         if existing_doctype:
#             doctype_doc = frappe.get_doc("DocType", existing_doctype[0].name)
#             doctype_doc.set("fields", [])
#             for field in fields:
#                 doctype_doc.append("fields", field)
#             doctype_doc.save()
#             frappe.msgprint(f"Doctype {doctype_name} updated successfully.")
#         else:
#             doctype_doc = frappe.get_doc({
#                 "doctype": "DocType",
#                 "name": "ko" + full_doctype_name,
#                 "module": "TFD Kobotoolbox",
#                 "custom": 1,
#                 "is_custom": 1,
#                 "fields": [],
#                 "permissions": [
#                     {
#                         "role": "System Manager",
#                         "read": 1,
#                         "write": 1,
#                         "create": 1,
#                         "delete": 1
#                     }
#                 ],
#                 "editable_grid": 1,
#                 "track_changes": 1
#             })
#             for field in fields:
#                 doctype_doc.append("fields", field)
#             doctype_doc.insert()
#             frappe.msgprint(f"Doctype {doctype_name} created successfully.")

#         return {"status": "success", "doctype": full_doctype_name}

#     def _safe_label(self, label):
#         if isinstance(label, list):
#             return " / ".join(str(l) for l in label)
#         return str(label or "")


# import frappe
# from frappe import _, msgprint
# import requests
# import xml.etree.ElementTree as ET
# from frappe.model.document import Document

# # إعداد التوكن
# KOBO_TOKEN = "ad756c586a221ff318cd228436a0321ad1f0504b"
# HEADERS = {
#     "Authorization": f"Token {KOBO_TOKEN}",
#     "Accept": "application/json"
# }

# ASSETS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"
# DATA_URL_BASE = "https://kc.kobotoolbox.org/api/v1/data"
# FORM_DETAILS_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

# class kobo(Document):
#     @frappe.whitelist()
#     def get_kobo_forms(self):
#         try:
#             response = requests.get(ASSETS_URL, headers=HEADERS)
#             if response.status_code != 200:
#                 frappe.msgprint(f"Error {response.status_code}: {response.text}")
#                 raise Exception("Failed to fetch forms")

#             forms = response.json().get("results", [])
#             for asset in forms:
#                 msgprint(f"Asset Name: {asset.get('name')}")
#                 msgprint(f"Owner: {asset.get('owner__username')}")
#                 msgprint(f"Type: {asset.get('asset_type')}")
#                 msgprint(f"Deployment Status: {asset.get('deployment_status')}")
#                 labels = asset.get('summary', {}).get('labels', [])
#                 msgprint(f"Questions: {', '.join(labels)}")
#                 msgprint(f"UID: {asset.get('uid')}")
#                 self.get_kobo_form_data(asset.get('uid'), asset.get('name'))

#             return forms
#         except Exception as e:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_forms")
#             frappe.throw("Failed to fetch forms from Kobo")

#     @frappe.whitelist()
#     def get_kobo_form_data(self, uid, name):
#         try:
#             url = f"{FORM_DETAILS_URL}{uid}/"
#             response = requests.get(url, headers=HEADERS)
#             if response.status_code != 200:
#                 frappe.msgprint(f"Error {response.status_code}: {response.text}")
#                 raise Exception("Failed to fetch form data")

#             form = response.json()
#             survey = form.get("content", {}).get("survey", [])
#             if not survey:
#                 frappe.throw("No survey questions found in this form.")

#             for question in survey:
#                 msgprint(str(question))

#             self.create_doctype_from_kobo(uid, form.get("title"), name)
#             return form
#         except Exception as e:
#             frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_form_data")
#             frappe.throw("Failed to fetch form data from Kobo")

#     def map_question_to_field(self, q, choices_map=None):
#         qtype = q.get("type", "")
#         fieldname = q.get("name") or q.get("$autoname")
#         label = self._safe_label(q.get("label", fieldname))

#         if not fieldname:
#             return None

#         if qtype.startswith("select_one") or q.get("select_from_list_name"):
#             list_name = q.get("select_from_list_name") or qtype.split(" ")[1] if " " in qtype else ""
#             options = choices_map.get(list_name, []) if choices_map else []
#             return {
#                 "fieldname": fieldname,
#                 "label": label,
#                 "fieldtype": "Select",
#                 "options": "\n".join(self._safe_label(opt[1]) for opt in options) or "No Options",
#                 "reqd": 0,
#                 "default": ""
#             }

#         elif qtype.startswith("select_multiple"):
#             list_name = q.get("select_from_list_name") or qtype.split(" ")[1] if " " in qtype else ""
#             options = choices_map.get(list_name, []) if choices_map else []
#             fields = []
#             for opt in options:
#                 opt_value = self._safe_label(opt[0])
#                 opt_label = self._safe_label(opt[1])
#                 fields.append({
#                     "fieldname": f"{fieldname}_{opt_value}",
#                     "label": f"{label} - {opt_label}",
#                     "fieldtype": "Check",
#                     "reqd": 0,
#                     "default": 0
#                 })
#             return fields

#         elif qtype in ["text", "string"]:
#             return {
#                 "fieldname": fieldname,
#                 "label": label,
#                 "fieldtype": "Data",
#                 "reqd": 0,
#                 "default": ""
#             }
#         elif qtype in ["integer", "decimal"]:
#             return {
#                 "fieldname": fieldname,
#                 "label": label,
#                 "fieldtype": "Int" if qtype == "integer" else "Float",
#                 "reqd": 0,
#                 "default": ""
#             }
#         elif qtype == "note":
#             return {
#                 "fieldname": fieldname,
#                 "label": label,
#                 "fieldtype": "Section Break",
#                 "reqd": 0,
#                 "default": ""
#             }
#         else:
#             return {
#                 "fieldname": fieldname,
#                 "label": label,
#                 "fieldtype": "Data",
#                 "reqd": 0,
#                 "default": ""
#             }

#     @frappe.whitelist()
#     def create_doctype_from_kobo(self, uid, name, doctype_name=None):
#         url = f"{FORM_DETAILS_URL}{uid}/"
#         res = requests.get(url, headers=HEADERS)

#         if res.status_code != 200:
#             frappe.msgprint(f"Error {res.status_code}: {res.text}")
#             raise Exception("Failed to fetch form details")

#         form = res.json()
#         doctype_name = doctype_name or form.get("title", f"KoboForm_{name}")
#         fields = []
#         survey = form.get("content", {}).get("survey", [])

#         if not survey:
#             frappe.throw("No survey questions found in this form.")

#         choices_map = {}
#         for choice in form.get("content", {}).get("choices", []):
#             list_name = choice.get("list_name")
#             if list_name not in choices_map:
#                 choices_map[list_name] = []
#             choices_map[list_name].append([
#                 self._safe_label(choice.get("name")),
#                 self._safe_label(choice.get("label"))
#             ])

#         for q in survey:
#             if "name" in q or "$autoname" in q:
#                 mapped = self.map_question_to_field(q, choices_map)
#                 if isinstance(mapped, list):
#                     fields.extend(mapped)
#                 elif mapped:
#                     fields.append(mapped)

#         full_doctype_name = doctype_name
#         existing_doctype = frappe.get_all("DocType", filters={"name": full_doctype_name})

#         if existing_doctype:
#             doctype_doc = frappe.get_doc("DocType", existing_doctype[0].name)
#             doctype_doc.set("fields", [])
#             for field in fields:
#                 doctype_doc.append("fields", field)
#             doctype_doc.save()
#             frappe.msgprint(f"Doctype {doctype_name} updated successfully.")
#         else:
#             doctype_doc = frappe.get_doc({
#                 "doctype": "DocType",
#                 "name": "ko" + full_doctype_name,
#                 "module": "TFD Kobotoolbox",
#                 "custom": 1,
#                 "is_custom": 1,
#                 "fields": [],
#                 "permissions": [
#                     {
#                         "role": "System Manager",
#                         "read": 1,
#                         "write": 1,
#                         "create": 1,
#                         "delete": 1
#                     }
#                 ],
#                 "editable_grid": 1,
#                 "track_changes": 1
#             })
#             for field in fields:
#                 doctype_doc.append("fields", field)
#             doctype_doc.insert()
#             frappe.msgprint(f"Doctype {doctype_name} created successfully.")

#         return {"status": "success", "doctype": full_doctype_name}

#     def get_kobo_forms_fields(self):
#         try:
#             forms_response = requests.get(ASSETS_URL, headers=HEADERS)
#             forms_response.raise_for_status()
#             forms = forms_response.json().get('results', [])
#             forms_data = []

#             for form in forms:
#                 form_uid = form['uid']
#                 form_name = form['name']
#                 form_fields = []
#                 deployment_url = f"{ASSETS_URL}{form_uid}/deployment/"
#                 deployment_response = requests.get(deployment_url, headers=HEADERS)
#                 if deployment_response.status_code != 200:
#                     continue
#                 xform_url = deployment_response.json().get('source')
#                 if not xform_url:
#                     continue
#                 xform_response = requests.get(xform_url, headers=HEADERS)
#                 if xform_response.status_code != 200:
#                     continue
#                 root = ET.fromstring(xform_response.text)
#                 for elem in root.iter():
#                     if 'input' in elem.tag or 'select' in elem.tag or 'upload' in elem.tag:
#                         ref = elem.attrib.get('ref') or elem.attrib.get('name')
#                         if ref:
#                             field_name = ref.split('/')[-1]
#                             form_fields.append(field_name)
#                 forms_data.append({
#                     "form_name": form_name,
#                     "fields": form_fields
#                 })
#             return forms_data
#         except Exception as e:
#             frappe.log_error(title="Kobo Error", message=frappe.get_traceback())
#             return []

#     def _safe_label(self, label):
#         if isinstance(label, list):
#             return " / ".join(str(l) for l in label)
#         return str(label)