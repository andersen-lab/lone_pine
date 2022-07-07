import numpy as np
import pandas as pd
from dash import html
from epiweeks import Week

from src.variants import VOC, VOI
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from numpy import exp, sqrt, diagonal, log
import geopandas as gpd

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


def load_growth_rates():
    return pd.read_csv( "resources/growth_rates.csv" )


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
                   {"label" : "All Delta lineages", "value" : "all-delta" },
                   {"label" : "All Omicron lineages", "value" : "all-omicron" },
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
    def lgm_mixture( ndays, x0_1, r_1, x0_2, r_2, x0_3, r_3 ):
        return lgm( ndays, x0_1, r_1 ) - lgm( ndays, x0_2, r_2 ) + lgm( ndays, x0_3, r_3 )

    tests = pd.read_csv( "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_SGTF_San-Diego/main/SGTF_San_Diego_new.csv", parse_dates=["Date"] )
    tests.columns = ["Date", "sgtf_all", "sgtf_likely", "sgtf_unlikely", "no_sgtf", "total_positive", "percent_low", "percen_all"]
    tests = tests.loc[~tests["Date"].isna()]
    tests["percent"] = tests["sgtf_all"] / tests["total_positive"]
    tests["percent_filter"] = savgol_filter( tests["percent"], window_length=5, polyorder=2 )
    tests["ndays"] = tests.index

    fit, covar = curve_fit(
        f=lgm_mixture,
        xdata=tests["ndays"],
        ydata=tests["percent_filter"],
        p0=[0.003, 0.008, 0.002, 0.008, 0.001, 0.008],
        bounds=([0] * 6, [np.inf] * 6)
    )
    sigma_ab = np.sqrt( np.diagonal( covar ) )

    days_sim = 400

    fit_df = pd.DataFrame( {"date" : pd.date_range( tests["Date"].min(), periods=days_sim ) } )
    fit_df["ndays"] = fit_df.index
    fit_df["fit_y"] = [lgm_mixture(i, *fit) for i in range( days_sim )]

    sigma_addition = sigma_ab
    # should be -1 when we want to include the term. I won't for now because the CI is so large.
    sigma_addition[4] *= 0
    sigma_addition[5] *= -1

    fit_df["fit_lower"] = [lgm_mixture( i, *(fit - sigma_addition) ) for i in range( days_sim )]
    fit_df["fit_upper"] = [lgm_mixture( i, *(fit + sigma_addition) ) for i in range( days_sim )]

    above_99 = fit_df.loc[(fit_df["date"] > "2022-04-15")&(fit_df["fit_y"] > 0.99),"date"].min()
    above_99_lower = fit_df.loc[(fit_df["date"] > "2022-04-15")&(fit_df["fit_lower"] > 0.99),"date"].min()
    above_99_upper = fit_df.loc[(fit_df["date"] > "2022-04-15")&(fit_df["fit_upper"] > 0.99),"date"].min()

    above_50 = fit_df.loc[(fit_df["date"] > "2022-04-15")&(fit_df["fit_y"] > 0.50),"date"].min()
    above_50_lower = fit_df.loc[(fit_df["date"] > "2022-04-15")&(fit_df["fit_lower"] > 0.50),"date"].min()
    above_50_upper = fit_df.loc[(fit_df["date"] > "2022-04-15")&(fit_df["fit_upper"] > 0.50),"date"].min()

    growth_rate = fit[5]
    serial_interval = 5.5

    estimates = pd.DataFrame( {
        "estimate" : [above_99, above_50, growth_rate],
        "lower" : [above_99_lower, above_50_lower, growth_rate - sigma_ab[5]],
        "upper" : [above_99_upper, above_50_upper, growth_rate + sigma_ab[5]] }, index=["date99", "date50", "growth_rate"] )
    estimates = estimates.T
    estimates["doubling_time"] = log(2) / estimates["growth_rate"]
    estimates["transmission_increase"] = serial_interval * estimates["growth_rate"]

    return tests, fit_df, estimates

def load_wastewater_data():
    def round_to_odd( value ):
        return np.ceil( np.floor( value ) / 2 ) * 2 - 1

    def load_ww_individual( loc, source ):
        temp = pd.read_csv( loc, parse_dates=["Sample_Date"] )
        temp["source"] = source
        temp.columns = ["date", "gene_copies", "source"]
        window_length = 11 if source == "PointLoma" else 5
        temp.loc[~temp["gene_copies"].isna(), "gene_copies_rolling"] = savgol_filter(
            temp["gene_copies"].dropna(), window_length=window_length, polyorder=2 )

        return temp

    def load_seq_individul( loc, source ):
        temp = pd.read_csv( loc, parse_dates=["Date"], index_col="Date" )
        temp["source"] = source
        return temp

    titer_template = "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/{}_sewage_qPCR.csv"
    seqs_template = "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/{}_sewage_seqs.csv"
    locations = ["PointLoma", "Encina", "SouthBay"]

    return_df = pd.concat( [load_ww_individual( titer_template.format( loc ), loc ) for loc in locations] )
    seqs = pd.concat( [load_seq_individul( seqs_template.format( loc ), loc ) for loc in locations] )

    return return_df, seqs

def load_catchment_areas():
    zip_loc = "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/Zipcodes.csv"
    zips = pd.read_csv( zip_loc, usecols=["Zip_code", "Wastewater_treatment_plant"] )

    sd = gpd.read_file( "resources/zips.geojson" )

    sd = sd.merge( zips, left_on=["ZIP"], right_on=["Zip_code"], how="outer" )
    sd = sd.loc[~sd["geometry"].isna()]
    sd["geometry"] = sd.simplify( 0.002 )
    sd["Wastewater_treatment_plant"] = sd["Wastewater_treatment_plant"].fillna( "Other" )
    sd["ZIP"] = sd["ZIP"].apply( lambda x: f"{x:.0f}" )
    sd = sd.set_index( "ZIP" )
    return sd

def load_ww_plot_config():
    """
    Loads the configuration file for the wastewater seqs plots. Essentially, the file specifies the name and color of
    lineages to be included.
    Returns
    -------
    dict
        Description of the name, lineage members, and color of each trace to be included in the plot.
    """
    import yaml
    from urllib import request

    try:
        config_url = request.urlopen( "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/plot_config.yml" )
        plot_config = yaml.load( config_url, Loader=yaml.FullLoader )
    except:
        print( "Unable to connect to remote config. Defaulting to local, potentially out-of-date copy." )
        with open( "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/plot_config.yml", "r" ) as f :
            plot_config = yaml.load( f, Loader=yaml.FullLoader )

    # Test the config is reasonable complete.
    assert "Other" in plot_config, "YAML is not complete. Does not contain 'Other' entry."
    for key in plot_config.keys() :
        for value in ["name", "members", "color"] :
            assert value in plot_config[key], f"YAML entry {key} is not complete. Does not contain '{value}' entry."

    return plot_config

def load_monkeypox_data():
    data = pd.read_csv( "resources/monkeypox.csv", parse_dates=["date"] )
    data["copies"] = data["copies"] * 1000000
    return data