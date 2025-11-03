// ============================================================================
//   *** بناء شجرة الـ Logframe (ترتيب صحيح + عرض هرمي منسق) ***
// ============================================================================

async function buildLogframeTree(data) {
    console.log("🚀 تم استدعاء buildLogframeTree بالبيانات:", data);

    // 🧩 ترتيب الأنواع
    const childOrder = {
        Goal: ["Ind", "Outcome"],
        Outcome: ["Ind", "Output"],
        Output: ["Ind"]
    };

    // 🧠 إنشاء العقد (Nodes)
    const nodes = {};
    data.forEach(it => {
        const creationFromBackend = it.indicator_creation
            ? new Date(it.indicator_creation)
            : new Date(8640000000000000); // fallback تاريخ بعيد

        const type = (it.type || "").trim();
        nodes[it.name] = {
            ...it,
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "",
            creation: creationFromBackend
        };
    });

    // 🧩 بناء خريطة الأبناء
    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    const orderValue = node => node.creation.getTime();

    // 🧩 استخراج الرقم من الاسم (Ind-00152 → 152)
    function getNumericCode(name) {
        const match = name.match(/(\d+)/);
        return match ? parseInt(match[1], 10) : 0;
    }

    // 🧠 ترتيب الأبناء حسب النوع + التاريخ + الرقم
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

        // ترتيب كل مجموعة: حسب التاريخ أولاً ثم الرقم
        for (let arr of buckets.values()) {
            arr.sort((a, b) => {
                const dateDiff = orderValue(nodes[a]) - orderValue(nodes[b]);
                if (dateDiff !== 0) return dateDiff;
                return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
            });
        }

        rest.sort((a, b) => {
            const dateDiff = orderValue(nodes[a]) - orderValue(nodes[b]);
            if (dateDiff !== 0) return dateDiff;
            return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
        });

        return [...order.flatMap(t => buckets.get(t)), ...rest];
    };

    // 🧩 بناء HTML بتسلسل هرمي (Goal.1, Ind.1.1, ...)
    function buildHTML(nodeName, numberingPath) {
        const node = nodes[nodeName];
        const type = node.type || "Item";
        const title = frappe.utils?.escape_html
            ? frappe.utils.escape_html(node.indicator_name1 || node.title || node.name)
            : (node.indicator_name1 || node.title || node.name);

        const label = `${type}.${numberingPath.join(".")}`;

        let html = `<li><strong>${label}</strong>: ${title}`;
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

    // 🌳 تحديد الجذور
    const isChildSomewhere = new Set(Object.values(childrenMap).flat());
    const roots = data
        .filter(it => !isChildSomewhere.has(it.name))
        .sort((a, b) => {
            const dateDiff = orderValue(nodes[a]) - orderValue(nodes[b]);
            if (dateDiff !== 0) return dateDiff;
            return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
        })
        .map(it => it.name);

    // 🧱 بناء HTML النهائي
    let html = "<ul>";
    roots.forEach((root, idx) => {
        html += buildHTML(root, [idx + 1]); // يبدأ Goal.1, Goal.2 ...
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

                // 🧠 بناء الشجرة بالعرض الهرمي الجديد
                const html_output = await buildLogframeTree(logframeData);
                frm.set_value("indicators_and_activities_html", html_output);

                // 🗂️ تحديث الجداول
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
