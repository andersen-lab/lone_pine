from urllib.error import HTTPError
import pandas as pd
from arcgis import GIS
import datetime

def append_wastewater( sd ):
    zip_loc = "https://raw.githubusercontent.com/andersen-lab/SARS-CoV-2_WasteWater_San-Diego/master/Zipcodes.csv"
    zips = pd.read_csv( zip_loc, usecols=["Zip_code", "Wastewater_treatment_plant"], dtype={"Zip_code" : str, "Wastewater_treatment_plant" : str } )
    zips.columns = ["ziptext", "catchment"]
    zips["catchment"] = zips["catchment"].str.replace( " " , "" )
    zips = zips.set_index( "ziptext" )
    return_df = sd.merge( zips, left_on="ziptext", right_index=True, how="left" )
    return_df["catchment"] = return_df["catchment"].fillna( "Other" )

    assert return_df.shape[0] == sd.shape[0], f"Merge was unsuccessful. {sd.shape[0]} rows in original vs. {return_df.shape[0]} rows in merge output."
    return return_df

def download_sd_cases():
    """
    Returns
    -------
    pandas.DataFrame
        DataFrame detailing the daily number of cases in San Diego.
    """
    def _append_population( dataframe ):
        pop_loc = "resources/zip_pop.csv"
        pop = pd.read_csv( pop_loc, usecols=["Zip", "Total Population"], thousands=",", dtype={"Zip" : str, "Total Population" : int } )
        dataframe = dataframe.merge( pop, left_on="ziptext", right_on="Zip", how="left" )
        dataframe = dataframe.drop( columns=["Zip"] ).rename( columns={"Total Population" : "population"} )
        return dataframe

    def _add_missing_cases( entry ):
        entry = entry.set_index( "updatedate" ).reindex( pd.date_range( entry["updatedate"].min(), entry["updatedate"].max() ) ).rename_axis( "updatedate" ).reset_index()
        indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=7)
        entry["new_cases"] = entry.rolling( window=indexer, min_periods=1 )["new_cases"].apply( lambda x: x.max() / 7 )
        return entry

    gis = GIS()
    cases_loc = "34b6df47e084441790813348c69d49ee"
    gis_layer = gis.content.get( cases_loc )
    features = gis_layer.layers[0].query( where='1=1' )
    sd = features.df
    sd = sd[["ziptext","case_count", "updatedate"]]
    sd["updatedate"] = pd.to_datetime( sd["updatedate"] ).dt.tz_localize( None )
    sd["updatedate"] = sd["updatedate"].dt.normalize()
    #sd["ziptext"] = pd.to_numeric( sd["ziptext"] )
    sd = sd.groupby( ["updatedate", "ziptext"] ).last().reset_index()
    sd = sd.sort_values( "updatedate" )

    # Calculate cases per day because that's way more usable than cumulative counts.
    sd["case_count"] = sd["case_count"].fillna( 0 )
    sd["new_cases"] = sd.groupby( "ziptext" )["case_count"].diff()
    sd["new_cases"] = sd["new_cases"].fillna( sd["case_count"] )
    sd.loc[sd["new_cases"]<0, "new_cases"] = 0

    # Brief hack because SD stopped reporting daily cases and instead reports weekly cases after 2021-06-29.
    sdprob = sd.loc[sd["updatedate"]>"2021-06-28"]
    sdprob = sdprob.groupby( "ziptext" ).apply( _add_missing_cases )
    sdprob = sdprob.drop( columns="ziptext" ).reset_index()
    sdprob = sdprob.drop( columns="level_1" )

    sd = sd.loc[sd["updatedate"]<="2021-06-28"]
    sd = pd.concat( [sd,sdprob] )

    sd = _append_population( sd )

    sd["days_past"] = ( datetime.datetime.today() - sd["updatedate"] ).dt.days

    sd["case_count"] = sd.groupby( "ziptext" )["new_cases"].cumsum()

    # Add the catchment area
    sd = append_wastewater( sd )
    return sd

def download_bc_cases():
    """
    Returns
    -------
    pandas.DataFrame
        DateFrame detailing the daily number of cases in Baja California, Mexico
    """
    today = datetime.datetime.today()
    date_range = 10
    attempts = 0
    while attempts < date_range:
        print( f"Attemping to load BC data from {today.strftime( '%Y-%m-%d')}" )
        date_url = int( today.strftime( "%Y%m%d" ) )
        bc_url = f"https://datos.covid-19.conacyt.mx/Downloads/Files/Casos_Diarios_Estado_Nacional_Confirmados_{date_url}.csv"

        try:
            bc = pd.read_csv( bc_url, index_col="nombre" )
            break
        except HTTPError:
            today = today - datetime.timedelta( days=1 )
    else:
        raise RuntimeError( f"Unable to find a valid download link. Last url tried was {bc_url}" )

    bc = bc.drop( columns=["cve_ent", "poblacion"] )
    bc = bc.T
    bc = bc["BAJA CALIFORNIA"].reset_index()
    bc["index"] = pd.to_datetime( bc["index"], format="%d-%m-%Y" ).dt.tz_localize( None )
    bc["index"] = bc["index"].dt.normalize()
    bc.columns = ["updatedate", "new_cases"]
    bc = bc.sort_values( "updatedate" )

    # Generate the additional columns
    bc["case_count"] = bc["new_cases"].cumsum()
    bc["ziptext"] = "None"
    bc["population"] = 3648100
    bc["days_past"] = ( today - bc["updatedate"] ).dt.days

    bc = bc.loc[bc["case_count"] > 0]

    return bc

def download_cases():
    """ Downloads the cases per San Diego ZIP code. Appends population.
    Returns
    -------
    pandas.DataFrame
        DataFrame detailing the cummulative cases in each ZIP code.
    """
    sd = download_sd_cases()
    bc = download_bc_cases()
    c = pd.concat( [sd,bc] )

    return c

if __name__ == "__main__":
    cases = download_cases()
    cases.to_csv( "resources/cases.csv", index=False )