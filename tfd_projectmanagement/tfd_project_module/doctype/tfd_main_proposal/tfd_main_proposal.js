// ============================================================================
//   *** بناء شجرة الـ Logframe (ترتيب صحيح + عرض هرمي منسق) ***
// ============================================================================

async function buildLogframeTree(data) {
    console.log("🚀 تم استدعاء buildLogframeTree بالبيانات:", data);

    // ترتيب الأبناء حسب نوع العنصر
    const childOrder = {
        Goal: ["Ind", "Outcome", "Output"],
        Outcome: ["Output", "Ind"],
        Output: ["Ind"]
    };

    // تجهيز العقد (nodes)
    const nodes = {};
    data.forEach(it => {
        const type = (it.type || "").trim();
        nodes[it.name] = {
            ...it,
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "",
            order_index: it.order_index || 0
        };
    });

    // بناء خريطة الأبناء
    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    // دالة لاستخراج رقم من الاسم (لمقارنة رقمية عند الفرز إذا لزم)
    function getNumericCode(name) {
        const match = name ? name.match(/(\d+)/) : null;
        return match ? parseInt(match[1], 10) : 0;
    }

    // دالة لترتيب الأبناء
    const getOrderedChildren = (parentName) => {
        const parent = nodes[parentName];
        const all = childrenMap[parentName] || [];
        const order = childOrder[parent?.type] || [];

        // فصل الأبناء حسب النوع
        const buckets = new Map(order.map(t => [t, []]));
        const rest = [];

        all.forEach(child => {
            const t = nodes[child]?.type || "";
            if (buckets.has(t)) {
                buckets.get(t).push(child);
            } else {
                rest.push(child);
            }
        });

        // ترتيب داخلي لكل مجموعة
        const sorter = (a, b) => {
            const orderDiff = (nodes[a].order_index || 0) - (nodes[b].order_index || 0);
            if (orderDiff !== 0) return orderDiff;
            return getNumericCode(nodes[a].name) - getNumericCode(nodes[b].name);
        };

        for (let arr of buckets.values()) arr.sort(sorter);
        rest.sort(sorter);

        // ضمان أن "Ind" تظهر أولاً إذا كانت ضمن ترتيب الأبناء
        const ordered = [];
        if (order.includes("Ind") && buckets.get("Ind")) {
            ordered.push(...buckets.get("Ind"));
        }
        order.forEach(t => {
            if (t !== "Ind" && buckets.get(t)?.length) ordered.push(...buckets.get(t));
        });

        return [...ordered, ...rest];
    };

    // دالة لبناء HTML هرمي مع الترقيم
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

    // تحديد الجذور (العناصر العليا)
    const roots = data
        .filter(it => !it.parent_tfd_logframe || it.parent_tfd_logframe === "" || it.parent_tfd_logframe === null)
        .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
        .map(it => it.name);

    // بناء HTML نهائي
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
        try {
            const r = await frappe.call({
                doc: frm.doc,
                method: "get_log_frame",
                args: { log_frame_name: logframe_name.toString() },
            });

            const logframeData = r.message || [];
            console.log("🧩 logframeData from backend:", logframeData);

            const html_output = await buildLogframeTree(logframeData);
            frm.set_value("indicators_and_activities_html", html_output);

            // Fill project_info / project_plan from returned rows
            frm.doc.project_info = [];
            frm.doc.project_plan = [];

            $.each(logframeData, function (_i, e) {
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
        } catch (err) {
            console.error("Error fetching logframe rows:", err);
            frappe.msgprint(__("حدث خطأ أثناء جلب بيانات الـ Logframe لعرض الشجرة."));
        }

        // =====================================================================
        // 2️⃣ جلب معلومات الـ Goal (root) من الخادم بشكل آمن
        // =====================================================================
        try {
            const resp = await frappe.call({
                method: "tfd_projectmanagement.tfd_project_module.doctype.tfd_main_proposal.tfd_main_proposal.get_logframe_link",
                args: { logframe_name },
            });

            const details = resp.message || {};

            // always set objective (field exists in your form)
            frm.set_value("overall_project_objective", details.indicator_name1 || "");

            // set order_index and type only if these fields exist in the current form
            if (frm.fields_dict && frm.fields_dict.order_index) {
                frm.set_value("order_index", details.order_index || 0);
            }
            if (frm.fields_dict && frm.fields_dict.type) {
                frm.set_value("type", details.type || "");
            }

        } catch (err) {
            console.error("Error fetching goal details:", err);
            frappe.msgprint(__("حدث خطأ أثناء جلب بيانات الـ Logframe الإضافية."));
        }
    }
});
