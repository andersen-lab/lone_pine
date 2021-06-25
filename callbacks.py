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
        Output( "cum-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_cummulative_graph( window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer )
        new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

        return dashplot.plot_cummulative_cases_seqs( new_seqs_per_case )

    @app.callback(
        Output( "daily-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_daily_graph( window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer )
        new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

        return dashplot.plot_daily_cases_seqs( new_seqs_per_case )

    @app.callback(
        Output( "fraction-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_fraction_graph( window, zip_f, provider, sequencer ):
        new_sequences = get_sequences( sequences, window, provider, sequencer )
        new_seqs_per_case = format_data.get_seqs_per_case( get_cases( cases_whole, window ), new_sequences, zip_f=zip_f )

        return dashplot.plot_cummulative_sampling_fraction( new_seqs_per_case )

    @app.callback(
        Output( "lineage-graph", "figure" ),
        [Input( "recency-drop", "value" ),
         Input( "zip-drop", "value" ),
         Input( "provider-drop", "value"),
         Input( 'sequencer-drop', "value")]
    )
    def update_lineages_graph( window, zip_f, provider, sequencer ):
        return dashplot.plot_lineages( sequences, window, zip_f, provider, sequencer )

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
        return dashplot.plot_lineages_time( sequences, lineage, window, zip_f, provider, scaleby, sequencer )

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