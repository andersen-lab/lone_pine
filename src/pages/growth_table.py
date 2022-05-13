from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dash_table.Format import Format, Scheme

def get_layout():
    df = pd.read_csv( "../../resources/growth_rates.csv" )

    date_first = df["first_date"].values[0]
    date_last = df["last_date"].values[0]

    df = df.drop( columns=["first_date", "last_date"] )

    columns = [
        {'id': "lineage", 'name': "Lineage"},
        {"id": "variant", 'name': 'Variant'},
        {'id': "total_count", 'name': "Total", 'type' : 'numeric'},
        {'id': "recent_counts", 'name': "Last 2 months", 'type' : 'numeric'},
        {'id': "est_proportion", 'name': "Prevalence", 'type' : 'numeric', 'format' : Format( precision=1, scheme=Scheme.percentage ) },
        {'id': "growth_rate", 'name': "Growth rate", 'type' : 'numeric', 'format' : Format( precision=1, scheme=Scheme.percentage )},
    ]

    layout = html.Div( [
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=columns,
            tooltip_header={
                "total_count" : "Total number of genomces sequenced from lineage.",
                "recent_counts" : "Number of genomes sequenced from lineage in past two months.",
                "est_proportion" : f"Lineage prevalence in the community estimated from sequencing data as of {date_last}.",
                "growth_rate" : f"Estimated logisitic growth rate over the past two months ({date_first} to {date_last})."
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
            sort_action="native",
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold',
                'fontFamily': 'sans-serif',
                'borderBottom': '1px solid black',
                'borderTop': '2px solid black',
            },
            style_cell = {
                'fontFamily': 'sans-serif',
                'border': '0'
            },
            style_table={
                'borderBottom': '1px solid black',
                'fontSize': "12px"
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
                    'backgroundColor': '#f0f0f0',
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
        ) ],
        style={
            "width" : "30em",
            "marginLeft" : "auto",
            "marginRight" : "auto",
            "marginBottom" : "20px"
        }
    )

    return layout