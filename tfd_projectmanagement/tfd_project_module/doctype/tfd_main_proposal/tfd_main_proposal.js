// ============================================================================
//   *** بناء شجرة الـ Logframe (ترتيب صحيح + عرض هرمي منسق) ***
// ============================================================================

async function buildLogframeTree(data) {
    console.log("🚀 تم استدعاء buildLogframeTree بالبيانات:", data);

    // 🧩 ترتيب الأنواع (العلاقات الهرمية)
    const childOrder = {
        Goal: ["Outcome", "Output", "Ind"],
        Outcome: ["Output", "Ind"],
        Output: ["Ind"]
    };

    // 🧠 إنشاء العقد (Nodes)
    const nodes = {};
    data.forEach(it => {
        const type = (it.type || "").trim();
        nodes[it.name] = {
            ...it,
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "",
            order_index: it.order_index || 0
        };
    });

    // 🧩 بناء خريطة الأبناء
    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    // 🧩 استخراج الرقم من الاسم (احتياطي فقط)
    function getNumericCode(name) {
        const match = name ? name.match(/(\d+)/) : null;
        return match ? parseInt(match[1], 10) : 0;
    }

    // 🧠 ترتيب الأبناء حسب النوع + order_index
    const getOrderedChildren = (parentName) => {
        const parent = nodes[parentName];
        const all = childrenMap[parentName] || [];
        const order = childOrder[parent?.type] || [];

        const buckets = new Map(order.map(t => [t, []]));
        const rest = [];

        all.forEach(child => {
            const t = nodes[child]?.type || "";
            (buckets.has(t) ? buckets.get(t) : rest).push(child);
        });

        for (let arr of buckets.values()) {
            arr.sort((a, b) => {
                const orderDiff = (nodes[a].order_index || 0) - (nodes[b].order_index || 0);
                if (orderDiff !== 0) return orderDiff;
                return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
            });
        }

        rest.sort((a, b) => {
            const orderDiff = (nodes[a].order_index || 0) - (nodes[b].order_index || 0);
            if (orderDiff !== 0) return orderDiff;
            return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
        });

        return [...order.flatMap(t => buckets.get(t)), ...rest];
    };

    // 🧩 بناء HTML هرمي باستخدام order_index
    function buildHTML(nodeName, numberingPath) {
        const node = nodes[nodeName];
        const type = node.type || "Item";
        const title = frappe.utils?.escape_html
            ? frappe.utils.escape_html(node.indicator_name1 || node.title || node.name)
            : (node.indicator_name1 || node.title || node.name);

        const colorMap = { Goal: "#0d6efd", Outcome: "#198754", Output: "#0dcaf0", Ind: "#ffc107" };
        const color = colorMap[type] || "#000";

        const label = `${type}.${numberingPath.join(".")}`;

        let html = `<li><strong style="color:${color}">${label}</strong>: ${title}`;
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

    // 🌳 تحديد الجذور (العناصر التي لا تملك أب)
    const isChildSomewhere = new Set(Object.values(childrenMap).flat());
    const roots = data
        .filter(it =>
            !it.parent_tfd_logframe ||
            it.parent_tfd_logframe === "undefined" ||
            it.parent_tfd_logframe === "null" ||
            it.parent_tfd_logframe === ""
        )
        .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
        .map(it => it.name);

    // 🧱 بناء HTML النهائي
    let html = "<ul>";
    roots.forEach((root, idx) => {
        html += buildHTML(root, [idx + 1]);
    });
    html += "</ul>";

    return html;
}


// ============================================================================
//             *** 2. الحدث في DocType TFD Main Proposal ***
// ============================================================================

frappe.ui.form.on("TFD Main Proposal", {
    log_frame_name: function(frm) {
        const logframe_name = frm.doc.log_frame_name;
        if (logframe_name) {
            frappe.call({
                doc: frm.doc,
                method: "get_log_frame",
                args: { log_frame_name: logframe_name.toString() },
            }).done(async (r) => {
                const logframeData = r.message || [];
                console.log("🧩 logframeData from backend:", logframeData);

                // 🧠 بناء الشجرة باستخدام order_index
                const html_output = await buildLogframeTree(logframeData);
                frm.set_value("indicators_and_activities_html", html_output);

                // 🗂️ تعبئة الجداول من البيانات
                frm.doc.project_info = [];
                frm.doc.project_plan = [];

                $.each(logframeData, function(_i, e) {
                    if (!e.activity__name) return;
                    let entry = frm.add_child("project_info");
                    let entry1 = frm.add_child("project_plan");
                    entry.project_name = e.project_name;
                    entry.cost = e.cost;
                    entry.activity__name = e.activity__name;
                    entry1.project_name = e.project_name;
                    entry1.activity_name = e.activity__name;
                });

                refresh_field("project_info");
                refresh_field("project_plan");
            });
        } else {
            frm.set_value("indicators_and_activities_html", "");
        }

        frm.save();
    }
});
