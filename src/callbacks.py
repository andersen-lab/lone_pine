import src.plot as dashplot
import src.format_resources as format_data
import src.pages.mainpage as mainpage
import src.pages.sgtfpage as sgtfpage
import src.pages.wastewaterpage as wastepage
from dash.dependencies import Input, Output

def register_url_sequences( df, url ):
    if url == "/bajacalifornia":
        return df.loc[df["state"]=="Baja California"]
    else:
        return df.loc[df["state"]=="San Diego"]

def register_url_cases( df, url ):
    if url == "/bajacalifornia":
        return df.loc[df["ziptext"]=="None"]
    else:
        return df.loc[df["ziptext"]!="None"]


def register_callbacks( app, sequences, cases_whole, sgtf_data, wastewater_data ):

    def get_sequences( seqs, url, window=None, provider=None, sequencer=None, zip_f=None ):
        new_seqs = seqs.copy()

        new_seqs = register_url_sequences( new_seqs, url )

        if window:
            new_seqs = new_seqs.loc[sequences["days_past"] <= window]
        if provider:
            new_seqs = new_seqs.loc[new_seqs['provider']==provider]
        if sequencer:
            new_seqs = new_seqs.loc[new_seqs["sequencer"]==sequencer]
        if zip_f:
            new_seqs = new_seqs.loc[new_seqs["zipcode"]==zip_f]

        return new_seqs

    def get_cases( cases, url, window=None ):
        new_cases = cases.copy()

        new_cases = register_url_cases( new_cases, url )

        if window:
            new_cases = cases.loc[cases["days_past"] <= window]
        return new_cases

    @app.callback(
        Output( "page-contents", "children" ),
        Input( "url", "pathname")
    )
    def generate_page_content( path ):
        if path == "/sgtf":
            return sgtfpage.get_layout( format_data.load_sgtf_data() )
        elif path == "/wastewater":
            return wastepage.get_layout( format_data.load_wastewater_data() )
        else:
            return mainpage.get_layout()

    @app.callback(
        Output( "markdown-stuff", "children" ),
        Input( "url", "pathname" )
    )
    def update_markdown( path ):
        if path == "/bajacalifornia":
            place = "Baja California"
        else:
            place = "San Diego County"

        markdown_text = f'''
        To gain insights into the emergence, spread, and transmission of COVID-19 in our community, we are working with a large 
        number of partners to sequence SARS-CoV-2 samples from patients in San Diego and Baja California. This dashboard provides up-to-date 
        information on the number and locations of our sequencing within {place}. Consensus sequences are deposited on 
        GISAID, NCBI under the [BioProjectID](https://www.ncbi.nlm.nih.gov/bioproject/612578), and the 
        [Andersen Lab Github repository](https://github.com/andersen-lab/HCoV-19-Genomics).
        '''

        return markdown_text

    @app.callback(
        Output( "zip-drop", "options" ),
        Input( "url", "pathname" )
    )
    def update_zip_drop( url ):
        new_cases = get_cases( cases_whole, url, None )
        return [{"label" : i, "value": i } for i in new_cases["ziptext"].sort_values().unique()]

    @app.callback(
        Output( "zip-drop", "disabled" ),
        Input( "url", "pathname" )
    )
    def enable_zip_drop( url ):
        return url == "/bajacalifornia"

    @app.callback(
        Output( "sequencer-drop", "options" ),
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( 'provider-drop', "value" ),
         Input( "zip-drop", "value")]
    )
    def update_sequencer_drop( url, window, provider, zip_f ):
        new_sequences = get_sequences( sequences, url, window, provider, None, zip_f )
        return format_data.get_provider_sequencer_values( new_sequences, "sequencer" )

    @app.callback(
        Output( "provider-drop", "options" ),
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( 'sequencer-drop', "value" ),
         Input( "zip-drop", "value")]
    )
    def update_sequencer_drop( url, window, sequencer, zip_f ):
        new_sequences = get_sequences( sequences, url, window, None, sequencer, zip_f )
        return format_data.get_provider_sequencer_values( new_sequences, "provider" )

    @app.callback(
        Output( "lineage-drop", "options" ),
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineage_drop( url, window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, url, window, provider, sequencer, zip_f )
        return format_data.get_lineage_values( new_sequences )

    @app.callback(
        Output( "summary-table", "children"),
        [Input( "url", "pathname" ),
         Input( "provider-drop", "value"),
         Input( "sequencer-drop", "value"),
         Input( "zip-drop", "value")]
    )
    def update_summary_table( url, provider, sequencer, zip_f ):
        new_sequences = get_sequences( sequences, url, None, provider, sequencer, zip_f )
        return format_data.get_summary_table( new_sequences )

    @app.callback(
        Output( "zip-graph", "figure" ),
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_zip_graph( url, window, provider, sequencer ):
        new_sequences = get_sequences( sequences, url, window, provider, sequencer )
        new_cases = format_data.format_cases_total( get_cases( cases_whole, url, window ) )
        return dashplot.plot_zips( format_data.format_zip_summary( new_cases, new_sequences ) )

    @app.callback(
        [Output( "cum-graph", "figure" ),
         Output( "daily-graph", "figure" ),
         Output( "fraction-graph", "figure" )],
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_cummulative_graph( url, window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, url, window, provider, sequencer )
        new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, url, window ), new_sequences, zip_f=zip_f )

        return_plots = [dashplot.plot_cummulative_cases_seqs( new_seqs_per_case ),
                        dashplot.plot_daily_cases_seqs( new_seqs_per_case ),
                        dashplot.plot_cummulative_sampling_fraction( new_seqs_per_case )]

        return return_plots

    @app.callback(
        Output( "lineage-graph", "figure" ),
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineages_graph( url, window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, url, window, provider, sequencer, zip_f )
        return dashplot.plot_lineages( new_sequences )

    @app.callback(
        Output( "lineage-time-graph", "figure" ),
        [Input( "url", "pathname" ),
         Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "lineage-drop", "value"),
         Input( "provider-drop", "value"),
         Input( "lineage-type", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineage_time_graph( url, window, zip_f, lineage, provider, scaleby, sequencer ):
        new_sequences = get_sequences( sequences, url, window, provider, sequencer, zip_f )

        if lineage == "all-voc":
            return dashplot.plot_voc( new_sequences, scaleby )
        else:
            return dashplot.plot_lineages_time( new_sequences, lineage, scaleby )

    @app.callback(
        Output('zip-drop', 'value'),
        Input('zip-graph', 'clickData'))
    def update_figures_after_click( clickData ):
        if clickData is None:
            return None
        else:
            return clickData["points"][0]["x"]

    @app.callback(
        Output( "lineage-drop", "value" ),
        Input( "lineage-graph", "clickData" )
    )
    def update_lineage_value( clickData ):
        if clickData is None:
            return None
        else:
            return clickData["points"][0]["x"]

    @app.callback(
        Output( "zip-div", "hidden" ),
        Input( "url", "pathname" )
    )
    def enable_zip_graph( url ):
        return url=="/bajacalifornia"