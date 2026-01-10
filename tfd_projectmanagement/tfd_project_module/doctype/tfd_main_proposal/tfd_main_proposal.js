/** * buildLogframeTree: Converts a flat array of data into a hierarchical HTML tree.
 * It handles parent-child relationships, custom sorting, and specific numbering labels.
 */
async function buildLogframeTree(data) {
    const nodes = {};
    
    // 1. Prepare Data: Cleans type names and assigns a default order index.
    data.forEach(it => {
        const type = (it.type || "").trim();
        nodes[it.name] = { 
            ...it, 
            type: type ? type[0].toUpperCase() + type.slice(1).toLowerCase() : "Item", 
            order_index: it.order_index || 0 
        };
    });

    // 2. Map Parents to Children: Groups child record names under their parent record name.
    const childrenMap = {};
    data.forEach(it => {
        const parent = it.parent_tfd_logframe || it.parent || null;
        if (parent) (childrenMap[parent] ||= []).push(it.name);
    });

    // Helper: Extracts numbers from a string (e.g., "Goal.01" -> 1) for sorting.
    function getNumericCode(name) { 
        const match = name ? name.match(/(\d+)/) : null; 
        return match ? parseInt(match[1], 10) : 0; 
    }

    // 3. Sorting Function: Returns children sorted by type priority, then order index, then name.
    const getOrderedChildren = (parentName) => {
        const all = childrenMap[parentName] || [];
        
        const typePriority = { "Ind": 1, "Outcome": 2, "Output": 3, "Activity": 4 };

        return all.sort((a, b) => {
            const nodeA = nodes[a];
            const nodeB = nodes[b];
            
            // Sort by Type (e.g., Indicators first, then Outcomes)
            const weightA = typePriority[nodeA.type] || 99;
            const weightB = typePriority[nodeB.type] || 99;
            if (weightA !== weightB) return weightA - weightB;

            // Sort by manual Order Index
            const orderDiff = (nodeA.order_index || 0) - (nodeB.order_index || 0);
            if (orderDiff !== 0) return orderDiff;
            
            // Sort by Name (numeric comparison)
            return getNumericCode(nodeA.name) - getNumericCode(nodeB.name);
        });
    };

    // 4. Build HTML: Recursively generates <ul> and <li> tags for the tree view.
    function buildHTML(nodeName, numberingPath) {
        const node = nodes[nodeName];
        const type = node.type;
        const id = node.name;

        // Get the Text Description
        let description = node.indicator_name1 || node.indicator_name || node.title || ""; 

        // Fix: Clean up prefixes from description using Regular Expression.
        if (description) {
            description = description.replace(/^[A-Za-z]+\.\d+\s*-\s*/, "");
        }

        // Assign colors based on node type
        const colorMap = { Goal: "#0d6efd", Outcome: "#198754", Output: "#0dcaf0", Ind: "#ffc107" };
        const color = colorMap[type] || "#000";
        
        // Define numbering logic (e.g., Goal.1, Outcome.1.1)
        const parentId = node.parent_tfd_logframe || node.parent;
        const parentNode = parentId ? nodes[parentId] : null;
        const parentType = parentNode ? parentNode.type : "";

        let label = `${type}.${numberingPath.join(".")}`;

        // Special case: Indicators under a Goal
        if (type === "Ind" && parentType === "Goal") {
            const myIndex = numberingPath[numberingPath.length - 1];
            label = `Ind.G.${myIndex}`;
        }

        let fullText = description ? description : id;

        let html = `<li style="margin-bottom:5px;">
                        <strong style="color:${color}">${label}</strong>: ${fullText}`;
        
        // Find and process children nodes
        const kids = getOrderedChildren(nodeName);
        if (kids.length) {
            html += "<ul style='margin-top:5px;'>";
            const typeCounts = {}; 
            kids.forEach((childName) => { 
                const childNode = nodes[childName];
                const cType = childNode.type;
                if (!typeCounts[cType]) typeCounts[cType] = 0;
                typeCounts[cType]++;
                html += buildHTML(childName, [...numberingPath, typeCounts[cType]]); 
            });
            html += "</ul>";
        }
        html += "</li>";
        return html;
    }

    // 5. Build Root: Starts the process from top-level nodes (nodes with no parents).
    const roots = data.filter(it => !it.parent_tfd_logframe)
                    .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
                    .map(it => it.name);
    
    let html = "<ul>";
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
// *** Form Logic (Fixed the freezing/hanging issue permanently) ***
// ============================================================================

frappe.ui.form.on("TFD Main Proposal", {
    
    // 1️⃣ On Refresh: Do not touch tables! Just render the view tree.
    refresh: function(frm) {
        if (frm.doc.log_frame_name) {
            frm.trigger('render_view_only'); 
        }
    },

    // 2️⃣ On manual Name change: Only here we fill the actual tables.
    log_frame_name: function(frm) {
        if (frm.doc.log_frame_name) {
            frm.trigger('fetch_and_populate');
        } else {
            // Cleanup if name is deleted
            $(frm.fields_dict.indicators_and_activities_html.wrapper).html("");
            frm.doc.project_info = [];
            frm.doc.project_plan = [];
            frm.refresh_field("project_info");
            frm.refresh_field("project_plan");
        }
    },

    // render_view_only: Very lightweight display function.
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

    // fetch_and_populate: Data fetching function (runs only on manual selection).
    fetch_and_populate: async function(frm) {
        const logframe_name = frm.doc.log_frame_name;
        
        // Loading indicator
        $(frm.fields_dict.indicators_and_activities_html.wrapper).html('<div class="text-muted">Fetching data...</div>');

        try {
            const r = await frappe.call({
                doc: frm.doc,
                method: "get_log_frame",
                args: { log_frame_name: logframe_name.toString() }
            });

            const data = r.message || [];
            
            // 1. Draw the Tree
            const html_output = await buildLogframeTree(data);
            $(frm.fields_dict.indicators_and_activities_html.wrapper).html(html_output);

            // 2. Populate only one table (project_info) to reduce load
            frm.doc.project_info = [];
            
            $.each(data, function(_i, e) {
                if (!e.activity__name) return;
                let row = frm.add_child("project_info");
                row.project_name = e.project_name;
                row.cost = e.cost;
                row.activity__name = e.activity__name;
            });
            
            frm.refresh_field("project_info");

            // 3. Fetch objective data
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
            frappe.msgprint("An error occurred while fetching data");
            console.error(err);
        }
    }
});