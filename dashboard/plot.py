import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

def _add_date_formating( fig ):
    # TODO: making background needs to be automated.
    for i in range( 3, 15, 2 ):
        year = 2020
        month = i
        if month > 12:
            year += 1
            month -= 12
        fig.add_vrect( x0=f"{year}-{month}-01", x1=f"{year}-{month+1}-01", fillcolor="#EFEFEF", opacity=1, layer="below" )

    fig.update_xaxes( dtick="M1", tickformat="%b\n%Y" )
    fig.update_layout( template="simple_white",
                       hovermode="x unified",
                       plot_bgcolor="#F9F9F9",
                       paper_bgcolor="#F9F9F9",
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
    day = 1
    max_lim = pd.to_datetime( f"{year}-{month}-{day}" )

    # min
    year = series.min().year
    month = series.min().month
    day = 1
    min_lim = pd.to_datetime( f"{year}-{month}-{day}" )
    return [min_lim, max_lim]

def plot_lineages( df, window=None, zip_f=None ):


    if window:
        df = df.loc[df["days_past"] <= window]

    if zip_f:
        if type( zip_f ) != list:
            zip_f = [zip_f]
        df = df.loc[df["zipcode"].isin( zip_f )]

    plot_df = df["lineage"].value_counts().reset_index()

    if len( plot_df ) > 50:
        plot_df = plot_df.iloc[:50]

    voc = ["B.1.1.7", "B.1.351", "P.1"]
    voi = ["B.1.427", "B.1.429", "B.1.526", "P.2"]
    colors = list()
    for i in plot_df["index"]:
        if i in voi:
            colors.append( "#4977CE" )
        elif i in voc:
            colors.append( "#AC6D41" )
        else:
            colors.append( "#767676" )

    fig = go.Figure()
    fig.add_trace( go.Bar( x=plot_df["index"], y=plot_df["lineage"], marker_color=colors ) )
    fig.update_yaxes( showgrid=True, title="<b>Number of sequences</b>" )
    fig.update_xaxes( title="<b>PANGO lineage</b>" )
    fig.update_layout( template="simple_white",
                       plot_bgcolor="#F9F9F9",
                       paper_bgcolor="#F9F9F9",
                       margin={"r":0,"t":0,"l":0,"b":0},
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0)" ) )
    return fig

def plot_daily_cases_seqs( df ):
    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=df["date"], y=df["new_cases"],
                                 mode='markers',
                                 name='Daily Cases',
                                 marker={ "color" : "#767676" } ) )
    fig.add_trace(go.Scattergl(x=df["date"], y=df["new_sequences"],
                               mode='markers',
                               name='Daily Sequences',
                               marker={ "color" : "#DFB377"} ) )

    _add_date_formating( fig )
    fig.update_yaxes( type="log", dtick=1, title="<b>Number of cases</b>" )
    fig.update_xaxes( range=get_date_limits( df["date"] ) )

    return fig

def plot_cummulative_cases_seqs( df ):
    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=df["date"], y=df["cases"],
                               mode='lines',
                               name='Reported',
                               line={ "color" : '#767676', "width" : 4 } ) )
    fig.add_trace(go.Scattergl(x=df["date"], y=df["sequences"],
                             mode='lines',
                             name='Sequenced',
                             line={ "color" : "#DFB377", "width" : 4 } ) )

    _add_date_formating( fig )
    fig.update_yaxes( type="log", dtick=1, title="<b>Cummulative cases</b>" )
    fig.update_xaxes( range=get_date_limits( df["date"] ) )

    return fig

def plot_cummulative_sampling_fraction( df ):
    fig = go.Figure()
    fig.add_trace( go.Scattergl( x=df["date"], y=df["fraction"],
                                 mode='lines',
                                 name='Fraction',
                                 line={ "color" : '#767676', "width" : 4 } ) )

    _add_date_formating( fig )

    min_lim = np.floor( np.log10( df["fraction"].min() ) )
    max_lim = np.ceil( np.log10( df["fraction"].max() ) )
    fig.update_yaxes( type="log", title="<b>Cummulative sampling fraction</b>", range=[min_lim,max_lim] )
    fig.update_xaxes( range=get_date_limits( df["date"] ) )

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
                         projection="mercator", color_continuous_scale=px.colors.sequential.Bluyl )
    fig.update_geos( fitbounds="locations",
                     visible=False,
                     bgcolor="#f9f9f9" )
    fig.update_layout( autosize=True,
                       plot_bgcolor="#F9F9F9",
                       paper_bgcolor="#F9F9F9",
                       margin={"r":0,"t":0,"l":0,"b":0} )
    return fig