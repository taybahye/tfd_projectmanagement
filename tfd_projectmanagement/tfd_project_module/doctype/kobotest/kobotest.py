# # Copyright (c) 2024, Amd Oudah Prosite  and contributors
# # For license information, please see license.txt

# # import frappe
# from frappe.model.document import Document


# class Kobotest(Document):
# 	pass


import frappe
from frappe.model.document import Document
import requests

class Kobotest(Document):
		@frappe.whitelist()
		def get_form_data(self):	
			
				rms_url = f"https://kf.kobotoolbox.org/private-media/mohammedtaher77511/exports/Formulario_de_autoregistro_de_emergencias_-_2806_-_all_versions_-_False_-_2024-12-30-20-09-58.geojson"
				username = "test_1234567@example.com"
				password = "1234567"
				auth_data = {
							"username": username,
							"password": password
						}
				response = requests.get(rms_url, auth=(username, password), data=auth_data)
				request = response.json()
				form_data = request["data"] 
				for page in request["data"]:
					self.get_answer_data(form_id,page["id"],page["name"],page["type"])
					
		# 			existing_page = frappe.db.exists("Page", {"page": page["id"]})

		# 			if existing_page:
		# 				frappe.db.set_value("Page", existing_page, "page_name", page["name"])
		# 				frappe.db.set_value("Page", existing_page, "description", page["description"])
		# 			else:
		# 				self.append("pages",
		# 				{
		# 					"page": page["id"],
		# 					"page_name": page["name"],
		# 					"description": page["description"]
		# 				})
		# 		return form_data
		# 	else:
		# 		frappe.throw("Pleas insert form id")
	
		# def get_answer_data(self,form_id,pagenumber,pagename,pagetype):
		# 	if self.pwp_project_id:
		# 		form_id = self.pwp_project_id
		# 		rms_get_answers=f"http://rms2.pwpyemen.org/api/v2/serv/projects/{form_id}/forms/{pagenumber}/submissions/data"
		# 		username = "test_1234567@example.com "
		# 		password = "1234567"
		# 		auth_data = {
		# 					"username": username,
		# 					"password": password
		# 				}
		# 		response = requests.get(rms_get_answers, auth=(username, password), data=auth_data)
		# 		request = response.json()  
		# 		form_data = request["data"]
		# 		lastupl=[]
		# 		for page in request["data"]:
		# 			for item in page["answers"]:
		# 				answer  = item.get('answer')
		# 				question = item.get('question')
      
		# 				self.append("answers",{
		# 					"page_number": pagenumber,
		# 						"project_id": form_id,
		# 						"page": pagename,
		# 						"question": question,
        # 						"answer": answer
		# 				})
		# 		return form_data