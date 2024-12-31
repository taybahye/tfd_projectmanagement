# # Copyright (c) 2024, Amd Oudah Prosite  and contributors
# # For license information, please see license.txt

# # import frappe
# from frappe.model.document import Document


# class Kobotest(Document):
# 	pass


import frappe
from frappe import _, msgprint 
from frappe.model.document import Document
import requests
import json

class Kobotest(Document):
	@frappe.whitelist()
	def get_form_data():
		try:
			# Debugging message
			frappe.msgprint(_("Starting to fetch data from KoboToolbox..."))

			# KoboToolbox export URL
			rms_url = "https://kf.kobotoolbox.org/private-media/mohammedtaher77511/exports/Formulario_de_autoregistro_de_emergencias_-2806-all_versions-False-_2024-12-30-20-09-58.geojson"

			# Headers for authentication
			rms_headers = {
				"Authorization": "Basic 1ab9cbfa23fbbd141ccbcb07633e09fb881e0baf"
			}

			# Make the request
			response = requests.get(rms_url, headers=rms_headers)

			# Check for HTTP errors
			response.raise_for_status()

			# Parse JSON response
			data = response.json()

			# Debugging: Show fetched data
			frappe.msgprint(_("Data fetched successfully"))
			frappe.msgprint(_(str(data)))

			# Return the data (or handle as needed)
			return data

		except requests.exceptions.RequestException as e:
			# Handle HTTP request errors
			frappe.log_error(f"Error fetching KoboToolbox data: {str(e)}")
			frappe.throw(_("Failed to fetch data from KoboToolbox"))

		except Exception as e:
			# Handle unexpected errors
			frappe.log_error(f"Unexpected error: {str(e)}")
			frappe.throw(_("An unexpected error occurred"))

			# 		print('sssssssssssssssssss')
			# 		print(request)
 


			# 		# Update progress
			# 		if total_records > 0:
			# 			progress = (processed_records / total_records) * 100
			# 			frappe.db.set_value(
			# 				self.doctype, self.name, "progress", progress
			# 			)  # Update progress in the Doctype
			# 			frappe.publish_realtime(
			# 				"update_progress",
			# 				{"progress": progress},
			# 				user=frappe.session.user,
			# 			)
			# 			msgprint(_(progress))

			# 		# Move to the next page
			# 		page += 1

			# 	msgprint(_("Data import completed."))
			# else:
			# 	frappe.throw("Please insert form id")

		# @frappe.whitelist()
		# def get_form_data(self):	
			
		# 		rms_url = f"https://kf.kobotoolbox.org/private-media/mohammedtaher77511/exports/Formulario_de_autoregistro_de_emergencias_-_2806_-_all_versions_-_False_-_2024-12-30-20-09-58.geojson"
		# 		username = "test_1234567@example.com"
		# 		password = "1234567"
		# 		auth_data = {
		# 					"username": username,
		# 					"password": password
		# 				}
		# 		response = requests.get(rms_url, auth=(username, password), data=auth_data)
		# 		request = response.json()
		# 		form_data = request["data"] 
		# 		for page in request["data"]:
		# 			self.get_answer_data(form_id,page["id"],page["name"],page["type"])
					
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