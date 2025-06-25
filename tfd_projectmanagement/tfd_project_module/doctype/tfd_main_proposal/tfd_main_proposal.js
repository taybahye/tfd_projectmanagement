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
    framework: function(frm) {
      let framework = frm.doc.framework;
  
      if (framework) {
          frappe.call({
              method: "get_indicators",
              doc: frm.doc,
              args: { logframe_name: framework },
  
              callback: (r) => {
                  if (r.message) {
                      console.log("Response received:", r.message);
  
                      // Clear existing rows in the tables
                      frm.clear_table("indicators");
                      frm.clear_table("activities");
  
                      // Create a Set to track unique indicators
                      let addedIndicators = new Set();
  
                      $.each(r.message, function(_i, e) {
                          // Add unique indicators
                          if (!addedIndicators.has(e.indicator)) {
                              let indicator_row = frm.add_child("indicators");
                              indicator_row.indicator = e.indicator;
                              addedIndicators.add(e.indicator);
                          }
  
                          // Add unique activities linked to the indicator
                          let activity_row = frm.add_child("activities");
                          activity_row.activity = e.activity;
                          activity_row.indicator = e.indicator;
                      });
  
                      // Refresh both tables
                      refresh_field("indicators");
                      refresh_field("activities");
                  }
              }
          });
      }
  },
  
  log_frame_name :function(frm)
    {
      // alert('aaa');
      let pro_list=frm.doc.log_frame_name;
      // console.log('pro_list');
    //  console.log(pro_list);
      if(pro_list){
        frappe.call({//mis_config.proposal_module.project_disbursement_level.
          doc: frm.doc,
          method: "get_log_frame",
          // args: {ppst:pro_list.toString()},
          // args: {pro_list.toString()} ,//{ ppst: { pro_list: pro_list.toString() } },
           args: {log_frame_name:pro_list.toString()},
        }).done((r)=>{
           console.log('eeeeeeeeeeeeee')
          // console.log(r)
          console.log(r.message)
          const logframeData = r.message
          indicators_and_activities_htmlff = buildLogframeTree(logframeData);
          // buildLogframeTree(logframeData,frm)
                frm.set_value('indicators_and_activities_html', indicators_and_activities_htmlff);
 
          // frm.doc.staffing_details=[]
          $.each(r.message , function(_i,e)
          {
            // console.log('eeeeeeeeeeeeee')
            // console.log(r.message)
            // alert('aaa');
            // let entry =frm.add_child("staffing_details");
            //  alert(e.logframe_name)
            // entry.designation=e.designation;
            // entry.vacancies=e.vacancies;
            // entry.estimated_cost_per_position=e.estimated_cost_per_position;
            // entry.number_of_positions=e.number_of_positions;
          })
            // refresh_field("staffing_details")
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

 function buildLogframeTree(data) {
    const nodes = {};
    const childrenMap = {};
    const renderedSet = new Set();

    // ربط كل العناصر
    data.forEach(item => {
        nodes[item.name] = item;
        let parentKey = item.parent_tfd_logframe;

        if (!parentKey && item.parentfield === "activities") {
            parentKey = item.parent;
        }

        if (parentKey) {
            if (!childrenMap[parentKey]) {
                childrenMap[parentKey] = [];
            }
            if (!childrenMap[parentKey].includes(item.name)) {
                childrenMap[parentKey].push(item.name);
            }
        }
    });

    // دالة بناء الشجرة مع الترقيم التصاعدي الثابت
    function buildHTML(nodeName, numberingPath = []) {
        if (renderedSet.has(nodeName)) {
            return '';
        }
        renderedSet.add(nodeName);

        const node = nodes[nodeName];

        // تحديث الترقيم
        let currentLevel = numberingPath.length;
        if (!numberingPath[currentLevel - 1]) {
            numberingPath[currentLevel - 1] = 0;
        }
        numberingPath[currentLevel - 1] += 1;

        const currentNumber = numberingPath.join('.');
        const labelPrefix = `${node.type}.${currentNumber}`;

        let html = `<li><strong>${labelPrefix}</strong>: ${node.indicator_name1}`;

        const children = childrenMap[nodeName];
        if (children && children.length) {
            html += "<ul>";
            const newPath = [...numberingPath, 0];
            children.forEach(child => {
                html += buildHTML(child, [...newPath]);
            });
            html += "</ul>";
        }

        html += "</li>";
        return html;
    }

    // اختيار الجذور (اللي ما عندها أب)
    const roots = data.filter(item =>
        !item.parent_tfd_logframe &&
        !(item.parentfield === "activities")
    ).map(item => item.name);

    let finalHtml = "<ul>";
    roots.forEach((root, index) => {
        finalHtml += buildHTML(root, [index + 1]); // نبدأ من 1 وليس 2
    });
    finalHtml += "</ul>";

    return finalHtml;
}



// function buildLogframeTree(data) {
//     const nodes = {};
//     const childrenMap = {};

//     // تجهيز العقد وربط الأبناء
//     data.forEach(item => {
//         nodes[item.name] = item;
//         let parentKey = item.parent_tfd_logframe;

//         if (!parentKey && item.parentfield === "activities") {
//             parentKey = item.parent;
//         }

//         if (parentKey) {
//             if (!childrenMap[parentKey]) {
//                 childrenMap[parentKey] = [];
//             }
//             childrenMap[parentKey].push(item.name);
//         }
//     });

//     // بناء الشجرة بشكل متكرر
//     function buildHTML(nodeName) {
//         const node = nodes[nodeName];
//         let html = `<li><strong>${node.type}</strong>: ${node.indicator_name1}`;
//         const children = childrenMap[nodeName];

//         if (children && children.length) {
//             html += "<ul>";
//             children.forEach(child => {
//                 html += buildHTML(child);
//             });
//             html += "</ul>";
//         }

//         html += "</li>";
//         return html;
//     }

//     // إيجاد العناصر الجذرية (التي ليس لها parent_tfd_logframe ولا parent activities)
//     const roots = data.filter(item =>
//         !item.parent_tfd_logframe &&
//         !(item.parentfield === "activities")
//     ).map(item => item.name);

//     let finalHtml = "<ul>";
//     roots.forEach(root => {
//         finalHtml += buildHTML(root);
//     });
//     finalHtml += "</ul>";

//     console.log(finalHtml); // لعرض الشجرة في وحدة التحكم
//     return finalHtml;
// }