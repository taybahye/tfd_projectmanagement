// ============================================================================
//   *** دالة بناء الشجرة (ألوان فقط - بدون أيقونات) ***
// ============================================================================
async function buildLogframeTree(data) {
    const childOrder = { Goal: ["Ind", "Outcome", "Output"], Outcome: ["Output", "Ind"], Output: ["Ind"] };
    const nodes = {};
    
    // تجهيز البيانات
    data.forEach(it => {
        const type = (it.type || "").trim();
        nodes[it.name] = { 
            ...it, 
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "", 
            order_index: it.order_index || 0 
        };
    });

    // ربط الآباء بالأبناء
    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    function getNumericCode(name) { 
        const match = name ? name.match(/(\d+)/) : null; 
        return match ? parseInt(match[1], 10) : 0; 
    }

    // دالة الترتيب
    const getOrderedChildren = (parentName) => {
        const parent = nodes[parentName];
        const all = childrenMap[parentName] || [];
        const order = childOrder[parent?.type] || [];
        const buckets = new Map(order.map(t => [t, []]));
        const rest = [];

        all.forEach(child => {
            const t = nodes[child]?.type || "";
            if (buckets.has(t)) buckets.get(t).push(child); else rest.push(child);
        });

        const sorter = (a, b) => {
            const orderDiff = (nodes[a].order_index || 0) - (nodes[b].order_index || 0);
            if (orderDiff !== 0) return orderDiff;
            return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
        };

        for (let arr of buckets.values()) arr.sort(sorter);
        rest.sort(sorter);

        const ordered = [];
        if (order.includes("Ind") && buckets.get("Ind")) ordered.push(...buckets.get("Ind"));
        order.forEach(t => { if (t !== "Ind" && buckets.get(t)?.length) ordered.push(...buckets.get(t)); });
        return [...ordered, ...rest];
    };

    // بناء HTML
    function buildHTML(nodeName, numberingPath) {
        const node = nodes[nodeName];
        const type = node.type || "Item";
        const title = node.indicator_name1 || node.title || node.name;
        
        // الألوان فقط كما طلبت
        const colorMap = { Goal: "#0d6efd", Outcome: "#198754", Output: "#0dcaf0", Ind: "#ffc107" };
        const color = colorMap[type] || "#000";
        const label = `${type}.${numberingPath.join(".")}`;

        let html = `<li style="margin-bottom:5px;">
                        <strong style="color:${color}">${label}</strong>: ${title}`;
        
        const kids = getOrderedChildren(nodeName);
        if (kids.length) {
            html += "<ul style='margin-top:5px;'>";
            kids.forEach((childName, idx) => { html += buildHTML(childName, [...numberingPath, idx + 1]); });
            html += "</ul>";
        }
        html += "</li>";
        return html;
    }

    const roots = data.filter(it => !it.parent_tfd_logframe)
                      .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
                      .map(it => it.name);
    
    let html = "<ul>";
    roots.forEach((root, idx) => { html += buildHTML(root, [idx + 1]); });
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