import dash_core_components as dcc
import dash_html_components as html
import requests
from datetime import datetime, timezone, timedelta
import src.plot as dashplot


def get_last_commit_date():
    last_commit_url = "https://api.github.com/repos/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/git/refs/heads/master"
    last_commit = requests.get( last_commit_url ).json()["object"]["url"]
    last_commit_date = requests.get( last_commit ).json()["author"]["date"]
    last_commit_date = datetime.strptime( last_commit_date, "%Y-%m-%dT%H:%M:%SZ" ).replace( tzinfo=timezone.utc ).astimezone( timezone( timedelta( hours=-8 ) ) )
    return last_commit_date.strftime( "%B %d @ %I:%M %p PST" )

def get_layout( wastewater_data ):
    markdown = """
    To monitor the prevalence of SARS-CoV-2 infections in San Diego, we are measuring virus concentration at the Point 
    Loma Wastewater Treatment Plant, the main wastewater treatment facility for the city (serves roughly 2.3 million 
    residents). Fragments of SARS-CoV-2 RNA are shed in urine and stool and can serve as an early indicator of changes 
    in COVID-19 caseload in the community. The data shown here is collected by the Knight Lab at UCSD in collaboration 
    with San Diego County. The raw data for this dashboard can be found in our 
    [GitHub repository](https://github.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego).
    """

    #commit_date = get_last_commit_date()
    commit_date = "December 22 @ 9:30 AM PST"

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
        html.P( html.I( f"Updated on {commit_date}" ), style={ 'textAlign': 'center' } )
    ]

    return layout