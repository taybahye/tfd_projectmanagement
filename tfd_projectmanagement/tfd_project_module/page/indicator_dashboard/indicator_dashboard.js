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

const parent_colors = [
    '#2563eb',
    '#16a34a',
    '#f59e0b',
    '#dc2626',
    '#7c3aed',
    '#0891b2',
    '#db2777',
    '#65a30d'
];

function lighten_color(hex, percent) {
    const num = parseInt(hex.replace('#', ''), 16);
    const r = Math.min(255, (num >> 16) + percent);
    const g = Math.min(255, ((num >> 8) & 0x00FF) + percent);
    const b = Math.min(255, (num & 0x0000FF) + percent);

    return '#' + (
        0x1000000 +
        (Math.round(r) << 16) +
        (Math.round(g) << 8) +
        Math.round(b)
    ).toString(16).slice(1);
}


function render_indicator_cards(indicators) {
    const $grid = $('.indicator-dashboard-grid');
    $grid.empty();

    const indicators_with_data = indicators.filter(indicator => {
        return Number(indicator.total) > 0;
    });

    if (!indicators_with_data.length) {
        $grid.html(`<div class="empty-state">No indicator data found.</div>`);
        return;
    }

    indicators_with_data.forEach(indicator => {
        const chart_id = `chart-${frappe.utils.get_random(8)}`;
        const parents = indicator.parents || [];

        const rows_html = parents.map(parent => `
            <div class="parent-row">
                <span>${parent.parent_type || 'Without Group'}</span>
                <strong>${Number(parent.total) || 0}</strong>
            </div>

            ${(parent.items || []).map(item => `
                <div class="indicator-row child-row">
                    <span>${item.type || 'Unknown'}</span>
                    <strong>${Number(item.value) || 0}</strong>
                </div>
            `).join('')}
        `).join('');

        $grid.append(`
            <div class="indicator-card">
                <div class="indicator-card-header">
                    <div class="indicator-title">${indicator.indicator || ''}</div>
                    <div class="indicator-total">Total: ${Number(indicator.total) || 0}</div>
                </div>

                <div id="${chart_id}" class="indicator-chart"></div>

                <div class="indicator-breakdown">
                    ${rows_html}
                </div>
            </div>
        `);

        const outer_data = [];
        const inner_data = [];

        const has_parent_groups = parents.some(parent => {
            return parent.parent_type && parent.parent_type !== 'Without Group';
        });

        parents.forEach((parent, parent_index) => {
            const base_color = parent_colors[parent_index % parent_colors.length];

            if (has_parent_groups) {
               outer_data.push({
                    name: parent.parent_type || '',
                    value: Number(parent.total) || 0,
                    target: Number(parent.target) || 0,
                    achievement: Number(parent.achievement) || 0,
                    itemStyle: {
                        color: base_color
                    }
                });

                (parent.items || []).forEach((item, item_index) => {
                   inner_data.push({
                        name: item.type || 'Unknown',
                        value: Number(item.value) || 0,
                        target: Number(item.target) || 0,
                        achievement: Number(item.achievement) || 0,
                        itemStyle: {
                            color: lighten_color(base_color, 35 + (item_index * 25))
                        }
                    });
                });
            } else {
                (parent.items || []).forEach((item, item_index) => {
                    inner_data.push({
                        name: item.type || 'Unknown',
                        value: Number(item.value) || 0,
                        itemStyle: {
                            color: parent_colors[item_index % parent_colors.length]
                        }
                    });
                });
            }
        });

        const chart = echarts.init(document.getElementById(chart_id));
        
        

        let series = [];

        if (has_parent_groups) {

            series = [
                {
                    name: 'Types',
                    type: 'pie',
                    radius: ['28%', '55%'],
                    label: {
                        position: 'inside',
                        fontSize: 11
                    },
                    labelLine: {
                        show: false
                    },
                    data: inner_data
                },
                {
                    name: 'Parent Types',
                    type: 'pie',
                    radius: ['55%', '88%'],
                    label: {
                        formatter: '{b}',
                        fontSize: 11
                    },
                    labelLine: {
                        length: 16,
                        length2: 8
                    },
                    data: outer_data
                }
            ];

        } else {

            series = [
                {
                    name: 'Types',
                    type: 'pie',
                    radius: ['35%', '80%'],
                    label: {
                        formatter: '{b}',
                        fontSize: 11
                    },
                    data: inner_data
                }
            ];
        }
        const indicator_achievement = Number(indicator.achievement || 0).toFixed(1);
       chart.setOption({
            tooltip: {
                trigger: 'item',
                formatter: function(info) {
                    const data = info.data || {};
                    const achievement = Number(data.achievement || 0).toFixed(1);
                    const actual = Number(data.value || 0);
                    const target = Number(data.target || 0);

                    return `
                        <div style="min-width:150px">
                            <div style="font-weight:600;margin-bottom:6px">
                                ${info.name}
                            </div>
                            <div>Achievement: ${achievement}%</div>
                            <div>Actual: ${actual}</div>
                            <div>Target: ${target}</div>
                        </div>
                    `;
                }
            },

            graphic: [
                {
                    type: 'text',
                    left: 'center',
                    top: '42%',
                    style: {
                        text: `${indicator_achievement}%`,
                        textAlign: 'center',
                        fill: '#0f172a',
                        fontSize: 18,
                        fontWeight: 700
                    }
                },
                {
                    type: 'text',
                    left: 'center',
                    top: '51%',
                    style: {
                        text: 'Achievement',
                        textAlign: 'center',
                        fill: '#64748b',
                        fontSize: 10
                    }
                }
            ],

            series: series
        });
    });
}