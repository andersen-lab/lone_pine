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
cases_whole = format_data.load_cases()
sgtf_data = format_data.load_sgtf_data()

register_callbacks( app, sequences, cases_whole, sgtf_data )

app.layout = html.Div( children=[
    dcc.Location(id='url', refresh=False),
    html.Div( [html.P( "Loading..." )],
        id="page-contents"
    ),
    html.Div( id="hidden-div", children=[], hidden=True )
],
    style={ "marginLeft" : "auto",
            "marginRight" : "auto",
            "maxWidth" : "80em" }
)

if __name__ == '__main__':
    app.run_server( debug=True )
