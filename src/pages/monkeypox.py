from dash import html, dcc
import dash_bootstrap_components as dbc

def get_layout( commit_date ):
    markdown = """
    To monitor the prevalence of Monkeypox in San Diego, we are measuring virus concentration at the wastewater 
    treatment plants in San Diego. Fragments of monkeypox virus DNA are shed in urine and stool and can serve as an 
    early indicator of the caseload in the community. The data shown here is collected by the Knight Lab at UCSD in 
    collaboration with San Diego County. The raw data used by this dashboard will be publicly available soon. Scatter 
    points indicate raw data, while solid line represent the same data smoothed with a Savitzky-Golay filter. Hover-over
    text displays raw values for viral load and smoothed values for reported cases.
    """

    layout = [
        html.Div(
            [
                dcc.Markdown( markdown, link_target='_blank' ),
                html.P(),
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
                                    #{ "label": "Encina", "value": "Encina", "disabled" : True },
                                    { "label": "Point Loma", "value": "PointLoma" },
                                    #{ "label": "South Bay", "value": "SouthBay", "disabled" : True }
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
                                        { "label": "Log scale", "value": "log", "disabled" : True },

                                    ],
                                    value="linear",
                                    style={ "width": "50%", "justifyContent": "flex-end" }
                                )]
                        ),
                        dcc.Graph(
                            id="monkeypox-graph",
                            config={"displayModeBar" : False },
                            style={"height" : "30em"}
                        ),
                    ]
                )
            ]
        ),
        html.Br(),
        html.Br(),
        html.P( html.I( commit_date ), style={ 'textAlign': 'center' } )
    ]

    return layout