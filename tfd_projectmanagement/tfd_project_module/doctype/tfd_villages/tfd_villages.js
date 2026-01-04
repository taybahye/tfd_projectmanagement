
frappe.ui.form.on('TFD Villages', {
    // Triggered when the City field changes
    city: function(frm) {
        if (frm.doc.city) {
            // Filter Directorates based on selected City (Government)
            frm.set_query('directorate', function() {
                return {
                    filters: {
                        'government': frm.doc.city 
                    }
                };
            });
        } else {
            // Clear Directorate filter if no City is selected
            frm.set_query('directorate', function() {
                return {};
            });
        }
    },

    // Triggered when the Directorate field changes
    directorate: function(frm) {
        if (frm.doc.directorate) {
            // Filter Districts based on selected Directorate
            frm.set_query('disticts', function() {
                return {
                    filters: {
                        'directorate': frm.doc.directorate  
                    }
                };
            });
        } else {

            // Clear District filter if no Directorate is selected
            frm.set_query('disticts', function() {
                return {};
            });
        }
    }
});