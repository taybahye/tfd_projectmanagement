frappe.treeview_settings['TFD Logframe'] = {
    breadcrumb: "TFD",
    title: __("TFD Logframe"),
    get_tree_nodes: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.get_logframe_children",
    sort_function: function (a, b) {
        // دالة مساعدة لاكتشاف النوع (إما من الحقل أو من الاسم)
        const getDetectedType = (node) => {
            // 1. إذا كان النوع موجوداً في البيانات، استخدمه
            if (node.data.type) return node.data.type.toLowerCase();
            
            // 2. إذا كان فارغاً، ابحث عنه داخل الاسم (ID)
            // مثال: "test4-Ind.G-1.1" يحتوي على "ind"
            const val = (node.data.value || "").toLowerCase();
            if (val.includes("ind")) return "ind";
            if (val.includes("outcome")) return "outcome";
            if (val.includes("output")) return "output";
            if (val.includes("activity")) return "activity";
            if (val.includes("goal")) return "goal";
            
            return "other";
        };

        const typeA = getDetectedType(a);
        const typeB = getDetectedType(b);

        // قائمة الأولويات (Ind في الأعلى دائماً)
        const typePriority = { 
            "ind": 1, 
            "goal": 2, // عادة Goal هو الأب، لكن للاحتياط
            "outcome": 3, 
            "output": 4, 
            "activity": 5 
        };
        
        const weightA = typePriority[typeA] || 99;
        const weightB = typePriority[typeB] || 99;

        // ⭐ الترتيب الصارم: المجموعات أولاً!
        // إذا اختلف النوع، رتب حسب النوع فوراً ولا تنظر للأرقام
        if (weightA !== weightB) {
            return weightA - weightB;
        }

        // ⭐ الترتيب الرقمي: فقط عندما يكون النوع متشابهاً
        let valA = String(a.data.value || "").trim();
        let valB = String(b.data.value || "").trim();

        return valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' });
    },
    // إعدادات الشجرة الإضافية
    onload: function(treeview) {
        treeview.make_new_node = function(parent_node, parent_label, is_root) {
            // ... كود make_new_node الخاص بك ...
            // يمكنك نسخه من الكود القديم
        }
    }
};