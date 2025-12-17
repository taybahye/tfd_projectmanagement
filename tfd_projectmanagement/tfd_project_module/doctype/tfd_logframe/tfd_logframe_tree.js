// frappe.treeview_settings['TFD Logframe'] = {
//     breadcrumb: "TFD",
//     title: __("TFD Logframe"),
//     get_tree_nodes:
//         "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.get_logframe_children",

//     sort_function: function (a, b) {

//         const getType = (node) => {
//             if (node.data.type) return node.data.type.toLowerCase();

//             const v = (node.data.value || "").toLowerCase();
//             if (v.startsWith("ind")) return "ind";
//             if (v.startsWith("outcome")) return "outcome";
//             if (v.startsWith("output")) return "output";
//             if (v.startsWith("activity")) return "activity";
//             if (v.startsWith("goal")) return "goal";
//             return "other";
//         };

//         // ⭐ أولوية صارمة جداً
//         const priority = {
//             ind: 1,        // 🔥 دايم أولاً
//             outcome: 2,
//             output: 3,
//             activity: 4,
//             goal: 5
//         };

//         const typeA = getType(a);
//         const typeB = getType(b);

//         const pA = priority[typeA] || 99;
//         const pB = priority[typeB] || 99;

//         // 1️⃣ النوع يحسم الترتيب نهائياً
//         if (pA !== pB) {
//             return pA - pB;
//         }

//         // 2️⃣ ترتيب رقمي فقط داخل نفس النوع
//         const extractNum = (val) => {
//             const m = String(val || "").match(/\d+/);
//             return m ? parseInt(m[0], 10) : 0;
//         };

//         return extractNum(a.data.value) - extractNum(b.data.value);
//     }
// };
