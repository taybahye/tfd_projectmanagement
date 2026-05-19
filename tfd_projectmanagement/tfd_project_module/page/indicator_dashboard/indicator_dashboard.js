frappe.pages['indicator_dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Indicator Dashboard',
        single_column: true
    });

    $(page.main).html(`
        <div class="indicator-filter-section" style="margin-bottom: 20px;">
            <div class="logframe-filter"></div>
        </div>

        <div class="summary-cards"></div>
        <div class="indicator-dashboard-grid"></div>
    `);

    page.logframe_name = frappe.ui.form.make_control({
        parent: page.main.find('.logframe-filter'),
        df: {
            label: 'Logframe Name',
            fieldtype: 'Link',
            fieldname: 'logframe_name',
            options: 'TFD Logframe Name',
            onchange: function() {
                load_dashboard(page);
            }
        },
        render_input: true
    });

    load_dashboard(page);
};

function load_dashboard(page) {
    const logframe_name = page.logframe_name.get_value();

    frappe.call({
        method: 'tfd_projectmanagement.tfd_project_module.page.indicator_dashboard.indicator_dashboard.get_indicator_dashboard',
        args: {
            logframe_name: logframe_name
        },
        freeze: true,
        freeze_message: 'Loading dashboard...',
        callback(r) {
            render_indicator_cards(r.message || []);
        }
    });
}
function render_indicator_cards(indicators) {
    const $grid = $('.indicator-dashboard-grid');
    $grid.empty();

    const indicators_with_data = indicators.filter(indicator => {
        const total = Number(indicator.total) || 0;
        return total > 0;
    });

    if (!indicators_with_data.length) {
        $grid.html(`<div class="empty-state">No indicator data found.</div>`);
        return;
    }

    indicators_with_data.forEach(indicator => {
        const chart_id = `chart-${frappe.utils.get_random(8)}`;
        const chart_values = indicator.items.map(item => Number(item.value) || 0);

        const rows_html = indicator.items
            .filter(item => Number(item.value) > 0)
            .map(item => `
                <div class="indicator-row">
                    <span>${item.type || 'Unknown'}</span>
                    <strong>${Number(item.value) || 0}</strong>
                </div>
            `).join('');

        $grid.append(`
            <div class="indicator-card">
                <div class="indicator-card-header">
                    <div>
                        <div class="indicator-title">${indicator.indicator || ''}</div>
                        <div class="indicator-total">Total: ${Number(indicator.total) || 0}</div>
                    </div>
                </div>

                <div id="${chart_id}" class="indicator-chart"></div>

                <div class="indicator-breakdown">
                    ${rows_html}
                </div>
            </div>
        `);

        new frappe.Chart(`#${chart_id}`, {
            data: {
                labels: indicator.items
                    .filter(item => Number(item.value) > 0)
                    .map(item => item.type || 'Unknown'),
                datasets: [
                    {
                        values: indicator.items
                            .filter(item => Number(item.value) > 0)
                            .map(item => Number(item.value) || 0)
                    }
                ]
            },
            type: 'pie',
            height: 230,
             colors: [
                '#2563eb',
                '#16a34a',
                '#f59e0b',
                '#dc2626',
                '#7c3aed',
                '#0891b2',
                '#db2777',
                '#65a30d'
            ]
        });
    });
}