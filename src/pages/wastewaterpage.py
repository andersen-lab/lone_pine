import base64
from dash import html, dcc
import dash_bootstrap_components as dbc
import src.plot as dashplot

def get_layout( commit_date ):
    markdown = """
    To monitor the prevalence of SARS-CoV-2 infections in San Diego, we are measuring virus concentration at the Encina, Point 
    Loma, and South Bay wastewater treatment plants (see map below for catchment areas of each plant). Fragments of 
    SARS-CoV-2 RNA are shed in urine and stool and can serve as an early indicator of changes in COVID-19 caseload in the 
    community. To study individual virus lineages in present in San Diego, we are sequencing wastewater and performing 
    lineage deconvolution with [Freyja](https://github.com/andersen-lab/Freyja). The data shown here is collected by the
     Knight Lab at UCSD in collaboration with San Diego County. The raw data for this dashboard can be found in our 
    [GitHub repository](https://github.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego). Displayed case counts for each 
    catchment area are aggregated from ZIP code-level case counts from within the catchment.
    """

    #commit_date = get_last_commit_date()
    #commit_date = "December 22 @ 1:07 PM PST"

    image_filename = 'assets/catchment_map.png'  # replace with your own image
    encoded_image = base64.b64encode( open( image_filename, 'rb' ).read() )

    layout = [
        html.Div(
            [
                dcc.Markdown( markdown, style={"margin-bottom" : "-15pt" }, link_target='_blank' ),
                html.Div(
                    html.Img( src='data:image/png;base64,{}'.format(encoded_image.decode()),
                          style={"width" : "40em", "zIndex" : '2'} ),
                    style={"textAlign" : "center", "margin-bottom" : "-15pt" }
                ),
                html.P(),
                html.P( children=[
                "The following graph compares ",
                html.Strong( "viral load in wastewater", style={"color" : "#56B4E9"} ),
                " to ",
                html.Strong( "reported cases", style={"color" : "#D55E00"} ),
                " in the communities that are treated by each plant. Scatter points indicate raw data, while solid line represent the same data smoothed with a Savitzky-Golay filter. "
                "Hover-over text displays raw values for viral load and smoothed values for reported cases."
                ] ),
                html.Div(
                    [
                        html.Div(
                            [dbc.RadioItems(
                                id="ww-source-radio",
                                className="btn-group",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary",
                                labelCheckedClassName="active",
                                options=[
                                    { "label": "Encina", "value": "Encina" },
                                    { "label": "Point Loma", "value": "PointLoma" },
                                    { "label": "South Bay", "value": "SouthBay" }
                                ],
                                value="PointLoma",
                                style={ "width": "50%", "justifyContent": "flex-start" }
                            ),
                            dbc.RadioItems(
                                id="yaxis-scale-radio",
                                className="btn-group",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary",
                                labelCheckedClassName="active",
                                options=[
                                    { "label": "Linear scale", "value": "linear" },
                                    { "label": "Log scale", "value": "log" },

                                ],
                                value="linear",
                                style = {"width" : "50%", "justifyContent": "flex-end"}
                            )]
                        ),
                        dcc.Graph(
                            id="wastewater-graph",
                            config={"displayModeBar" : False },
                            style={"height" : "30em"}
                        ),
                    ]
                ),
                html.P(),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Br(),
                                html.Div(
                                    html.H4( "Wastewater lineages" ),
                                    className="three columns",
                                    style={"width" : "63.3%", "marginLeft" : "0", "marginRight": "2.5%", 'display': 'inline-block'}
                                ),
                                html.Div(
                                    dbc.RadioItems(
                                        id="scale-seqs-radios",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        options=[
                                            { "label": "Prevalence", "value": "prevalence" },
                                            { "label": "Scale by viral load", "value": "viral" },
                                            { "label": "Scale by cases", "value": "cases" },
                                        ],
                                        value="prevalence",
                                        style={"justifyContent": "flex-end"}
                                    ),
                                    #className="three columns",
                                    style={ 'display': 'inline-block', "justifyContent": "flex-end" }
                                )
                            ],
                            className="radio-group",
                            style={"margin" : "0"}
                        ),
                        html.Div(
                            dcc.Graph(
                                id="wastewater-seq-graph",
                                config={"displayModeBar" : False},
                            ),
                            style={ "height": "30em", "margin" : "auto" }
                        )
                    ],

                )
            ]
        ),
        html.Br(),
        html.Br(),
        html.P( html.I( commit_date ), style={ 'textAlign': 'center' } )
    ]

    return layout