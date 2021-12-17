import dash_core_components as dcc
import dash_html_components as html
import src.plot as dashplot

def get_layout( sgtf_data ):
    markdown = """
    To gain insights in the spread of the Omicron variant in out community, we are working with a large number of 
    partners to track S-gene target failures (SGTFs). SGTFs are a feature of the TaqPath PCR assay that fails to detect
    the spike gene of certain variants of interest due to a deletion in these viruses coding sequence. Most Omicron 
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
                            style={"height" : "25em"}
                        ),
                        className="six columns",
                        style={ "borderStyle" : "solid" }
                    ),
                    html.Div(
                        dcc.Graph(
                            figure=dashplot.plot_sgtf_estiamte( sgtf_data ),
                            id="sgtf-estimate",
                            style={ "height" : "25em" }
                        ),
                        className="six columns",
                        style={ "borderStyle" : "solid" }
                    )
                ],
                    id="sgtf-div",
                    className="pretty_container",
                    style={ "marginLeft" : "auto",
                            "marginRight" : "auto",
                            "borderStyle" : "solid" }
                )
            ] )
    ]

    return layout