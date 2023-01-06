import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
from subprocess import run
import json
from pango_aliasor.aliasor import Aliasor
import re

SEQS_LOCATION = "resources/sequences.csv"
VOC_LOCATION = "resources/voc.txt"

aliasor = Aliasor()

def load_cdc_variants():
    # This link provides API access to the data found in this chart: https://covid.cdc.gov/covid-data-tracker/#variant-proportions
    # However, I haven't confirmed this doesn't change over time.
    init_url = "https://data.cdc.gov/resource/jr58-6ysp.json"
    request = run( f"curl -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36' {init_url}", shell=True, capture_output=True, text=True )
    response = json.loads( request.stdout )

    variants = ["XBB.1.5", "XBB"]
    for entry in response:
        if (entry["variant"] in variants) or (entry["variant"] == "Other"):
            continue
        variants.append( entry["variant"] )
    return variants

def load_sequences():
    seqs = pd.read_csv( SEQS_LOCATION, usecols=["ID", "collection_date", "epiweek", "lineage", "state"],
                       parse_dates=["collection_date", "epiweek"] )
    seqs = seqs.loc[seqs["state"] == "San Diego"]
    return seqs

def collapse_lineage( entry : str, accepted_lineages: set[str] ):
    if entry in accepted_lineages or "." not in entry:
        return entry
    elif re.match( "[A-Z]{2}.\d+$", entry ):
        return aliasor.partial_compress( aliasor.uncompress( entry ), accepted_aliases=["BA"] )
    return ".".join( entry.split( "." )[:-1] )

def model_sequence_counts( df : pd.DataFrame, weeks : list ):
    lg = LogisticRegression( multi_class="multinomial", solver="newton-cg", max_iter=1000 )
    lg.fit( df["epiweek_num"].to_numpy().reshape(-1,1), df["collapsed_linege"] )

    results = lg.predict_proba( mdates.date2num(weeks).reshape(-1,1) )
    results = pd.DataFrame( results, columns=lg.classes_, index=mdates.date2num(weeks) )
    return results, lg


def smooth_sequence_counts( df : pd.DataFrame, weeks : list, forced_lineages : list[str], rounds : int = 10, min_sequences : int = 50 ):
    last_seqs = df.loc[df["epiweek"].isin( weeks )].copy()

    previous_round = "lineage"
    for i in range( rounds ):
        counts = last_seqs[previous_round].value_counts()
        accepted = set( list( counts.loc[counts > min_sequences].index ) + forced_lineages )
        last_seqs[f"round_{i}"] = last_seqs[previous_round].apply( lambda x: collapse_lineage( x, accepted ) )

        previous_round = f"round_{i}"
        counts = last_seqs[previous_round].value_counts()
        print(
            f"Round {i} allowed {len( set( list( counts.loc[counts > min_sequences].index ) + forced_lineages ) )} lineages from {len( accepted )}" )
    else:
        last_seqs["collapsed_linege"] = last_seqs[previous_round]
        last_seqs = last_seqs.drop( columns=[i for i in last_seqs.columns if i.startswith( "round" )] )
        accepted = set( list( counts.loc[counts > min_sequences].index ) + forced_lineages )
        last_seqs.loc[~last_seqs["collapsed_linege"].isin( accepted ), "collapsed_linege"] = "Other"

    last_seqs["epiweek_num"] = mdates.date2num( last_seqs["epiweek"] )
    collapsed_names = last_seqs.groupby( "lineage" ).first()["collapsed_linege"].to_dict()

    smoothed, model = model_sequence_counts( last_seqs, weeks )

    return smoothed, model, collapsed_names


def calculate_last_weeks( df : pd.DataFrame ):
    last_weeks = df["epiweek"].value_counts().sort_index()
    last_weeks = last_weeks[last_weeks > 100]
    last_weeks = last_weeks[-8:].index
    return last_weeks


def calculate_growth_rate( entry: pd.Series ):
    logit = np.log( entry / (1-entry))
    logit = logit.replace([np.inf, -np.inf], np.nan )
    logit = logit.dropna()
    x = logit.index.values.reshape(-1, 1)
    y = logit.values.reshape(-1,1)
    linear_regressor = LinearRegression()
    linear_regressor.fit( x, y )
    return linear_regressor.coef_[0][0]


def load_vocs():
    with open( VOC_LOCATION, "r" ) as i:
        vocs = { k: v for k, v in map( lambda x: x.strip().split( ",", 1 ), i ) }
    return vocs


def generate_table(
        rates_df : pd.DataFrame,
        seqs_df : pd.DataFrame,
        abundance_df : pd.DataFrame,
        weeks, vocs: dict[str],
        forced_lineages : list[str],
):
    table = rates_df.reset_index()
    table.columns = ["lineage", "growth_rate"]

    table["variant"] = table["lineage"].map( vocs )

    total_counts = seqs_df["collapsed_lineage"].value_counts()
    total_counts.name = "total_count"
    table = table.merge( total_counts, left_on="lineage", right_index=True, how="left" )

    recent_counts = seqs_df.loc[seqs_df["epiweek"].isin( weeks ), "collapsed_lineage"].value_counts()
    recent_counts.name = "recent_counts"
    table = table.merge( recent_counts, left_on="lineage", right_index=True, how="left" )
    table = table.dropna( subset=["recent_counts"] )

    last_prop = abundance_df.iloc[-1]
    last_prop.name = "est_proportion"
    table = table.merge( last_prop, left_on="lineage", right_index=True, how="left" )
    table["first_date"] = mdates.num2date( abundance_df.index[0] ).strftime( "%Y-%m-%d" )
    table["last_date"] = mdates.num2date( abundance_df.index[-1] ).strftime( "%Y-%m-%d" )

    table = table.reindex(
        columns=["lineage", "variant", "total_count", "recent_counts", "est_proportion", "growth_rate", "first_date",
                 "last_date"] )
    table_filtered = table.loc[table["recent_counts"] > 5]

    fastest_growers = table_filtered.sort_values( "growth_rate", ascending=False ).head( 5 )["lineage"].to_list()
    fastest_growers.extend( forced_lineages )
    table_filtered = table_filtered.loc[table_filtered["lineage"].isin( fastest_growers )]
    return table_filtered, table


def add_collapsed_lineages( seqs: pd.DataFrame, names: dict[str] ):
    seqs["collapsed_lineage"] = seqs["lineage"].replace( names )
    return seqs

def calculate_growth_rates():
    cdc_lineages = load_cdc_variants()
    seqs = load_sequences()
    last_weeks = calculate_last_weeks( seqs )
    smooth_seqs, model, names = smooth_sequence_counts( seqs, last_weeks, forced_lineages=cdc_lineages )
    rates = smooth_seqs.apply( calculate_growth_rate )
    rates = rates.sort_values( ascending=False )

    seqs = add_collapsed_lineages( seqs, names )

    voc_names = load_vocs()
    return generate_table( rates_df=rates, seqs_df=seqs, abundance_df=smooth_seqs, weeks=last_weeks, vocs=voc_names, forced_lineages=cdc_lineages )


if __name__ == "__main__":
    growth_rates_filtered, all = calculate_growth_rates()
    growth_rates_filtered.to_csv( "resources/growth_rates.csv", index=False )
    all.to_csv( "resources/growth_rates_all.csv", index=False )