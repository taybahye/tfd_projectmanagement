// ============================================================================
//   *** بناء شجرة الـ Logframe (ترتيب صحيح + عرض هرمي منسق) ***
// ============================================================================

async function buildLogframeTree(data) {
    console.log("🚀 تم استدعاء buildLogframeTree بالبيانات:", data);

    const childOrder = {
        Goal: ["Outcome", "Output", "Ind"],
        Outcome: ["Output", "Ind"],
        Output: ["Ind"]
    };

    const nodes = {};
    data.forEach(it => {
        const type = (it.type || "").trim();
        nodes[it.name] = {
            ...it,
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "",
            order_index: it.order_index || 0
        };
    });

    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    function getNumericCode(name) {
        const match = name ? name.match(/(\d+)/) : null;
        return match ? parseInt(match[1], 10) : 0;
    }

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

    const children = new Set(Object.values(childrenMap).flat());
    const roots = data
        .filter(it =>
            !it.parent_tfd_logframe ||
            it.parent_tfd_logframe === "undefined" ||
            it.parent_tfd_logframe === "null" ||
            it.parent_tfd_logframe === ""
        )
        .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
        .map(it => it.name);

    let html = "<ul>";
    roots.forEach((root, idx) => {
        html += buildHTML(root, [idx + 1]);
    });
    html += "</ul>";

    return html;
}


// ============================================================================
//             *** الأحداث في DocType TFD Main Proposal ***
// ============================================================================

frappe.ui.form.on("TFD Main Proposal", {
    // عند اختيار Log Frame Name
    async log_frame_name(frm) {
        const logframe_name = frm.doc.log_frame_name;

        if (!logframe_name) {
            frm.set_value("indicators_and_activities_html", "");
            return;
        }

        // =====================================================================
        // 1️⃣ جلب بيانات الـ Logframe لعرضها كشجرة في الحقل HTML
        // =====================================================================
        frappe.call({
            doc: frm.doc,
            method: "get_log_frame",
            args: { log_frame_name: logframe_name.toString() },
        }).done(async (r) => {
            const logframeData = r.message || [];
            console.log("🧩 logframeData from backend:", logframeData);

            const html_output = await buildLogframeTree(logframeData);
            frm.set_value("indicators_and_activities_html", html_output);

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

        // =====================================================================
        // 2️⃣ جلب معلومات إضافية من TFD Logframe Name أو TFD Logframe
        // =====================================================================
        try {
            // نحاول أولاً جلب الرابط إلى TFD Logframe (إذا موجود)
            const logframe_link = await frappe.db.get_value(
                "TFD Logframe Name",
                logframe_name,
                "logframe"
            );

            if (logframe_link && logframe_link.message.logframe) {
                const real_logframe = logframe_link.message.logframe;

                // الآن نجلب القيم المطلوبة من TFD Logframe
                const logframe_details = await frappe.db.get_value(
                    "TFD Logframe",
                    real_logframe,
                    ["order_index", "type", "indicator_name"]
                );

                if (logframe_details && logframe_details.message) {
                    frm.set_value("overall_project_objective", logframe_details.message.indicator_name);
                    frm.set_value("order_index", logframe_details.message.order_index);
                    frm.set_value("type", logframe_details.message.type);
                }
            } else {
                // لو ما في رابط مباشر، نحاول الجلب من TFD Logframe Name نفسه
                const direct = await frappe.db.get_value(
                    "TFD Logframe Name",
                    logframe_name,
                    ["order_index", "type", "indicator_name"]
                );
                if (direct && direct.message) {
                    frm.set_value("overall_project_objective", direct.message.indicator_name);
                    frm.set_value("order_index", direct.message.order_index);
                    frm.set_value("type", direct.message.type);
                }
            }
        } catch (err) {
            console.error(err);
            frappe.msgprint(__("حدث خطأ أثناء جلب بيانات الـ Logframe الإضافية."));
        }

        // حفظ التغييرات بعد كل شيء
     //   frm.save();
    }
});
