# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html
import src.format_resources as format_data
import dash
from src.callbacks import register_callbacks

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash( __name__, external_stylesheets=external_stylesheets )
server = app.server
app.config.suppress_callback_exceptions = True
app.scripts.config.serve_locally = True
app.title = "San Diego sequencing dashboard"

sequences = format_data.load_sequences()
#sequences = sequences.loc[sequences["state"]=="San Diego"]
cases_whole = format_data.load_cases()
#cases_whole = cases_whole.loc[cases_whole["ziptext"]!="None"]

register_callbacks( app, sequences, cases_whole )

app.layout = html.Div( children=[
    dcc.Location(id='url', refresh=False),
    html.Div( [dcc.Markdown( id="markdown-stuff" ),
               html.P() ] ),
    html.Div( [html.Table( id="summary-table" )], style={"width" : "30em",
                                                         "marginLeft" : "auto",
                                                         "marginRight" : "auto",
                                                         "marginBottom" : "20px"} ),
    html.Div( [
        html.Div( [
            html.Div( [
                html.H5( "ZIP code", style={ "color" : "#F8F9FA", "margin" : "1%" } ),
                dcc.Dropdown( id = 'zip-drop',
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
                              multi=False,
                              placeholder="All",
                              style={"margin" : "1%", "font-size" : "85%" }
                              )
            ],
                style={ "float" : "left", "width" : "25%" } ),
            html.Div( [
                html.H5( "Provider", style={ "color" : "#F8F9FA", "margin" : "1%" } ),
                dcc.Dropdown( id = 'provider-drop',
                              multi=False,
                              clearable=True,
                              searchable=True,
                              placeholder="All",
                              style={"margin" : "1%", "font-size" : "85%" }
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
        id="zip-div",
        className="pretty_container",
        style={ "marginLeft" : "auto",
                "marginRight" : "auto" }
    ),
    html.Div( id='hidden-div', style={'display':'none'} )
],
    style={ "marginLeft" : "auto",
            "marginRight" : "auto",
            "maxWidth" : "80em" }
)

if __name__ == '__main__':
    app.run_server( debug=False )
