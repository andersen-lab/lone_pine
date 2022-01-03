from datetime import datetime

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from epiweeks import Week
from src.variants import VOC, VOI


#VOC = sorted( ["AY.1", "AY.2", "AY.3", "AY.3.1", "B.1.1.7", "B.1.351", "B.1.351.2", "B.1.351.3", "B.1.617.2", "P.1", "P.1.1", "P.1.2"] )
#VOI = sorted( ["AV.1", "B.1.427", "B.1.429", "B.1.525", "B.1.526", "B.1.526.1", "B.1.526.2", "B.1.617", "B.1.617.1", "B.1.617.3",
#      "B.1.621", "B.1.621.1", "B.1.1.318", "C.36.3", "C.37", "P.3", "P.2"] )


def _add_date_formating( fig, minimum, maximum ):
    min_date = pd.to_datetime( f"{minimum.year}-{minimum.month}-01" )
    maximum += pd.DateOffset( months=1 )
    max_date = pd.to_datetime( f"{maximum.year}-{maximum.month}-01" )

    intervals = pd.interval_range(start=pd.to_datetime( min_date ), end=pd.to_datetime( max_date ), freq="M" )

    for i in intervals[::2]:
        fig.add_vrect( x0=i.left, x1=i.right, fillcolor="#EFEFEF", opacity=1, layer="below" )

    fig.update_xaxes( dtick="M1", tickformat="%b\n%Y", mirror=True )
    fig.update_yaxes( mirror=True )
    fig.update_layout( template="simple_white",
                       hovermode="x unified",
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":0,"l":0,"b":0},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)" ) )

def get_date_limits( series ):
    # Max
    year = series.max().year
    month = series.max().month + 1
    if month == 13:
        month = 1
        year += 1
    day = 1
    max_lim = pd.to_datetime( f"{year}-{month}-{day}" )

    # min
    year = series.min().year
    month = series.min().month
    day = 1
    min_lim = pd.to_datetime( f"{year}-{month}-{day}" )
    return [min_lim, max_lim]

def plot_daily_cases_seqs( df ):
    #df.to_csv( "/Users/natem/Downloads/temp_presentation/daily_cases.csv" )
    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=df["date"], y=df["new_cases"],
                                 mode='markers',
                                 name='Daily Cases',
                                 marker={ "color" : "#767676" } ) )
    fig.add_trace(go.Scattergl(x=df["date"], y=df["new_sequences"],
                               mode='markers',
                               name='Daily Sequences',
                               marker={ "color" : "#DFB377"} ) )

    _add_date_formating( fig, minimum=df["date"].min(), maximum=df["date"].max() )
    min_lim = np.floor( np.log10( 0.75 ) )
    max_lim = np.ceil( np.log10( df["new_cases"].max() ) )
    fig.update_yaxes( type="log", dtick=1, title="<b>Number of cases</b>", range=[min_lim, max_lim] )
    fig.update_xaxes( range=get_date_limits( df["date"] ) )

    return fig

def plot_cummulative_cases_seqs( df ):
    #df.to_csv( "/Users/natem/Downloads/presentation/cum_cases.csv" )
    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=df["date"], y=df["cases"],
                               mode='lines',
                               name='Reported',
                               line={ "color" : '#767676', "width" : 4 } ) )
    fig.add_trace(go.Scattergl(x=df["date"], y=df["sequences"],
                             mode='lines',
                             name='Sequenced',
                             line={ "color" : "#DFB377", "width" : 4 } ) )

    _add_date_formating( fig, minimum=df["date"].min(), maximum=df["date"].max() )
    min_lim = np.floor( np.log10( df.loc[df["sequences"] > 0,"sequences"].min() ) )
    max_lim = np.ceil( np.log10( df["cases"].max() ) )
    fig.update_yaxes( type="log", dtick=1, title="<b>Cummulative cases</b>", range=[min_lim, max_lim] )
    fig.update_xaxes( range=get_date_limits( df["date"] ) )

    return fig

def plot_cummulative_sampling_fraction( df ):
    df["epiweek"] = df["date"].apply( lambda x: Week.fromdate(x).startdate() )
    plot_df = df.groupby( "epiweek" ).agg( new_cases = ("new_cases", "sum"), new_sequences = ("new_sequences", "sum" ) )
    plot_df = plot_df.loc[plot_df["new_sequences"]>0]
    plot_df["fraction"] = plot_df["new_sequences"] / plot_df["new_cases"]
    plot_df = plot_df.reset_index()

    #plot_df.to_csv( "/Users/natem/Downloads/presentation/sampling_fraction.csv" )

    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=plot_df["epiweek"], y=plot_df["fraction"],
                                 mode='lines',
                                 name='Fraction',
                                 line={ "color" : '#767676', "width" : 4 } ) )

    _add_date_formating( fig, minimum=plot_df["epiweek"].min(), maximum=plot_df["epiweek"].max() )

    fig.update_layout(  yaxis_tickformat='.1%' )

    #cleaned_array = np.log10( plot_df.loc[plot_df["fraction"] > 0, "fraction"] )
    #cleaned_array = cleaned_array[~np.isinf( cleaned_array )]

    fig.update_yaxes( type="log", title="<b>Cases sequenced (%)</b>" )
    fig.update_xaxes( range=get_date_limits( plot_df["epiweek"] ) )

    return fig

def add_missing_to_color_scale( scale, color="white" ):
    return_list = [[0, color],
                   [0.01, color]]
    len_scale = len( scale ) - 1
    for i, col in enumerate( scale ):
        if i == 0:
            return_list.append( [0.01, col] )
        else:
            return_list.append( [( 1 / len_scale ) * i, col] )
    return return_list

def plot_choropleth( sf, colorby="fraction" ):
    # TODO: This plot would be easier to read in a log scale.
    #  Requires modifying sf, the hoverdata, and then the colorscale.
    #  Ref: https://community.plotly.com/t/how-to-make-a-logarithmic-color-scale-in-my-choropleth-map/35010/3

    fig = px.choropleth( sf, geojson=sf.geometry,
                         locations=sf.index, color=colorby,
                         labels={"fraction": "Sequences per case",
                                 "case_count" : "Cases",
                                 "sequences" : "Sequences" },
                         hover_data=[ "case_count", "sequences", "fraction" ],
                         projection="mercator", color_continuous_scale=px.colors.sequential.Bluyl,
                         basemap_visible=False, fitbounds="geojson", scope=None )
    fig.update_geos( bgcolor="#ffffff" )
    fig.update_layout( autosize=True,
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":0,"l":0,"b":0} )
    return fig

def plot_lineages_time( df, lineage=None, scaleby="fraction" ):
    plot_df = df.pivot_table( index="epiweek", columns="lineage", values="ID", aggfunc="count" )
    plot_df = plot_df.fillna( 0 )

    yaxis_label = "Sequences"

    if scaleby == "fraction":
        plot_df = plot_df.apply( lambda x: x / x.sum(), axis=1 )
        yaxis_label += " (%)"

    max_lim = np.round( plot_df.sum( axis=1 ).max() * 1.05 )

    fig = go.Figure()
    if lineage is not None:
        focus_df = plot_df[lineage]
        plot_df = plot_df.drop( columns=lineage )
        plot_df = plot_df.sum( axis=1 )
        plot_df = pd.concat( [focus_df, plot_df], axis=1 )
        plot_df.columns = [lineage, "all"]
        fig.add_trace( go.Bar( x=plot_df.index, y=plot_df[lineage], name=lineage, marker_color="#DFB377" ) )
    else:
        plot_df = plot_df.sum(axis=1).reset_index()
        plot_df.columns = ["epiweek", "all"]
        plot_df = plot_df.set_index( "epiweek" )

    fig.add_trace( go.Bar( x=plot_df.index, y=plot_df["all"], name="All", marker_color='#767676' ) )
    fig.update_layout(barmode='stack')
    fig.update_yaxes( showgrid=False, title=f"<b>{yaxis_label}</b>", range=[0,max_lim] )

    fig.update_xaxes( range=get_date_limits( df["collection_date"] ) )
    _add_date_formating( fig, minimum=plot_df.index.min(), maximum=plot_df.index.max() )

    if scaleby == "fraction":
        fig.update_layout( yaxis_tickformat='.1%',
                           legend=dict( bgcolor="white" ) )

    return fig

def plot_voc( df, scaleby="fractions" ):
    plot_df = df.pivot_table( index="epiweek", columns="lineage", values="state", aggfunc="count", fill_value=0 ).T
    plot_df["VOC"] = plot_df.index.map( VOC )
    plot_df.loc[plot_df["VOC"].isna(),"VOC"] = "Other"
    plot_df = plot_df.groupby( "VOC" ).agg( "sum" ).T

    order = plot_df.sum().sort_values( ascending=False ).index.to_list()
    order.remove( "Other" )
    order.append( "Other" )

    plot_df = plot_df.reindex( columns=order )

    yaxis_label = "Sequences"
    if scaleby == "fraction":
        plot_df = plot_df.apply( lambda x: x / x.sum(), axis=1 )
        yaxis_label += " (%)"

    max_lim = np.round( plot_df.sum( axis=1 ).max() * 1.05 )

    fig = go.Figure()
    for i, j in enumerate( plot_df ):
        if j == "Other":
            color = "#767676"
        else:
            color = px.colors.colorbrewer.Set1[i]
        fig.add_trace( go.Bar( x=plot_df.index, y=plot_df[j], name=j, marker_color=color ) )

    fig.update_layout( barmode='stack' )
    fig.update_yaxes( showgrid=False, title=f"<b>{yaxis_label}</b>", range=[0, max_lim] )
    fig.update_xaxes( range=get_date_limits( plot_df.index ) )
    fig.update_layout( legend=dict( bgcolor="rgba(256,256,256,256)" ) )
    _add_date_formating( fig, minimum=plot_df.index.min(), maximum=plot_df.index.max() )

    if scaleby == "fraction":
        fig.update_layout( yaxis_tickformat='.1%',
                           legend=dict( bgcolor="white" ) )
    return fig

def plot_lineages( df ):

    plot_df = df["lineage"].value_counts().reset_index()

    colors = list()
    for i in plot_df["index"]:
        if i in sorted( VOI.keys() ):
            colors.append( "#4977CE" )
        elif i in sorted( VOC.keys() ):
            colors.append( "#AC6D41" )
        else:
            colors.append( "#767676" )

    fig = go.Figure()
    fig.add_trace( go.Bar( x=plot_df["index"], y=plot_df["lineage"], marker_color=colors ) )
    fig.update_yaxes( showgrid=True, title="<b>Number of sequences</b>" )
    fig.update_xaxes( title="<b>PANGO lineage</b>" )

    if len( plot_df ) > 50:
        fig.update_xaxes( range=[-0.5, 50.5] )
    else:
        fig.update_xaxes( range=[-0.5, len( plot_df ) - 0.5] )

    fig.update_layout( template="simple_white",
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":0,"l":0,"b":0},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)" ) )
    return fig

def plot_zips( df, colorby="sequences" ):
    fig = go.Figure()
    fig.add_trace( go.Bar( x=df["ziptext"], y=df[colorby], marker_color="#767676" ) )

    if colorby == "fraction":
        title="Cases sequenced (%)"
        fig.update_layout( yaxis_tickformat='.1%' )
    else:
        title="Number of sequences"

    max_lim = df[colorby].max() * 1.05
    if colorby == 'sequences':
        max_lim = np.round( max_lim )
    fig.update_yaxes( showgrid=True, title=f"<b>{title}</b>", range=[0,max_lim] )
    fig.update_xaxes( title="<b>ZIP code</b>", type="category", categoryorder="total descending" )
    if (df['sequences']>0).sum() > 65:
        fig.update_xaxes( range=[-0.5, 65.5] )
    else:
        fig.update_xaxes( range=[-0.5, (df['sequences']>0).sum() - 0.5] )
    fig.update_layout( template="simple_white",
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":0,"l":0,"b":0},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)" ) )
    return fig


def plot_sgtf( sgtf_data ):
    plot_df = sgtf_data[0]
    max_lim = np.round( plot_df["total_positive"].max() * 1.05 )
    #print( plot_df[["sgtf_likely","total_positive"]].sum( axis=1 ) )

    fig = make_subplots( specs=[[{"secondary_y" : True}]] )
    fig.add_trace( go.Bar( x=plot_df["Date"], y=plot_df["sgtf_likely"], name="SGTF <=30 Ct", marker_color="#E69F00" ), secondary_y=False )
    fig.add_trace( go.Bar( x=plot_df["Date"], y=plot_df["sgtf_unlikely"], name="SGTF >30 Ct", marker_color="#009E73" ), secondary_y=False )
    fig.add_trace( go.Bar( x=plot_df["Date"], y=plot_df["total_positive"] - plot_df["sgtf_likely"] - plot_df["sgtf_unlikely"], name="Total positive", marker_color="#56B4E9" ), secondary_y=False )
    fig.add_trace( go.Scattergl( x=plot_df["Date"], y=plot_df["percent"],
                                 mode='lines',
                                 name='SGTF (%)',
                                 showlegend=False,
                                 line={ "color" : "#000000", "width" : 2, "dash" : "dash"} ), secondary_y=True )
    fig.update_layout( barmode='stack' )
    fig.update_yaxes( showgrid=True, title=f"<b>Tests</b>", range=[0,max_lim], secondary_y=False )
    fig.update_yaxes( showgrid=False, title=f"<b>SGTF (%)</b>", secondary_y=True, range=[-0.01,1.01] )

    fig.update_xaxes( dtick="6.048e+8", tickformat="%b\n%d", mirror=True, showline=False, ticks="" )
    fig.update_yaxes( mirror=True, secondary_y=False, showline=False, ticks="" )
    fig.update_yaxes( tickformat='.0%', secondary_y=True, showline=False, ticks="" )
    fig.update_layout( template="simple_white",
                       hovermode="closest",
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":40,"l":0,"b":0},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)" ) )

    return fig


def plot_sgtf_estiamte( sgtf_data ):
    plot_df = sgtf_data[1]
    shade = "#E4E4E4"
    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=sgtf_data[0]["Date"], y=sgtf_data[0]["percent_filter"],
                                 mode='markers',
                                 name='SGTF (%)',
                                 showlegend=False,
                                 hoverinfo='skip',
                                 marker={ "color" : "#56B4E9", "size" : 12 } ) )
    fig.add_trace( go.Scattergl( x=plot_df["date"], y=plot_df["fit_y"],
                                 mode='lines',
                                 name='SGTF (%)',
                                 showlegend=False,
                                 line={ "color" : "#000000", "width" : 2} ) )
    fig.add_trace( go.Scatter( x=plot_df["date"], y=plot_df["fit_lower"],
                               mode='lines',
                               fillcolor=shade,
                               showlegend=False,
                               hoverinfo='skip',
                               line={"color" : shade} ) )
    fig.add_trace( go.Scatter( x=plot_df["date"], y=plot_df["fit_upper"],
                               mode='lines',
                               fill="tonextx",
                               fillcolor="rgba(0,0,0,0.1)",
                               showlegend=False,
                               hoverinfo='skip',
                               line={"color" : shade } ) )

    fig.update_xaxes( dtick="6.048e+8", tickformat="%b\n%d", mirror=True, showline=False, ticks="", showgrid=True )
    fig.update_yaxes( mirror=True, tickformat='.0%', showline=False, ticks="" )
    fig.update_yaxes( showgrid=True, title=f"<b>SGTF (%)</b>", range=[-0.01,1.01] )
    fig.update_layout( template="simple_white",
                       hovermode="closest",
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":40,"l":0,"b":10},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)" ) )
    fig.update_xaxes( range=["2021-11-25", "2022-02-01"] )

    esti = sgtf_data[2]
    date_str = f"99%: {esti['date'][0].strftime('%B %d')}<br>({esti['date'][1].strftime('%B %d')}-{esti['date'][2].strftime('%B %d')})"
    double_str =  f"Doubling time (days): {esti['doubling_time'][0]:.1f} ({esti['doubling_time'][1]:.1f} - {esti['doubling_time'][2]:.1f})<br>"
    growth_str =  f"Daily growth rate: {esti['growth_rate'][0]:.1%} ({esti['growth_rate'][1]:.1%} - {esti['growth_rate'][2]:.1%})<br>"
    transmission_str =  f"Transmission increase: {esti['transmission_increase'][0]:.0%} ({esti['transmission_increase'][1]:.0%} - {esti['transmission_increase'][2]:.0%})<br>"

    midpoint =  pd.to_datetime( sgtf_data[2]["date"]["estimate"] ).timestamp() * 1000
    fig.add_vline( midpoint, line_color="#ff6a6a", line_dash="dash", opacity=1, line_width=2 )
    fig.add_annotation( x=midpoint, y=1.10, yref="paper", text=date_str, showarrow=False, font={"color" : "#ff6a6a"} )

    fig.add_annotation( x="2021-12-19", y=0.2, text=double_str, showarrow=False, xanchor="left", bgcolor="#ffffff" )
    fig.add_annotation( x="2021-12-19", y=0.15, text=growth_str, showarrow=False, xanchor="left", bgcolor="#ffffff" )
    fig.add_annotation( x="2021-12-19", y=0.1, text=transmission_str, showarrow=False, xanchor="left", bgcolor="#ffffff" )

    return fig

def plot_wastewater( ww ):
    fig = make_subplots( specs=[[{"secondary_y" : True}]] )
    fig.add_trace( go.Scattergl( x=ww["date"], y=ww["gene_copies"],
                                 name="Viral load in wastewater",
                                 mode="markers",
                                 marker={"color" : "#56B4E9", "size" : 8 } ), secondary_y=False )
    fig.add_trace( go.Scattergl( x=ww["date"], y=ww["gene_copies_rolling"],
                                 showlegend=False,
                                 name="Viral load in wastewater",
                                 mode="lines",
                                 line={"color" : "#56B4E9", "width" : 3 } ), secondary_y=False )
    fig.add_trace( go.Scattergl( x=ww["date"], y=ww["reported_cases"],
                                 name="Reported cases",
                                 mode="markers",
                                 marker={"color" : "#D55E00", "size" : 8 } ), secondary_y=True )
    fig.add_trace( go.Scattergl( x=ww.dropna()["date"], y=ww.dropna()["reported_cases_rolling"],
                                 name="Reported cases",
                                 mode="lines",
                                 showlegend=False,
                                 line={"color" : "#D55E00", "width" : 3 } ), secondary_y=True )

    fig.update_yaxes( showgrid=True, title=f"<b>Mean viral gene copies / Liter</b>", secondary_y=False, showline=False, ticks="" )
    fig.update_yaxes( showgrid=False, title=f"<b>Reported Cases</b>", secondary_y=True, showline=False, ticks="" )
    fig.update_xaxes( dtick="M1", tickformat="%b\n%Y", mirror=True, showline=False, ticks="" )

    fig.update_layout( template="simple_white",
                       hovermode="closest",
                       plot_bgcolor="#ffffff",
                       paper_bgcolor="#ffffff",
                       margin={"r":0,"t":0,"l":0,"b":0},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)",
                                    itemsizing='constant') )

    return fig