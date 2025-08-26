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
 
          frm.doc.project_info=[]
          frm.doc.project_plan=[]
          $.each(r.message , function(_i,e)
          {
  
            if (!e.activity__name) {
                // frappe.msgprint(__('Activity name is missing for indicator: {0}', [e.indicator__name]));
                return; // Skip this entry if activity name is not present
            }
            let entry = frm.add_child("project_info");
            let entry1 = frm.add_child("project_plan");
            // entry.indicator = e.indicator__name;
            entry.project_name = e.project_name;
            entry.cost = e.cost;
            entry.activity__name = e.activity__name;
            //==============
            entry1.project_name = e.project_name;
            entry1.activity_name = e.activity__name;

            // entry.activity__name = e.activity__name;
            // entry.indicator__name = e.indicator__name;
            // entry.cost = e.cost;
            // entry.project_name = e.project_name;
            // alert(e.indicator__name)
            // alert(e.activity__name)

            //  alert(e.activity__name)
            // entry.designation=e.designation;
            // entry.vacancies=e.vacancies;
            // entry.estimated_cost_per_position=e.estimated_cost_per_position;
            // entry.number_of_positions=e.number_of_positions;
          })
            refresh_field("project_info")
            refresh_field("project_plan")
          //   set_total_estimated_cost(frm, cdt, cdn);
        })
      }
 },
//   after_save : function(frm) {
//         if (!frm.doc.name) return;

//        console.log("hhhhhhhhhhhhhhhhhhhhhh");
//                 frappe.call({
//                     doc:frm.doc,
//                     method: "get_project_plan",
//                     callback: function(r) {
//                         if (r.message) {
//                             frm.clear_table("project_plan");

//                             r.message.forEach(function(d) {
//                                 let row = frm.add_child("project_plan");
//                                 row.project_name = d.project_name;
//                                 row.activity_name = d.activity__name;
//                             });

//                             frm.refresh_field("project_plan");
                            
//                         }
//                     }
//                 });
//     }

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

 function buildLogframeTree_ol(data) {
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
        finalHtml += buildHTML(root, [index + 0]); // نبدأ من 1 وليس 2
    });
    finalHtml += "</ul>";

    return finalHtml;
}

// مرونة في بناء الشجرة:
// 1) إن وُجد parent_tfd_logframe أو parent → نستخدمه.
// 2) إن لم يوجد → نربط العقدة بأقرب سلف منطقي بناءً على childOrder.
// 3) الترقيم هرمي: Goal.N → Outcome.N.M → Output.N.M.K → Ind.N.M.K.L

function buildLogframeTree(data, opts = {}) {
    // إعدادات قابلة للتخصيص
    const childOrder = opts.childOrder || {
        Goal:   ["Outcome", "Output", "Ind"],  // ممكن مؤشرات مباشرة تحت Goal
        Outcome:["Output", "Ind"],
        Output: ["Ind"]
        // لو عندك Activity أو غيره أضفه هنا: Activity: ["Ind"], ...
    };
    const orderKey = opts.orderKey || null; // مثال: "idx" لو عندك ترتيب مخصص

    // أدوات مساعدة
    const normType = (t) => {
        t = (t || "").trim();
        return t ? t[0].toUpperCase() + t.slice(1).toLowerCase() : "";
    };
    const textOf = (n) => n.indicator_name1 || n.title || n.subject || n.name || "";

    // 1) طبّع الأنواع ورتّب البيانات (اختياريًا على مفتاح orderKey)
    const items = data.map(it => ({...it, type: normType(it.type)}));
    if (orderKey) {
        items.sort((a,b) => {
            const av = a[orderKey] ?? Number.MAX_SAFE_INTEGER;
            const bv = b[orderKey] ?? Number.MAX_SAFE_INTEGER;
            return av === bv ? 0 : (av < bv ? -1 : 1);
        });
    }

    // 2) فهرسة وخرائط
    const nodes = Object.create(null);
    const childrenMap = Object.create(null);
    items.forEach(it => nodes[it.name] = it);

    // مكدّس المسار الحالي لاستخدامه في الإسناد التلقائي عند غياب الـ parent
    let stack = [];

    // إسناد طفل لأب
    const addChild = (parentName, childName) => {
        (childrenMap[parentName] ||= []).push(childName);
    };

    // إيجاد أقرب أب منطقي من المكدّس لِنوع childType
    const findAutoParentFromStack = (childType) => {
        for (let i = stack.length - 1; i >= 0; i--) {
            const anc = nodes[stack[i]];
            const allowed = childOrder[anc?.type] || [];
            if (allowed.includes(childType)) return anc.name;
        }
        return null; // يبقى جذر
    };

    // بناء روابط الأبناء
    for (const node of items) {
        let parentKey = node.parent_tfd_logframe || node.parent || null;

        if (!parentKey) {
            // لا يوجد parent → نبحث أقرب سلف منطقي
            parentKey = findAutoParentFromStack(node.type);
        }

        if (parentKey) {
            addChild(parentKey, node.name);
            // ضبط المكدّس: إن كان الأب موجودًا في المكدّس، نقصّه حتى الأب ثم نضيف الطفل
            const idxInStack = stack.lastIndexOf(parentKey);
            if (idxInStack >= 0) {
                stack = stack.slice(0, idxInStack + 1);
            } else {
                // الأب غير موجود بالمكدّس (مثلاً لم يُمرّ حتى الآن)، لا نقصّ
            }
            stack.push(node.name);
        } else {
            // جذر
            stack = (node.type === "Goal") ? [node.name] : [...stack, node.name];
        }
    }

    // 3) ترتيب أبناء كل أب حسب childOrder (ثم الأنواع غير المتوقعة في النهاية)
    const getOrderedChildren = (parentName) => {
        const parent = nodes[parentName];
        const all = childrenMap[parentName] || [];
        const order = childOrder[parent?.type] || [];

        const buckets = new Map(order.map(t => [t, []]));
        const rest = [];
        for (const child of all) {
            const t = nodes[child]?.type || "";
            (buckets.has(t) ? buckets.get(t) : rest).push(child);
        }
        return [...order.flatMap(t => buckets.get(t)), ...rest];
    };

    // 4) الجذور: لا parent_tfd_logframe ولا parent ولم يُسنَد تلقائيًا (أي ليس في أي childrenMap كطفل)
    const isChildSomewhere = new Set(
        Object.values(childrenMap).flat()
    );
    const roots = items.filter(it => !it.parent_tfd_logframe && !it.parent && !isChildSomewhere.has(it.name));

    // أعرض الـ Goals أولًا ثم غيرها
    const rootOrder = [
        ...roots.filter(r => r.type === "Goal"),
        ...roots.filter(r => r.type !== "Goal")
    ].map(r => r.name);

    // 5) الترقيم الهرمي والإخراج
    function buildHTML(nodeName, numberingPath) {
        const node = nodes[nodeName];
        const label = `${node.type}.${numberingPath.join(".")}`;
        const safeText = (window?.frappe?.utils?.escape_html)
            ? frappe.utils.escape_html(textOf(node))
            : textOf(node);

        let html = `<li><strong>${label}</strong>: ${safeText}`;

        const kids = getOrderedChildren(nodeName);
        if (kids.length) {
            html += "<ul>";
            kids.forEach((childName, idx) => {
                html += buildHTML(childName, [...numberingPath, idx + 1]);
            });
            html += "</ul>";
        }

        html += "</li>";
        return html;
    }

    let finalHtml = "<ul>";
    rootOrder.forEach((rootName, idx) => {
        finalHtml += buildHTML(rootName, [idx + 1]); // Goal.1, Goal.2, ...
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