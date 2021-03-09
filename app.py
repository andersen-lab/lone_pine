# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import data_wrangling.format_resources as format_data
import dashboard.plot as dashplot
from dash.dependencies import Input, Output


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash( __name__, external_stylesheets=external_stylesheets )
server = app.server

sequences = format_data.load_sequences()
cases_whole = format_data.load_cases()

markdown_text = '''
## SARS-CoV-2 Genomics
To gain insights into the emergence, spread, and transmission of COVID-19 in our community, we are working with a large 
number of parterns to sequence SARS-CoV-2 samples from patients in San Diego. This dashboard provides up-to-date 
information on the number and locations of our sequencing within San Diego County. Consensus sequences are deposited on 
GISAID, NCBI under the [BioProjectID](https://www.ncbi.nlm.nih.gov/bioproject/612578), and the 
[Andersen Lab Github repository](https://github.com/andersen-lab/HCoV-19-Genomics).
'''

app.layout = html.Div( children=[
    html.Div( style={ "backgroundColor" : "#2B4267", "height" : 10 } ),
    html.Div( [dcc.Markdown( markdown_text ),
               html.P() ] ),
    html.Div( [
        html.Div( [
            html.Div( [
                html.H5( "ZIP code" ),
                dcc.Dropdown( id = 'zip-drop',
                              options=[{"label" : i, "value": i } for i in cases_whole["ziptext"].sort_values().unique()],
                              multi=False,
                              placeholder="Select a ZIP code"
                              )
            ],
                className="four columns" ),
            html.Div( [
                html.H5( "Recency" ),
                dcc.Dropdown( id = 'recency-drop',
                              options=[
                                  { 'label' : "Last week", 'value': 7},
                                  { 'label' : "Last month", 'value' : 30 },
                                  { 'label' : "Last 6 month", 'value' : 183 },
                                  { 'label' : "Last year", 'value' : 365 },
                                  { 'label' : "All", 'value' : 1000 }
                              ],
                              value=1000,
                              multi=False,
                              clearable=False,
                              searchable=False
                              )
            ],
                className="four columns" ),
            html.Div( [
                html.H5( "Color by" ),
                dcc.RadioItems(
                    id='color-type',
                    options=[{'label': "Total", 'value': 'sequences'},
                             {'label': "Fraction", 'value': "fraction"}],
                    value='sequences',
                    labelStyle={'display': 'inline-block'}
                )
            ],
                className="four columns" )
        ] )
    ],
        style={ "marginLeft" : "auto",
                "marginRight" : "auto" },
        className="pretty_container row"
    ),
    html.Div(
        dcc.Graph(
            id='choropleth-graph',
            config={'displayModeBar': False},
            style={ "height" : "500px" }
        ),
        className="pretty_container",
        style={ "marginLeft" : "auto",
                "marginRight" : "auto"}
    ),
    html.Div( [
        html.Div(
            dcc.Graph(
                id="cum-graph",
                config={'displayModeBar': False},
                style={ "height" : "25em" }
            ),
            className="pretty_container four columns"
        ),
        html.Div(
            dcc.Graph(
                id="daily-graph",
                config={'displayModeBar': False},
                style={ "height" : "25em" }
            ),
            className="pretty_container four columns"

        ),
        html.Div(
            dcc.Graph(
                id="fraction-graph",
                config={'displayModeBar': False},
                style={ "height" : "25em" }
            ),
            className="pretty_container four columns"
        ),
    ], className="row",
       style={ "marginLeft" : "auto",
               "marginRight" : "auto" }

    ),
    html.Div( style={ "backgroundColor" : "#2B4267", "height"  : 10 } )
],
    style={ "marginLeft" : "auto",
            "marginRight" : "auto",
            "maxWidth" : "80em" }
)
# TODO: Add download button to download metadata associated with current filtered data.

@app.callback(
    Output( "choropleth-graph", "figure"),
    [Input( "recency-drop", "value" ),
     Input( 'color-type', "value")]
)
def update_choropleth( window, colortype ):
    new_sequences = sequences.loc[sequences["days_past"] <= window]
    new_cases = format_data.format_cases_total( cases_whole.loc[cases_whole["days_past"] <= window] )
    return dashplot.plot_choropleth( format_data.format_shapefile( new_cases, new_sequences ), colortype )

@app.callback(
    Output( "cum-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" )]
)
def update_cummulative_graph( window, zip_f ):
    new_sequences = sequences.loc[sequences["days_past"] <= window]
    new_cases_ts = format_data.format_cases_timeseries( cases_whole.loc[cases_whole["days_past"] <= window] )
    new_seqs_per_case = format_data.get_seqs_per_case( new_cases_ts, new_sequences, zip_f=zip_f )

    return dashplot.plot_cummulative_cases_seqs( new_seqs_per_case )

@app.callback(
    Output( "daily-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" )]
)
def update_cummulative_graph( window, zip_f ):
    new_sequences = sequences.loc[sequences["days_past"] <= window]
    new_cases_ts = format_data.format_cases_timeseries( cases_whole.loc[cases_whole["days_past"] <= window] )
    new_seqs_per_case = format_data.get_seqs_per_case( new_cases_ts, new_sequences, zip_f=zip_f )

    return dashplot.plot_daily_cases_seqs( new_seqs_per_case )

@app.callback(
    Output( "fraction-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" )]
)
def update_cummulative_graph( window, zip_f ):
    new_sequences = sequences.loc[sequences["days_past"] <= window]
    new_cases_ts = format_data.format_cases_timeseries( cases_whole.loc[cases_whole["days_past"] <= window] )
    new_seqs_per_case = format_data.get_seqs_per_case( new_cases_ts, new_sequences, zip_f=zip_f )

    return dashplot.plot_cummulative_sampling_fraction( new_seqs_per_case )

@app.callback(
    Output('zip-drop', 'value'),
    Input('choropleth-graph', 'clickData'))
def update_figures_after_click( clickData ):
    if clickData is None:
        return []
    else:
        return clickData["points"][0]["location"]


if __name__ == '__main__':
    app.run_server( debug=True )