import dash_core_components as dcc
import dash_html_components as html
import src.plot as dashplot

def get_layout( wastewater_data ):
    markdown = """
    To monitor the prevalence of SARS-CoV-2 infections in San Diego, we are measuring virus concentration at the Point 
    Loma Wastewater Treatment Plant, the main wastewater treatment facility for the city (serves roughly 2.3 million 
    residents). Fragments of SARS-CoV-2 RNA are shed in urine and stool and can serve as an early indicator of changes 
    in COVID-19 caseload in the community. The data shown here is collected by the Knight Lab at UCSD in collaboration 
    with San Diego County. The raw data for this dashboard can be found in our 
    [GitHub repository](https://github.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego).
    """

    layout = [
        html.Div(
            [
                dcc.Markdown( markdown ),
                html.Div(
                    dcc.Graph(
                        figure=dashplot.plot_wastewater( wastewater_data ),
                        id="wastewater-graph",
                        config={"displayModeBar" : False},
                        style={"height" : "30em"}
                    ),
                )
            ]
        ),
        html.Br(),
        html.Br(),
        #html.P( html.I( "Updated on December 18th @ 12:42 PM PST" ), style={ 'textAlign': 'center' })
    ]

    return layout