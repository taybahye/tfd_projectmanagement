// Copyright (c) 2024, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

frappe.ui.form.on("TFD Main Proposal", {
    staffing_plan :function(frm)
    {
      let pro_list=frm.doc.staffing_plan
    //  console.log(pro_list);
      if(pro_list){
        frappe.call({//mis_config.proposal_module.project_disbursement_level.
          doc: frm.doc,
          method: "get_staffing",
          args: {staffing_plan:pro_list.toString()},

        }).done((r)=>{
          console.log(r)
          frm.doc.staffing_details=[]
          $.each(r.message , function(_i,e)
          {
            let entry =frm.add_child("staffing_details");
             
            entry.designation=e.designation;
            entry.vacancies=e.vacancies;
            entry.estimated_cost_per_position=e.estimated_cost_per_position;
            entry.number_of_positions=e.number_of_positions;
          })
            refresh_field("staffing_details")
          //   set_total_estimated_cost(frm, cdt, cdn);
        })
      }
    },
});

frappe.ui.form.on('Staffing Plan Detail', {
    estimated_cost_per_position(frm, cdt, cdn) {
        updateTotalEstimatedCost(frm, cdt, cdn);
    },
});

const updateTotalEstimatedCost = (frm, cdt, cdn) => {
    const row = locals[cdt][cdn];
    const hasValidInputs = row.vacancies > 0 && row.estimated_cost_per_position;

    frappe.model.set_value(cdt, cdn, 'total_estimated_cost', 
        hasValidInputs ? row.vacancies * row.estimated_cost_per_position : 0
    );

    updateEstimatedBudget(frm);
};

const updateEstimatedBudget = (frm) => {
    const totalBudget = (frm.doc.staffing_details || [])
        .reduce((sum, detail) => sum + (detail.total_estimated_cost || 0), 0);

    frm.set_value('total_estimated_budget', totalBudget);
};

