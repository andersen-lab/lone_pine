import dash_core_components as dcc
import dash_html_components as html
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
                html.Br(),
                html.P( children=[
                "The following graph compares ",
                html.Strong( "viral load in wastewater", style={"color" : "#56B4E9"} ),
                " to ",
                html.Strong( "reported cases", style={"color" : "#D55E00"} ),
                " in San Diego county. Scatter points indicate raw data, while solid line represent the same data smoothed with a Savitzky-Golay filter. "
                "Hoverover text displays raw values only."
                ] ),
                html.Div(
                    dcc.Graph(
                        figure=dashplot.plot_wastewater( wastewater_data ),
                        id="wastewater-graph",
                        config={"displayModeBar" : False},
                        style={"height" : "30em"}
                    ),
                ),
                html.Div(
                    dcc.Graph(
                        figure=dashplot.plot_wastewater_seqs( wastewater_seq_data ),
                        id="wastewater-seq-graph",
                        config={"displayModeBar" : False},
                        style={"height" : "30em", "width" : "50em"}
                    ),
                    style={'width': '100%', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
                )
            ]
        ),
        html.Br(),
        html.Br(),
        html.P( html.I( commit_date ), style={ 'textAlign': 'center' } )
    ]

    return layout