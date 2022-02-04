from dash import html, dcc
import dash_bootstrap_components as dbc
import src.plot as dashplot

def get_layout( wastewater_data, wastewater_seq_data, commit_date ):
    markdown = """
    To monitor the prevalence of SARS-CoV-2 infections in San Diego, we are measuring virus concentration at the Point 
    Loma Wastewater Treatment Plant, the main wastewater treatment facility for the city (serves roughly 2.3 million 
    residents). Fragments of SARS-CoV-2 RNA are shed in urine and stool and can serve as an early indicator of changes 
    in COVID-19 caseload in the community. To study individual virus lineages in present in San Diego, we are sequencing 
    wastewater and performing lineage deconvolution with [Freyja](https://github.com/andersen-lab/Freyja). The data shown 
    here is collected by the Knight Lab at UCSD in collaboration with San Diego County. The raw data for this dashboard 
    can be found in our [GitHub repository](https://github.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego).
    """

    #commit_date = get_last_commit_date()
    #commit_date = "December 22 @ 1:07 PM PST"

    layout = [
        html.Div(
            [
                dcc.Markdown( markdown ),
                html.P(),
                html.P( children=[
                "The following graph compares ",
                html.Strong( "viral load in wastewater", style={"color" : "#56B4E9"} ),
                " to ",
                html.Strong( "reported cases", style={"color" : "#D55E00"} ),
                " in San Diego county. Scatter points indicate raw data, while solid line represent the same data smoothed with a Savitzky-Golay filter. "
                "Hover-over text displays raw values only."
                ] ),
                html.Div(
                    [
                        html.Div(
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
                                style = {"width" : "100%", "justifyContent": "flex-end"}
                            )
                        ),
                        dcc.Graph(
                            id="wastewater-graph",
                            config={"displayModeBar" : False},
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
                                    style={"width" : "60%", "marginLeft" : "0", "marginRight": "2.5%", 'display': 'inline-block'}
                                ),
                                html.Div(
                                    dbc.RadioItems(
                                        id="scale-seqs-radios",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        options=[
                                            { "label": "Raw prevalance", "value": "prevalence" },
                                            { "label": "Scale by viral load", "value": "viral" },
                                            { "label": "Scale by cases", "value": "cases" },
                                        ],
                                        value="prevalence",
                                        style={"justifyContent": "flex-end"}
                                    ),
                                    className="three columns",
                                    style={ 'display': 'inline-block' }
                                )
                            ],
                            className="radio-group",
                            style={"margin" : "0"}
                        ),
                        html.Div(
                            dcc.Graph(
                                figure=dashplot.plot_wastewater_seqs( wastewater_data, wastewater_seq_data ),
                                id="wastewater-seq-graph",
                                config={"displayModeBar" : False},
                            ),
                            style={ "height": "30em", 'width': '60em', "margin" : "auto" }
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