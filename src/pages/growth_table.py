from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dash_table.Format import Format, Scheme

def get_table( growth_rates ):
    date_first = growth_rates["first_date"].values[0]
    date_last = growth_rates["last_date"].values[0]

    growth_rates = growth_rates.drop( columns=["first_date", "last_date"] )

    columns = [
        {'id': "lineage", 'name': "Lineage"},
        {"id": "variant", 'name': 'Variant'},
        {'id': "total_count", 'name': "Total", 'type' : 'numeric'},
        {'id': "recent_counts", 'name': "Last 2 months", 'type' : 'numeric'},
        {'id': "est_proportion", 'name': "Prevalence", 'type' : 'numeric', 'format' : Format( precision=1, scheme=Scheme.percentage ) },
        {'id': "growth_rate", 'name': "Growth rate", 'type' : 'numeric', 'format' : Format( precision=1, scheme=Scheme.percentage )},
    ]

    table = html.Div( [
        dash_table.DataTable(
            data=growth_rates.to_dict('records'),
            columns=columns,
            tooltip_header={
                "total_count" : "Total number of genomes sequenced from lineage.",
                "recent_counts" : "Number of genomes sequenced from lineage in past two months.",
                "est_proportion" : f"Lineage prevalence in the community estimated from sequencing data as of {date_last}.",
                "growth_rate" : f"Estimated logistic growth rate over the past two months ({date_first} to {date_last})."
            },
            tooltip_delay=0,
            tooltip_duration=None,
            css=[
                { 'selector': '.dash-table-tooltip',
                  'rule': 'font-family: sans-serif; text-align: center; font-size: 12px' },
                { 'selector': '.dash-tooltip',
                  'rule': 'border: 0' },

            ],
            style_as_list_view=True,
            style_header={
                'backgroundColor': '#3C5C94',
                'color': '#F8F9FA',
                'fontWeight': 'bold',
                'fontFamily': 'sans-serif',
            },
            style_cell = {
                'fontFamily': 'sans-serif',
                'border': '0',
                'padding-right': '10px',
                'padding-left': '10px'
            },
            style_table={
                'borderRadius': '5px',
                "overflow" : "hidden",
                'fontSize': "11px",
            },
            style_header_conditional=[
                {
                    'if': { 'column_id': 'variant' },
                    'textAlign': 'center'
                },
                {
                    'if': { 'column_id': 'lineage' },
                    'textAlign': 'left'
                }
            ],
            style_data_conditional=[
                {
                    'if': { 'filter_query': '{growth_rate} > 0.05', 'column_id': 'growth_rate' },
                    'color': 'rgb(200, 0, 0)',
                    'fontWeight': 'bold'
                },
                {
                    'if': { 'filter_query': '{growth_rate} < -0.05', 'column_id': 'growth_rate' },
                    'color': 'rgb(0, 0, 200)',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'row_index': 'odd' },
                    'backgroundColor': '#e9eef6', # was #f0f0f0
                },
                {
                    'if': {'column_id': 'variant'},
                    'textAlign': 'center'
                },
                {
                    'if': { 'column_id': 'lineage' },
                    'textAlign': 'left',
                    'fontStyle': 'italic'
                }
            ]
        ) ]
    )

    return table