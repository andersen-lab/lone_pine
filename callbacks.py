#Input('url', 'pathname')
import dashboard.plot as dashplot
from dash.dependencies import Input, Output
import data_wrangling.format_resources as format_data

def register_callbacks( app, sequences, cases_whole ):

    def get_sequences( seqs, window, provider, sequencer, zip_f=None ):
        new_seqs = seqs.copy()
        if window:
            new_seqs = new_seqs.loc[sequences["days_past"] <= window]
        if provider:
            new_seqs = new_seqs.loc[new_seqs['provider']==provider]
        if sequencer:
            new_seqs = new_seqs.loc[new_seqs["sequencer"]==sequencer]
        if zip_f:
            new_seqs = new_seqs.loc[new_seqs["zipcode"]==zip_f]

        return new_seqs

    def get_cases( cases, window ):
        new_cases = cases.copy()
        if window:
            new_cases = cases.loc[cases["days_past"] <= window]
        return new_cases

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
        Input( "hidden-div", "children" )   # Will eventually take the URL as an option.
    )
    def update_zip_drop( _ ):
        return [{"label" : i, "value": i } for i in cases_whole["ziptext"].sort_values().unique()]

    @app.callback(
        Output( "sequencer-drop", "options" ),
        [Input( "recency-drop", "value" ),
         Input( 'provider-drop', "value" ),
         Input( "zip-drop", "value")]
    )
    def update_sequencer_drop( window, provider, zip_f ):
        new_sequences = get_sequences( sequences, window, provider, None, zip_f )
        return format_data.get_provider_sequencer_values( new_sequences, "sequencer" )

    @app.callback(
        Output( "provider-drop", "options" ),
        [Input( "recency-drop", "value" ),
         Input( 'sequencer-drop', "value" ),
         Input( "zip-drop", "value")]
    )
    def update_sequencer_drop( window, sequencer, zip_f ):
        new_sequences = get_sequences( sequences, window, None, sequencer, zip_f )
        return format_data.get_provider_sequencer_values( new_sequences, "provider" )

    @app.callback(
        Output( "lineage-drop", "options" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineage_drop( window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer, zip_f )
        return format_data.get_lineage_values( new_sequences )

    @app.callback(
        Output( "summary-table", "children"),
        [Input( "provider-drop", "value"),
         Input( "sequencer-drop", "value"),
         Input( "zip-drop", "value")]
    )
    def update_summary_table( provider, sequencer, zip_f ):
        new_sequences = get_sequences( sequences, None, provider, sequencer, zip_f )
        return format_data.get_summary_table( new_sequences )

    @app.callback(
        Output( "zip-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_zip_graph( window, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer )
        new_cases = format_data.format_cases_total( get_cases( cases_whole, window ) )
        return dashplot.plot_zips( format_data.format_zip_summary( new_cases, new_sequences ) )

    @app.callback(
        [Output( "cum-graph", "figure" ),
         Output( "daily-graph", "figure" ),
         Output( "fraction-graph", "figure" )],
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_cummulative_graph( window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer )
        new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

        return_plots = [dashplot.plot_cummulative_cases_seqs( new_seqs_per_case ),
                        dashplot.plot_daily_cases_seqs( new_seqs_per_case ),
                        dashplot.plot_cummulative_sampling_fraction( new_seqs_per_case )]

        return return_plots

    @app.callback(
        Output( "lineage-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineages_graph( window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer, zip_f )
        return dashplot.plot_lineages( new_sequences )

    @app.callback(
        Output( "lineage-time-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "lineage-drop", "value"),
         Input( "provider-drop", "value"),
         Input( "lineage-type", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineage_time_graph( window, zip_f, lineage, provider, scaleby, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer, zip_f )
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