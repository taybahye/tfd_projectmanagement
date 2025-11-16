// Copyright (c) 2024, Amd Oudah Prosite  and contributors
// For license information, please see license.txt


 frappe.ui.form.on("Kobotest", {
 	refresh(frm) {
     
        


	},
    get(frm){
		alert('هل تريد جلب الاستمارات')
        frappe.call({
			method: "get_form_data",
			doc: frm.doc,
			callback: function(r) {
                frm.refresh_field("sector");
                // frm.refresh_field("answers");	
			}
		});
    },
 });

 function showCustomAlert() {
    // إنشاء العنصر الخاص بالتنبيه
    const alertBox = document.createElement("div");
    alertBox.innerHTML = "هل تريد جلب الاستمارات؟";
    alertBox.style.position = "fixed";
    alertBox.style.top = "50%";
    alertBox.style.left = "50%";
    alertBox.style.transform = "translate(-50%, -50%)";
    alertBox.style.backgroundColor = "#d4edda";
    alertBox.style.color = "#155724";
    alertBox.style.padding = "20px";
    alertBox.style.border = "2px solidrgb(15, 234, 66)";
    alertBox.style.borderRadius = "5px";
    alertBox.style.fontWeight = "bold";
    alertBox.style.fontSize = "20px";
    alertBox.style.textAlign = "righat";
    alertBox.style.zIndex = "9999";

    // إضافة العنصر إلى الصفحة
    document.body.appendChild(alertBox);

    // إزالة التنبيه بعد 3 ثوانٍ
    setTimeout(() => {
        document.body.removeChild(alertBox);
    }, 10000);
}

// استدعاء الدالة
showCustomAlert();
