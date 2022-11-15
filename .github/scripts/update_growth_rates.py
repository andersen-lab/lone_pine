import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.dates as mdates
from scipy.signal import savgol_filter

SEQS_LOCATION = "../resources/sequences.csv"
VOC_LOCATION = "../resources/voc.txt"
CDC_LINEAGES = ["BA.5", "BA.5.2.6", "BA.4.6", "BQ.1.1", "BQ.1", "BN.1", "BF.7", "BA.4", "BA.2.75", "BA.2.75.2", "BA.2.12.1", "BA.2", "B.1.1.519", "BA.1.1", "B.1.617.2"]


def load_sequences():
    seqs = pd.read_csv( SEQS_LOCATION, usecols=["ID", "collection_date", "epiweek", "lineage", "state"],
                       parse_dates=["collection_date", "epiweek"] )
    seqs = seqs.loc[seqs["state"] == "San Diego"]
    return seqs


def smooth_sequence_counts( df : pd.DataFrame, weeks : list ):
    smoothed = df.pivot_table( index="epiweek", columns="lineage", values="state", aggfunc="count", fill_value=0 )
    smoothed = smoothed.apply( savgol_filter, window_length=7, polyorder=3 )
    smoothed[smoothed < 0] = 0
    smoothed = smoothed.apply( lambda x: x / x.sum(), axis=1 )
    smoothed = smoothed.loc[smoothed.index.isin( weeks )]
    smoothed = smoothed.loc[:, smoothed.max() > 0.005]
    smoothed.index = mdates.date2num( smoothed.index )
    return smoothed


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


def generate_table( rates_df : pd.DataFrame, seqs_df : pd.DataFrame, abundance_df : pd.DataFrame, weeks, vocs: dict[str] ):
    table = rates_df.reset_index()
    table.columns = ["lineage", "growth_rate"]

    table["variant"] = table["lineage"].map( vocs )

    total_counts = seqs_df["lineage"].value_counts()
    total_counts.name = "total_count"
    table = table.merge( total_counts, left_on="lineage", right_index=True, how="left" )

    recent_counts = seqs_df.loc[seqs_df["epiweek"].isin( weeks ), "lineage"].value_counts()
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
    fastest_growers.extend( CDC_LINEAGES )
    table_filtered = table_filtered.loc[table_filtered["lineage"].isin( fastest_growers )]
    return table_filtered, table


def calculate_growth_rates():
    seqs = load_sequences()
    last_weeks = calculate_last_weeks( seqs )
    smooth_seqs = smooth_sequence_counts( seqs, last_weeks )
    rates = smooth_seqs.apply( calculate_growth_rate )
    rates = rates.sort_values( ascending=False )

    voc_names = load_vocs()
    return generate_table( rates_df=rates, seqs_df=seqs, abundance_df=smooth_seqs, weeks=last_weeks, vocs=voc_names )


if __name__ == "__main__":
    growth_rates_filtered, all = calculate_growth_rates()
    growth_rates_filtered.to_csv( "../resources/growth_rates.csv", index=False )
    all.to_csv( "../resources/growth_rates_all.csv", index=False )