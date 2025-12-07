// ============================================================================
//   *** دالة بناء الشجرة (ترقيم مستقل لكل نوع + ترتيب حسب Order Index) ***
// ============================================================================
async function buildLogframeTree(data) {
    const nodes = {};
    
    // 1. Prepare Data
    data.forEach(it => {
        const type = (it.type || "").trim();
        nodes[it.name] = { 
            ...it, 
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "Item", 
            order_index: it.order_index || 0 
        };
    });

    // 2. Map Parents to Children
    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    function getNumericCode(name) { 
        const match = name ? name.match(/(\d+)/) : null; 
        return match ? parseInt(match[1], 10) : 0; 
    }

    // 3. Sorting Function (ترتيب حسب Order Index فقط)
    const getOrderedChildren = (parentName) => {
        const all = childrenMap[parentName] || [];
        return all.sort((a, b) => {
            const nodeA = nodes[a];
            const nodeB = nodes[b];
            
            // الترتيب حسب Order Index أولاً
            const orderDiff = (nodeA.order_index || 0) - (nodeB.order_index || 0);
            if (orderDiff !== 0) return orderDiff;
            
            // الترتيب حسب الاسم كاحتياط
            return getNumericCode(nodeA.name) - getNumericCode(nodeB.name);
        });
    };

    // 4. Build HTML (تم تعديل الترقيم ليكون مستقلاً لكل نوع)
    function buildHTML(nodeName, numberingPath) {
        const node = nodes[nodeName];
        const type = node.type;
        const title = node.indicator_name1 || node.title || node.name;
        
        // Colors
        const colorMap = { Goal: "#0d6efd", Outcome: "#198754", Output: "#0dcaf0", Ind: "#ffc107" };
        const color = colorMap[type] || "#000";
        
        // تكوين العنوان
        const label = `${type}.${numberingPath.join(".")}`;

        let html = `<li style="margin-bottom:5px;">
                        <strong style="color:${color}">${label}</strong>: ${title}`;
        
        const kids = getOrderedChildren(nodeName);
        if (kids.length) {
            html += "<ul style='margin-top:5px;'>";
            
            // --- [التعديل هنا] ---
            // إنشاء كائن لتتبع عدد مرات ظهور كل نوع داخل هذا المستوى
            const typeCounts = {}; 

            kids.forEach((childName) => { 
                const childNode = nodes[childName];
                const cType = childNode.type; // نوع الابن (Ind, Outcome, etc)
                
                // تهيئة العداد للنوع إذا كان جديداً، ثم زيادته
                if (!typeCounts[cType]) typeCounts[cType] = 0;
                typeCounts[cType]++;
                
                // نمرر الرقم الخاص بالنوع (typeCounts) بدلاً من الترتيب العام (idx)
                html += buildHTML(childName, [...numberingPath, typeCounts[cType]]); 
            });
            
            html += "</ul>";
        }
        html += "</li>";
        return html;
    }

    // 5. Build Root
    const roots = data.filter(it => !it.parent_tfd_logframe)
                      .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
                      .map(it => it.name);
    
    let html = "<ul>";
    // للجذر أيضاً نستخدم نفس المنطق إذا كان لديك أكثر من Goal
    const rootCounts = {};
    roots.forEach((root) => { 
        const rNode = nodes[root];
        const rType = rNode.type;
        if (!rootCounts[rType]) rootCounts[rType] = 0;
        rootCounts[rType]++;
        html += buildHTML(root, [rootCounts[rType]]); 
    });
    html += "</ul>";
    return html;
}
// ============================================================================
//             *** منطق النموذج (تم حل مشكلة التعليق نهائياً) ***
// ============================================================================

frappe.ui.form.on("TFD Main Proposal", {
    
    // 1️⃣ عند التحميل (Refresh): ممنوع لمس الجداول! عرض فقط.
    refresh: function(frm) {
        if (frm.doc.log_frame_name) {
            frm.trigger('render_view_only'); 
        }
    },

    // 2️⃣ عند تغيير الاسم يدوياً: هنا فقط نملأ الجداول
    log_frame_name: function(frm) {
        if (frm.doc.log_frame_name) {
            frm.trigger('fetch_and_populate');
        } else {
            // تنظيف إذا تم حذف الاسم
            $(frm.fields_dict.indicators_and_activities_html.wrapper).html("");
            frm.doc.project_info = [];
            frm.doc.project_plan = [];
            frm.refresh_field("project_info");
            frm.refresh_field("project_plan");
        }
    },

    // دالة العرض فقط (خفيفة جداً)
    render_view_only: async function(frm) {
        const logframe_name = frm.doc.log_frame_name;
        try {
            const r = await frappe.call({
                doc: frm.doc,
                method: "get_log_frame",
                args: { log_frame_name: logframe_name.toString() }
            });
            const html_output = await buildLogframeTree(r.message || []);
            $(frm.fields_dict.indicators_and_activities_html.wrapper).html(html_output);
        } catch (e) { console.log(e); }
    },

    // دالة التعبئة (تعمل فقط عند الاختيار اليدوي)
    fetch_and_populate: async function(frm) {
        const logframe_name = frm.doc.log_frame_name;
        
        // مؤشر تحميل
        $(frm.fields_dict.indicators_and_activities_html.wrapper).html('<div class="text-muted">جاري جلب البيانات...</div>');

        try {
            const r = await frappe.call({
                doc: frm.doc,
                method: "get_log_frame",
                args: { log_frame_name: logframe_name.toString() }
            });

            const data = r.message || [];
            
            // 1. رسم الشجرة
            const html_output = await buildLogframeTree(data);
            $(frm.fields_dict.indicators_and_activities_html.wrapper).html(html_output);

            // 2. تعبئة جدول واحد فقط (project_info) لتخفيف الحمل
            frm.doc.project_info = [];
            
            $.each(data, function(_i, e) {
                if (!e.activity__name) return;
                let row = frm.add_child("project_info");
                row.project_name = e.project_name;
                row.cost = e.cost;
                row.activity__name = e.activity__name;
            });
            
            frm.refresh_field("project_info");

            // 3. جلب بيانات الهدف
            const resp = await frappe.call({
                doc: frm.doc,
                method: "get_logframe_link",
                args: { logframe_name }
            });
            const d = resp.message || {};
            frm.set_value("overall_project_objective", d.indicator_name1 || "");
            if (frm.fields_dict.order_index) frm.set_value("order_index", d.order_index || 0);
            if (frm.fields_dict.type) frm.set_value("type", d.type || "");

        } catch (err) {
            frappe.msgprint("حدث خطأ في جلب البيانات");
            console.error(err);
        }
    }
});