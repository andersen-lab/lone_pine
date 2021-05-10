# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import data_wrangling.format_resources as format_data
import dashboard.plot as dashplot
from dash.dependencies import Input, Output, State


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash( __name__, external_stylesheets=external_stylesheets )
server = app.server
app.scripts.config.serve_locally = True
app.title = "San Diego sequencing dashboard"

sequences = format_data.load_sequences()
cases_whole = format_data.load_cases()

markdown_text = '''
To gain insights into the emergence, spread, and transmission of COVID-19 in our community, we are working with a large 
number of partners to sequence SARS-CoV-2 samples from patients in San Diego. This dashboard provides up-to-date 
information on the number and locations of our sequencing within San Diego County. Consensus sequences are deposited on 
GISAID, NCBI under the [BioProjectID](https://www.ncbi.nlm.nih.gov/bioproject/612578), and the 
[Andersen Lab Github repository](https://github.com/andersen-lab/HCoV-19-Genomics).
'''

app.layout = html.Div( children=[
    html.Div( [dcc.Markdown( markdown_text ),
               html.P() ] ),
    html.Div( [
        html.Div( [
            html.Div( [
                html.H5( "ZIP code", style={ "color" : "#F8F9FA", "margin" : "1%" } ),
                dcc.Dropdown( id = 'zip-drop',
                              options=[{"label" : i, "value": i } for i in cases_whole["ziptext"].sort_values().unique()],
                              multi=False,
                              placeholder="All",
                              style={"margin" : "1%"}
                              )
            ],
                style={ "float" : "left", "width" : "25%" } ),
            html.Div( [
                html.H5( "Recency", style={ "color" : "#F8F9FA", "margin" : "1%" } ),
                dcc.Dropdown( id = 'recency-drop',
                              options=[
                                  { 'label' : "Last week", 'value': 7},
                                  { 'label' : "Last month", 'value' : 30 },
                                  { 'label' : "Last 6 month", 'value' : 183 },
                                  { 'label' : "Last year", 'value' : 365 }
                              ],
                              multi=False,
                              clearable=True,
                              searchable=False,
                              placeholder="All",
                              style={"margin" : "1%"}
                              )
            ],
                style={ "float" : "left", "width" : "25%" } ),
            html.Div( [
                html.H5( "Sequencing Lab", style={ "color" : "#F8F9FA", "margin" : "1%" } ),
                dcc.Dropdown( id = 'sequencer-drop',
                              options=[{"label" : i, "value": i } for i in sequences["sequencer"].sort_values().unique()],
                              multi=False,
                              placeholder="All",
                              style={"margin" : "1%"}
                              )
            ],
                style={ "float" : "left", "width" : "25%" } ),
            html.Div( [
                html.H5( "Provider", style={ "color" : "#F8F9FA", "margin" : "1%" } ),
                dcc.Dropdown( id = 'provider-drop',
                              options=[{ 'label' : i, 'value': i} for i in sequences["provider"].sort_values().unique()],
                              multi=False,
                              clearable=True,
                              searchable=True,
                              placeholder="All",
                              style={"margin" : "1%"}
                              )
            ],
                style={ "float" : "left", "width" : "25%" }
            ),
        ] )
    ],
        style={ "marginLeft" : "auto",
                "marginRight" : "auto",
                "backgroundColor" : "#5A71A2"},
        className="pretty_container_rounded row"
    ),
    html.Div( [
        html.Div(
            dcc.Graph(
                id="cum-graph",
                config={'displayModeBar': False},
                style={ "height" : "25em" }
            ),
            className="pretty_container four columns",
            style={"flexGrow" : "1"}
        ),
        html.Div(
            dcc.Graph(
                id="daily-graph",
                config={'displayModeBar': False},
                style={ "height" : "25em" }
            ),
            className="pretty_container four columns",
            style={"flexGrow" : "1"}

        ),
        html.Div(
            dcc.Graph(
                id="fraction-graph",
                config={'displayModeBar': False},
                style={ "height" : "25em" }
            ),
            className="pretty_container four columns",
            style={"flexGrow" : "1"}
        ),
    ], className="row",
       style={ "marginLeft" : "auto",
               "marginRight" : "auto",
               "display": "flex",
               "flexWrap": "wrap" }
    ),
    html.Div( [
        html.H4( "PANGO Lineages" ),
        html.Div(
            dcc.Dropdown( id = 'lineage-drop',
                          options=format_data.get_lineage_values( sequences ),
                          multi=False,
                          placeholder="All lineages"
                          ),
                  className="three columns" ),
        html.Div(
            dcc.RadioItems(
                id='lineage-type',
                options=[{ 'label': "Total", 'value': 'sequences' },
                         { 'label': "Fraction", 'value': "fraction" }],
                value='sequences',
                labelStyle={ 'display': 'inline-block' }
            ),
            style={"marginLeft" : "15px", "marginTop" : "7px" },
            className="three columns" )
    ],
        className="row"
    ),
    html.Div(
        dcc.Graph(
            id="lineage-graph",
            config={"displayModeBar" : False},
            style={ "height"  : "25em" }
        ),
        className="pretty_container",
        style={ "marginLeft" : "auto",
                "marginRight" : "auto" }
    ),
    html.Div(
        dcc.Graph(
            id="lineage-time-graph",
            config={"displayModeBar" : False},
            style={"height" : "25em" }
        ),
        className="pretty_container",
        style={ "marginLeft" : "auto",
                "marginRight" : "auto" }
    ),
    html.Div( [
        html.H4( "ZIP Codes" ),
        dcc.Graph(
            id="zip-graph",
            config={"displayModeBar" : False},
            style={ "height"  : "25em" }
        ) ],
        className="pretty_container",
        style={ "marginLeft" : "auto",
                "marginRight" : "auto" }
    )
],
    style={ "marginLeft" : "auto",
            "marginRight" : "auto",
            "maxWidth" : "80em" }
)

def get_sequences( seqs, window, provider, sequencer ):
    new_seqs = seqs.copy()
    if window:
        new_seqs = new_seqs.loc[sequences["days_past"] <= window]
    if provider:
        new_seqs = new_seqs.loc[new_seqs['provider']==provider]
    if sequencer:
        new_seqs = new_seqs.loc[new_seqs["sequencer"]==sequencer]
    return new_seqs

def get_cases( cases, window ):
    new_cases = cases.copy()
    if window:
        new_cases = cases.loc[cases["days_past"] <= window]
    return new_cases

@app.callback(
    Output( "zip-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "provider-drop", "value"),
     Input( 'sequencer-drop', "value")]
)
def update_zip_graph( window, provider, sequencer ):
    new_sequences = get_sequences( sequences, window, provider, sequencer )
    new_cases = format_data.format_cases_total( get_cases( cases_whole, window ) )
    return dashplot.plot_zips( format_data.format_zip_summary( new_cases, new_sequences ) )

@app.callback(
    Output( "cum-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" ),
     Input( "provider-drop", "value"),
     Input( 'sequencer-drop', "value")]
)
def update_cummulative_graph( window, zip_f, provider, sequencer ):
    new_sequences = get_sequences( sequences, window, provider, sequencer )
    new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

    return dashplot.plot_cummulative_cases_seqs( new_seqs_per_case )

@app.callback(
    Output( "daily-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" ),
     Input( "provider-drop", "value"),
     Input( 'sequencer-drop', "value")]
)
def update_daily_graph( window, zip_f, provider, sequencer ):
    new_sequences = get_sequences( sequences, window, provider, sequencer )
    new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

    return dashplot.plot_daily_cases_seqs( new_seqs_per_case )

@app.callback(
    Output( "fraction-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" ),
     Input( "provider-drop", "value"),
     Input( 'sequencer-drop', "value")]
)
def update_fraction_graph( window, zip_f, provider, sequencer ):
    new_sequences = get_sequences( sequences, window, provider, sequencer )
    new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

    return dashplot.plot_cummulative_sampling_fraction( new_seqs_per_case )

@app.callback(
    Output( "lineage-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" ),
     Input( "provider-drop", "value"),
     Input( 'sequencer-drop', "value")]
)
def update_lineages_graph( window, zip_f, provider, sequencer ):
    return dashplot.plot_lineages( sequences, window, zip_f, provider, sequencer )

@app.callback(
    Output( "lineage-time-graph", "figure" ),
    [Input( "recency-drop", "value" ),
     Input( "zip-drop", "value" ),
     Input( "lineage-drop", "value"),
     Input( "provider-drop", "value"),
     Input( "lineage-type", "value"),
     Input( 'sequencer-drop', "value")]
)
def update_lineage_time_graph( window, zip_f, lineage, provider, scaleby, sequencer ):
    return dashplot.plot_lineages_time( sequences, lineage, window, zip_f, provider, scaleby, sequencer )

@app.callback(
    Output('zip-drop', 'value'),
    Input('zip-graph', 'clickData'))
def update_figures_after_click( clickData ):
    if clickData is None:
        return None
    else:
        return float( clickData["points"][0]["x"] )

@app.callback(
    Output( "lineage-drop", "value" ),
    Input( "lineage-graph", "clickData" )
)
def update_lineage_value( clickData ):
    if clickData is None:
        return None
    else:
        return clickData["points"][0]["x"]


if __name__ == '__main__':
    app.run_server( debug=False )