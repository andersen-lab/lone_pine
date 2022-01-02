import geopandas as gpd
import numpy as np
import pandas as pd
import dash_html_components as html
from src.variants import VOC, VOI
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from numpy import exp, sqrt, diagonal, log

#VOC = sorted( ["AY.1", "AY.2", "AY.3", "AY.3.1", "B.1.1.7", "B.1.351", "B.1.351.2", "B.1.351.3", "B.1.617.2", "P.1", "P.1.1", "P.1.2"] )
#VOI = sorted( ["AV.1", "B.1.427", "B.1.429", "B.1.525", "B.1.526", "B.1.526.1", "B.1.526.2", "B.1.617", "B.1.617.1", "B.1.617.3",
#      "B.1.621", "B.1.621.1", "B.1.1.318", "C.36.3", "C.37", "P.3", "P.2"] )

def load_sequences( window=None ):
    sequences = pd.read_csv( "resources/sequences.csv" )

    # Convert to dates correctly.
    sequences["collection_date"] = pd.to_datetime( sequences["collection_date"] ).dt.tz_localize( None )
    sequences["collection_date"] = sequences["collection_date"].dt.normalize()
    sequences["epiweek"] = pd.to_datetime( sequences["epiweek"] ).dt.tz_localize( None )
    sequences["epiweek"] = sequences["epiweek"].dt.normalize()

    sequences["zipcode"] = sequences["zipcode"].apply( lambda x: str(x).split( ":" )[0] )
    sequences["zipcode"] = sequences["zipcode"].replace(r'^\s*$', np.nan, regex=True)
    sequences["zipcode"] = sequences["zipcode"].apply( lambda x: f"{float( x ):.0f}" )

    if window is not None:
        sequences = sequences.loc[sequences["days_past"] <= window].copy()

    return sequences

def load_cases( window = None ):
    cases = pd.read_csv( "resources/cases.csv" )

    # Convert to dates correctly.
    cases["updatedate"] = pd.to_datetime( cases["updatedate"] ).dt.tz_localize( None )
    cases["updatedate"] = cases["updatedate"].dt.normalize()

    if window is not None:
        cases = cases.loc[cases["days_past"] <= window].copy()
    return cases

#def format_cases_timeseries( cases_df, window=None ):
#    return cases_df.melt( id_vars=["updatedate", "ziptext"], value_vars=['case_count'] )

def format_cases_total( cases_df ):
    return_df = cases_df.sort_values( "updatedate", ascending=False ).groupby( "ziptext" ).first()
    return_df = return_df.reset_index()
    return return_df.drop( columns=["days_past"] )

def get_seqs_per_case( time_series, seq_md, zip_f=None ):
    """ Combines timeseries of cases and sequences.
    Parameters
    ----------
    time_series
    seq_md
    zip_f

    Returns
    -------

    """
    if zip_f:
        if type( zip_f ) != list:
            zip_f = [zip_f]
        time_series = time_series.loc[time_series["ziptext"].isin(zip_f)]
    cases = time_series.pivot_table( index="updatedate", values="case_count", aggfunc="sum" )
    cases["case_count"] = np.maximum.accumulate( cases["case_count"] )
    cases = cases.reset_index()

    cases.columns = ["date", "cases"]

    cases = cases.merge( get_seqs( seq_md, zip_f=zip_f ), on="date", how="outer", sort=True )

    cases["new_sequences"] = cases["new_sequences"].fillna( 0.0 )
    cases["sequences"] = cases["new_sequences"].cumsum()
    cases = cases.loc[~cases["cases"].isna()]
    cases["new_cases"] = cases["cases"].diff()
    cases["new_cases"] = cases["new_cases"].fillna( 0.0 )
    cases.loc[cases["new_cases"] < 0,"new_cases"] = 0

    return cases

def get_seqs( seq_md, groupby="collection_date", zip_f=None ):
    """ Pivots the output of download_search().
    Parameters
    ----------
    seq_md : pandas.DataFrame
        output of download_search(); list of sequences attached to ZIP code and collection date.
    groupby : str
        column of seq_md to count.
    zip_f : bool
        indicates whether to filter sequences to a single zipcode.

    Returns
    -------
    pandas.DatFrame
    """
    if zip_f:
        seqs = seq_md.loc[seq_md["zipcode"].isin( zip_f )]
    else:
        seqs = seq_md

    seqs = seqs.groupby( groupby )["ID"].agg( "count" ).reset_index()
    if groupby == "collection_date":
        seqs.columns = ["date", "new_sequences"]
    elif groupby == "zipcode":
        seqs.columns = ["zip", "sequences"]

    return seqs

def format_shapefile( cases, seqs ):
    """ Downloads and formats the San Diego ZIP GeoJSON formatted as a dictionary.
    Parameters
    ----------
    cases : pandas.DataFrame
        output of download_cases() containing the cummulative cases for each ZIP code.
    seqs : pandas.DataFrame
        output of download_search() containing a list of sequences with ZIP code information.
    Returns
    -------
    geopandas.GeoDataFrame:
        GeoDataFrame linking ZIP code areas to case counts, sequences, and fraction of cases sequenced.
    """
    zip_area = gpd.read_file( "resources/zips.geojson")

    # Add case data so it is there...
    zip_area = zip_area.merge( cases, left_on="ZIP", right_on="ziptext" )
    zip_area = zip_area.merge( get_seqs( seqs, groupby="zipcode" ), left_on="ZIP", right_on="zip", how="left" )
    zip_area["sequences"] = zip_area["sequences"].fillna( 0 )
    zip_area["fraction"] = zip_area["sequences"] / zip_area["case_count"]
    zip_area.loc[zip_area["fraction"].isna(),"fraction"] = 0
    zip_area = zip_area.set_index( "ZIP" )

    # Removing a number of columns to save memory.
    zip_area = zip_area[["geometry", "case_count","sequences", "fraction"]]

    return zip_area

def format_zip_summary( cases, seqs ):
    """ Merges cummulate cases and sequences for each ZIP code.
    Parameters
    ----------
    cases : pandas.DataFrame
        output of format_cases_total( load_cases() ) containing the cummulative cases for each zip code.
    seqs : pandas.DataFrame
        output of download_search() or load_sequences() containing a lkist of sequences with ZIP code information.
    Returns
    -------
    pandas.DataFrame :
        DataFrame linking ZIP code to case counts, sequences, and fraction of cases sequenced. Use format_shapefile() if
        want GeoDataFrames.
    """
    cumulative_seqs = get_seqs( seqs, groupby="zipcode" )

    cumulative_seqs = cumulative_seqs.merge( cases[["ziptext", "case_count"]], left_on="zip", right_on="ziptext", how="right" )
    cumulative_seqs["sequences"] = cumulative_seqs["sequences"].fillna( 0.0 )
    cumulative_seqs["fraction"] = cumulative_seqs["sequences"] / cumulative_seqs["case_count"]
    cumulative_seqs.loc[cumulative_seqs["fraction"].isna(),"fraction"] = 0
    cumulative_seqs = cumulative_seqs.drop( columns=["zip"] )

    return cumulative_seqs

def get_lineage_values( seqs ):
    values = seqs["lineage"].dropna()
    values = values.sort_values().unique()

    return_dict = [{"label" : "All variants of concern", "value" : "all-voc" },
                   {"label" : " - Variants of concern" , "value" : "None", "disabled" : True}]
    for i in sorted( VOC.keys() ):
        if i in values:
            return_dict.append( { "label" : i, "value" : i } )

    return_dict.append( {"label" : " - Variants of interest" , "value" : "None", "disabled" : True} )
    for i in sorted( VOI.keys() ):
        if i in values:
            return_dict.append( { "label" : i, "value" : i } )

    return_dict.append( {"label" : " - PANGO lineages" , "value" : "None", "disabled" : True} )
    for i in values:
        if ( i not in VOC ) & ( i not in VOI ):
            return_dict.append( { "label" : i, "value" : i } )

    return return_dict

def get_summary_table( seqs ):
    sg = {"textAlign" : "center" }
    sd2 = {"marginLeft" : "50px" }
    table = [html.Tr( [html.Th( "Type", style={"marginLeft" : "20px" } ), html.Th( "Total", style=sg ), html.Th( "Last Month", style=sg )] ),
             html.Tr( [html.Td( html.B( "Sequences", style={"marginLeft" : "10px" } ) ), html.Td( len( seqs ), style=sg ), html.Td( len( seqs.loc[seqs['days_past'] < 30] ), style=sg )] ),
             html.Tr(html.Td( "", colSpan=3 ) ),
             html.Tr( html.Td( html.B( "Variants of concern", style={"marginLeft" : "10px" } ), colSpan=3))]

    vocs = seqs.copy()
    vocs["VOC"] = vocs["lineage"].map( VOC )
    vocs = vocs.loc[~vocs["VOC"].isna()]

    for i in vocs["VOC"].sort_values().unique():
        table.append( html.Tr( [html.Td( html.I( i, style={"marginLeft" : "20px" } ) ), html.Td( len( vocs.loc[vocs['VOC']==i] ), style=sg ), html.Td( len( vocs.loc[(vocs['VOC']==i)&(seqs['days_past']<30)] ), style=sg )] ) )

    # Brief hack to get Omicron in table
    #table.append( html.Tr(
    #    [html.Td( html.I( "Omicron-like", style={ "marginLeft": "20px" } ) ), html.Td( 0, style=sg ),
    #     html.Td( 0, style=sg )] ) )

    return table

def get_provider_sequencer_values( seqs, value ):
    labels = [{"label" : f"{i} ({j})", "value": i }for i, j in seqs[value].sort_values().value_counts().iteritems()]
    labels = sorted( labels, key=lambda x: x["label"] )
    return labels


def load_sgtf_data():
    def lgm( ndays, x0, r ):
        return 1 / ( 1 + ( ( ( 1 / x0 ) - 1 ) * exp( -1 * r * ndays ) ) )

    tests = pd.read_csv( "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_SGTF_San-Diego/main/SGTF_San_Diego_new.csv", parse_dates=["Date"] )
    tests.columns = ["Date", "sgtf_all", "sgtf_likely", "sgtf_unlikely", "no_sgtf", "total_positive", "percent_low", "percen_all"]
    tests["percent"] = tests["sgtf_likely"] / tests["total_positive"]
    tests["percent_filter"] = savgol_filter( tests["percent"], window_length=5, polyorder=2 )
    tests["ndays"] = tests.index

    fit, covar = curve_fit( lgm, tests["ndays"], tests["percent_filter"], [0.001, 0.008] )
    sigma_ab = sqrt( diagonal( covar ) )

    days_sim = 300

    fit_df = pd.DataFrame( {"date" : pd.date_range( tests["Date"].min(), periods=days_sim ) } )
    fit_df["ndays"] = fit_df.index
    fit_df["fit_y"] = [lgm(i, fit[0], fit[1]) for i in range( days_sim )]
    fit_df["fit_lower"] = [lgm(i, fit[0]-sigma_ab[0], fit[1]-sigma_ab[1]) for i in range( days_sim )]
    fit_df["fit_upper"] = [lgm(i, fit[0]+sigma_ab[0], max(0, fit[1]+sigma_ab[1]) ) for i in range( days_sim )]

    above_50 = fit_df.loc[fit_df["fit_y"] >= 0.99,"date"].min()
    above_50_lower = fit_df.loc[fit_df["fit_lower"] >= 0.99,"date"].min()
    above_50_upper = fit_df.loc[fit_df["fit_upper"] >= 0.99,"date"].min()

    growth_rate = fit[1]
    serial_interval = 5.5

    estimates = pd.DataFrame( {
        "estimate" : [above_50,growth_rate],
        "lower" : [above_50_lower,growth_rate - sigma_ab[1]],
        "upper" : [above_50_upper,growth_rate + sigma_ab[1]] }, index=["date", "growth_rate"] )
    estimates = estimates.T
    estimates["doubling_time"] = log(2) / estimates["growth_rate"]
    estimates["transmission_increase"] = serial_interval * estimates["growth_rate"]

    return tests, fit_df, estimates

def load_wastewater_data():
    return_df = pd.read_csv( "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/PointLoma_sewage_qPCR.csv", parse_dates=["Sample_Date"] )
    return_df.columns = ["date", "gene_copies", "reported_cases"]
    return_df.loc[~return_df["gene_copies"].isna(),"gene_copies_rolling"] = savgol_filter( return_df["gene_copies"].dropna(), window_length=11, polyorder=2 )
    return_df.loc[~return_df["reported_cases"].isna(),"reported_cases_rolling"] = savgol_filter( return_df["reported_cases"].dropna(), window_length=7, polyorder=2 )
    return return_df