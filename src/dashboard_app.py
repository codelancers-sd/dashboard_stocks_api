import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go
from io import StringIO
import datetime

st.set_page_config(layout="wide")
pd.options.mode.chained_assignment = None  # default='warn'


key='D64NACBJ98Z13QL6'

def format_hover_text_value(inp_obj):
    """
    Format float so that we do not show gazillion decimal points

    Input:
    inp_obj - value
    Returns:
    Formatted value
    """

    if isinstance(inp_obj, float):
        return f"{inp_obj:.2f}"

    else:
        return inp_obj

def make_portfolio_chart(data_df, title):

    hovertext_df = data_df[["port_current"]]
    hovertext_list = [list(item[1].items()) for item in hovertext_df.to_dict(orient="index").items()]
    hovertext = [ '<br />'.join([f"{pair[0]} = {format_hover_text_value(pair[1])}" for pair in values]) for values in hovertext_list ]

    port_evol = go.Scatter(
        x=data_df.index, 
        y=data_df["port_current"],
        mode="lines+markers",
        hovertext=hovertext,
        showlegend=True,
        name="Position",
        line=dict(width=4, color="#307ccf"),
        yaxis='y1')

    stock1_line = go.Scatter(
        x=data_df.index, 
        y=data_df["0__value"],
        mode="lines+markers",
        hovertext=hovertext,
        showlegend=True,
        name=f"{data_df['0__name'].iloc[0]}",
        opacity = 0.2,
        line=dict(width=4, color="#e41b47"),
        yaxis='y1')
    stock2_line = go.Scatter(
        x=data_df.index, 
        y=data_df["1__value"],
        mode="lines+markers",
        hovertext=hovertext,
        showlegend=True,
        name=f"{data_df['1__name'].iloc[0]}",
        opacity = 0.2,
        line=dict(width=4, color="#2bd481"),
        yaxis='y1')
    stock3_line = go.Scatter(
        x=data_df.index, 
        y=data_df["2__value"],
        mode="lines+markers",
        hovertext=hovertext,
        showlegend=True,
        name=f"{data_df['2__name'].iloc[0]}",
        opacity = 0.2,
        line=dict(width=4, color="#f8ba07"),
        yaxis='y1')

    layout = go.Layout(yaxis=dict(title='Position'))
    fig_plotly = go.Figure( data=[port_evol, stock1_line, stock2_line, stock3_line], layout=layout)
    fig_plotly.update_layout(
        autosize=False,
        width=1600,
        height=800,
        margin=dict(
        l=50,
        r=100,
        b=50,
        t=50,
        pad=4
        ),
    )
    fig_plotly.update_layout(title=f"{title}",font=dict( size=18,color="#2a057b" ) )
    fig_plotly.update_layout(legend=dict( yanchor="bottom", y=0.8, xanchor="left", x=1.05 )  )

    return fig_plotly

def make_fin_chart(data_df, title):

    df.columns = df.columns.str[3:]
    df.index = pd.to_datetime(df.index)
    df['open'] = df['open'].astype(float)
    df['volume'] = df['volume'].astype(float)


    hovertext_df = df
    hovertext_list = [list(item[1].items()) for item in hovertext_df.to_dict(orient="index").items()]
    hovertext = [ '<br />'.join([f"{pair[0]} = {format_hover_text_value(pair[1])}" for pair in values]) for values in hovertext_list ]

    open_price = go.Scatter(
        x=df.index, 
        y=df["open"],
        mode="lines+markers",
        hovertext=hovertext,
        showlegend=True,
        name="Price @ Open",
        line=dict(width=4, color="#3587ca"),
        yaxis='y1')

    vol = go.Bar(
        x=df.index, 
        y=df["volume"],
        # mode="lines+markers",
        hovertext=hovertext,
        showlegend=True,
        name="Volume",
        opacity=.3,
        # line=dict(width=4, color="#ce3157"),
        yaxis='y2')

    layout = go.Layout(yaxis=dict(title='Price'),
                       yaxis2=dict(title='Volume',
                                   overlaying='y',
                                   side='right'))
    fig_plotly = go.Figure( data=[open_price, vol], layout=layout)
    fig_plotly.update_layout(
        autosize=False,
        width=1600,
        height=800,
        margin=dict(
        l=50,
        r=100,
        b=50,
        t=50,
        pad=4
        ),
    )
    fig_plotly.update_layout(title=f"{title}",font=dict( size=18,color="#2a057b" ) )
    fig_plotly.update_layout(legend=dict( yanchor="bottom", y=0.8, xanchor="left", x=1.05 )  )

    return fig_plotly

def compute_portfolio_evol(df_dict, purchase_dict):

    port_evol_df = pd.DataFrame()

    for key in purchase_dict.keys():

        this_stock_name = df_dict[key][2]
        this_stock_df_all = df_dict[key][0]
        this_stock_df_all.index = pd.to_datetime(this_stock_df_all.index).tz_localize(None)
        data_sel_df = this_stock_df_all[ this_stock_df_all.index > pd.to_datetime(purchase_dict[key][0]).tz_localize(None)]
        data_sel_df.columns = data_sel_df.columns.str[3:]
        data_sel_df['no_shares'] = purchase_dict[key][1]
        data_sel_df['name'] = this_stock_name
        data_sel_df['open'] = data_sel_df['open'].astype(float)
        data_sel_df['value'] = data_sel_df['no_shares'] * data_sel_df['open']

        data_sel_df_crop = data_sel_df[ ["no_shares","open","value","name"] ].add_prefix(f"{key}__")
        port_evol_df = pd.concat( [port_evol_df, data_sel_df_crop], axis = 1)

    port_evol_df['port_current'] = port_evol_df[ [c for c in list(port_evol_df.columns) if "__value" in c] ].sum(axis=1)
    return port_evol_df

@st.cache
def load_symbols():

    url = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={key}'
    r = requests.get(url)
    df = pd.read_csv(StringIO(r.text))
    df['Stock'] = df['symbol'] + " -- " + df['name']

    return df[ df['symbol'].notna() ].reset_index(drop=True)
    
tab1, tab2 = st.tabs(["Financial ", "Porfolio simulation"])

with tab1:

    st.title(f"Financial dashboard")

    df_symbols = load_symbols().copy()
    try:
        init_index = df_symbols[ df_symbols['symbol'].str.contains("IBM") ].index[0]
    except:
        init_index = 0

    col1, col2 = st.columns(2)

    with col1:

        with st.form(f"Select the stock you wish to see data for"):

            stock_name_complex = st.selectbox("Available symbols", df_symbols['Stock'].to_list(), index=int(init_index)  )
            vote_submit_button = st.form_submit_button("Run chart")

    if vote_submit_button:

        stock_name = stock_name_complex.split("--")[0].strip()

        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stock_name}&apikey={key}'
        r = requests.get(url)
        data_json = r.json()

        df = pd.DataFrame(data_json['Time Series (Daily)']).T
        metadata_df = pd.DataFrame(data_json['Meta Data'], index=[0])

        fig = make_fin_chart(df, stock_name_complex)

        st.plotly_chart(fig)

        print(metadata_df)

with tab2:

    st.title(f"Portfolio simulation")

    col_date_start, col_stock, col_shares, temp = st.columns(4)
    delta_days = datetime.timedelta(days=90)

    with st.form(f"Select the date range", clear_on_submit=False):
            
        with col_date_start:        
            mindate1 = st.date_input( "Purchase date", datetime.datetime.now() - delta_days, key="mindate1", min_value=datetime.datetime.now() - delta_days)
            mindate2 = st.date_input( "Purchase date", datetime.datetime.now() - delta_days, key="mindate2", min_value=datetime.datetime.now() - delta_days)
            mindate3 = st.date_input( "Purchase date", datetime.datetime.now() - delta_days, key="mindate3", min_value=datetime.datetime.now() - delta_days)

        with col_stock:
            try:
                init_index1 = df_symbols[ df_symbols['symbol'].str.contains("IBM") ].index[0]
                init_index2 = df_symbols[ df_symbols['symbol'].str.contains("MSFT") ].index[0]
                init_index3 = df_symbols[ df_symbols['symbol'].str.contains("TSLA") ].index[0]
            except Exception as e:
                init_index1 = 0
                init_index2 = 1
                init_index3 = 2
                print(e)
            stock_name_complex1 = st.selectbox("Available symbols", df_symbols['Stock'].to_list(), index=int(init_index1), key="sn1"  )
            stock_name_complex2 = st.selectbox("Available symbols", df_symbols['Stock'].to_list(), index=int(init_index2), key="sn2"  )
            stock_name_complex3 = st.selectbox("Available symbols", df_symbols['Stock'].to_list(), index=int(init_index3), key="sn3"  )

        with col_shares:
            no_shares1 = st.number_input('No. of shares', min_value=1.0, format="%.2f", key = "no_shares1")
            no_shares2 = st.number_input('No. of shares', min_value=1.0, format="%.2f", key = "no_shares2")
            no_shares3 = st.number_input('No. of shares', min_value=1.0, format="%.2f", key = "no_shares3")
        
        portfolio_button = st.form_submit_button("Simulate portfolio")
        if portfolio_button:

            stock_name1 = stock_name_complex1.split("--")[0].strip()
            stock_name2 = stock_name_complex2.split("--")[0].strip()
            stock_name3 = stock_name_complex3.split("--")[0].strip()

            df_dict = {}
            purchase_dict = {
                0: [mindate1, no_shares1],
                1: [mindate2, no_shares2],
                2: [mindate3, no_shares3],
            }
            stock_name_complex_list = [stock_name_complex1,stock_name_complex2,stock_name_complex3]

            for idx,s in enumerate([stock_name1, stock_name2, stock_name3]):
                url_port = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={s}&apikey={key}'
                r_port = requests.get(url_port)
                data_port_json = r_port.json()

                try:
                    data_df_port = pd.DataFrame(data_port_json['Time Series (Daily)']).T
                    data_df_port.index = pd.to_datetime(data_df_port.index)
                    df_dict[idx] = [data_df_port, pd.DataFrame(data_port_json['Meta Data'], index=[0]), stock_name_complex_list[idx]]
                except Exception as e:
                    print( data_port_json )
                    print( e )
                    raise Exception(e)
                                

            st.write(f"Bought {no_shares1} shares of {stock_name1} on {mindate1}")
            st.write(f"Bought {no_shares2} shares of {stock_name2} on {mindate2}")
            st.write(f"Bought {no_shares3} shares of {stock_name3} on {mindate3}")

            print( df_dict )
            print( mindate1)

            portfolio_df = compute_portfolio_evol(df_dict, purchase_dict)
            print( portfolio_df )

            fig_port = make_portfolio_chart(portfolio_df, "Portfolio")

            st.plotly_chart(fig_port)