# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import data_wrangling.download_resources as download
import dashboard.plot as dashplot
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import geopandas as gpd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash( __name__, external_stylesheets=external_stylesheets )
server = app.server

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

#fig1 = dashplot.plot_choropleth( zips )
#fig2 = dashplot.plot_cummulative_cases_seqs( plot_df )
#fig3 = dashplot.plot_daily_cases_seqs( plot_df )
#fig4 = dashplot.plot_cummulative_sampling_fraction( plot_df )

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
    html.Div( style={ "backgroundColor" : "#2B4267", "height"  : 10 } ),
    dcc.Store( id='hidden-data' )
],
    style={ "marginLeft" : "auto",
            "marginRight" : "auto",
            "maxWidth" : "80em" }
)
# TODO: Add download button to download metadata associated with current filtered data.

@app.callback(
    Output( "hidden-data", "data" ),
    [Input( "zip-drop", "value" ),
     Input( "recency-drop", "value"  )] )
def update_data( zip_f, window ):
    md = download.download_search( window=window )
    df, ts = download.download_cases( window=window )
    zips = download.download_shapefile( df, md, local=True )
    plot_df = download.get_seqs_per_case( ts, md, zip_f=zip_f )

    datasets = {
        "zips" : zips.reset_index().to_json(),
        "seqs_per_case" : plot_df.to_json( orient="split", date_format="iso" )
    }

    return json.dumps( datasets )


@app.callback(
    Output('zip-drop', 'value'),
    Input('choropleth-graph', 'clickData'))
def update_figures_after_click( clickData ):
    if clickData is None:
        return []
    else:
        return clickData["points"][0]["location"]

@app.callback(
    [Output( 'choropleth-graph', "figure" ),
     Output( "zip-drop", "options")],
    [Input( "hidden-data", "modified_timestamp" ),
     Input( 'color-type', "value")],
    State( "hidden-data", "data" ))
def update_choropleth( timestamp, colorby, jsonified_data ):
    datasets = json.loads( jsonified_data )
    zips = gpd.GeoDataFrame.from_features( json.loads( datasets["zips"] ) )
    zips = zips.set_index( "ZIP" )

    zip_options = [{'label': i, 'value': i} for i in zips.index.unique()]

    return [dashplot.plot_choropleth( zips, colorby=colorby ), zip_options]

@app.callback(
    [Output( "cum-graph", "figure" ),
     Output( "daily-graph","figure" ),
     Output( "fraction-graph","figure" )],
    Input( "hidden-data", "modified_timestamp" ),
    State( "hidden-data", "data" ) )
def update_figures( timestamp, jsonified_data ):
    datasets = json.loads( jsonified_data )
    new_df = pd.read_json( datasets["seqs_per_case"], orient="split" )
    return [dashplot.plot_cummulative_cases_seqs( new_df ),
            dashplot.plot_daily_cases_seqs( new_df ),
            dashplot.plot_cummulative_sampling_fraction( new_df )]

if __name__ == '__main__':
    app.run_server( debug=True )