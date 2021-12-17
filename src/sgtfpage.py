import dash_core_components as dcc
import dash_html_components as html
import src.plot as dashplot

def get_layout( sgtf_data ):
    markdown = """
    To gain insight into the spread of the Omicron variant in our community, we are working with a large number of 
    partners to track S-gene target failures (SGTFs). SGTFs are a feature of the TaqPath PCR assay that fails to detect
    the spike gene of certain variants of interest due to a deletion in these viruses' spike gene. Most Omicron 
    sequences have this deletion while most Delta sequences do not. As a result, the proportion of SGTF in positive 
    tests can be used to estimate the prevalence of Omicron. The data shown here is collected by our collaboring 
    partners in San Diego. More information on Omicron and other estimates of its prevalence in San Diego and elsewhere 
    can be found at [Outbreak.info](https://outbreak.info/).
    """

    layout = [
        html.Div(
            [
                dcc.Markdown( markdown ),
                html.Div( [
                    #html.H4( "S Gene Target Failure" ),
                    html.Div(
                        dcc.Graph(
                            figure=dashplot.plot_sgtf( sgtf_data ),
                            id="sgtf-graph",
                            config={"displayModeBar" : False},
                            style={"height" : "30em"}
                        ),
                        className="six columns",
                    ),
                    html.Div(
                        dcc.Graph(
                            figure=dashplot.plot_sgtf_estiamte( sgtf_data ),
                            id="sgtf-estimate",
                            config={"displayModeBar" : False},
                            style={ "height" : "30em",
                                    "marginLeft" : "20px" }
                        ),
                        className="six columns",
                    )
                ],
                    id="sgtf-div",
                    className="pretty_container",
                    style={ "marginLeft" : "auto",
                            "marginRight" : "auto" }
                ),
            ],
            className="row" ),
        html.Br(),
        html.Br(),
        html.P( html.I( "Updated on December 17th @ 11:21 AM PST" ), style={"width":"80em", 'textAlign': 'center' })
    ]

    return layout