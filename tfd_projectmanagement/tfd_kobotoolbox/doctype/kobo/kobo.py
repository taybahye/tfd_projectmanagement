# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

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

    # Fetches all Kobo forms and imports their data into ERPNext
    @frappe.whitelist()
    def get_kobo_all_data(self):
        try:
            response = requests.get(ASSETS_URL, headers=HEADERS)
            if response.status_code != 200:
                frappe.msgprint(f"Error {response.status_code}: {response.text}")
                raise Exception("Failed to Data forms")
            forms = response.json().get("results", [])
            for asset in forms:
                raw_name = asset.get('name')              #doctype_name or form.get("title", f"KoboForm_{name}")
                doctype_name = self._sanitize_doctype_name(raw_name)
                # frappe.msgprint(f"--....>>>>>>>> {asset.get('uid')}: {doctype_name}")
                self.import_kobo_form_data(asset.get('uid'), doctype_name)

            return forms
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_all_data")
            frappe.throw("Failed to Data from Kobo")
            
        # self.import_kobo_form_data("aCBiRZuZjGSsaMpySR78v6", "CLTS_Questionnaire")


    # Fetches Kobo forms list and processes each form metadata
    @frappe.whitelist()
    def get_kobo_forms(self):
        try:
            response = requests.get(ASSETS_URL, headers=HEADERS)
            if response.status_code != 200:
                frappe.msgprint(f"Error {response.status_code}: {response.text}")
                raise Exception("Failed to fetch forms")

            forms = response.json().get("results", [])
            for asset in forms:
                # frappe.msgprint(f"--....>>>>>>>> {asset.get('uid')}: {asset.get('name')}")
                self.get_kobo_form_data(asset.get('uid'), asset.get('name'))

            return forms
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in get_kobo_forms")
            frappe.throw("Failed to fetch forms from Kobo")


    # Retrieves a single Kobo form structure and creates a Doctype if it has data
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


    # Maps a Kobo question to one or more ERPNext DocType fields
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
            # options_str = "\n".join([f"{opt[1]}:{opt[0]}" for opt in options]) if options else ""
            options_str = "\n".join([f"{opt[0]}" for opt in options]) if options else ""
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

  
    # Creates or updates an ERPNext DocType based on a Kobo form structure
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
            # self.get_kobo_form_data(uid, full_doctype_name)

            return {"status": "success", "doctype": full_doctype_name}

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Kobo: Error in create_doctype_from_kobo")
            frappe.throw("Failed to create or update Doctype from Kobo form.")
            
     
    # Validates that all generated fieldnames are unique
    def validate_fieldnames(self, fields):
        """Prevent duplicate fieldnames"""
        seen = set()
        for field in fields:
            if field['fieldname'] in seen:
                frappe.throw(f"Duplicate fieldname detected: {field['fieldname']}")
            seen.add(field['fieldname'])
    
            
    # Safely extracts a readable label from Kobo label formats
    def _safe_label(self, label):
        if isinstance(label, list):
            for l in label:
                if l:
                    return str(l)
            return ""
        return str(label or "")

   
    # Sanitizes a string to be a valid ERPNext DocType name
    def _sanitize_doctype_name(self, name):
        import re
        name = re.sub(r"[^\w\s\-]", "", name)
        name = name.strip().replace(" ", "_")
        if not name or not name[0].isalpha():
            name = "Doc_" + name
        return name


    # Sanitizes and normalizes field names to be valid ERPNext fieldnames
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


    # Imports Kobo form submissions into the generated ERPNext DocType
    @frappe.whitelist()
    def import_kobo_form_data(self, uid, doctype_name):
        try:
            # Delete all existing data before importing new submissions
            frappe.db.delete(doctype_name, {})  # This line deletes all existing records
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
            
            
    
    # Checks whether a Kobo form has no questions and no submissions
    def is_form_empty(self, survey, submissions):
        """تحقق إذا كانت الاستمارة فارغة"""
        return not survey and not submissions
    
    
    
    # Creates a placeholder record when no submissions are available
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
        
    
    # Retrieves form submissions using Kobo API v2 with fallback to v1
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
    

