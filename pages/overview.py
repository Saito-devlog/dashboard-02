import dash
import pandas as pd
from dash import dcc, html, Input, Output, callback,ctx
from data.data import create_ad_data
import plotly.graph_objects as go
import plotly.express as px

dash.register_page(__name__, path="/")
#data.pyにあるcreate_ad_data()←広告データ
#create_ad_data()は関数を実行する
#create_ad_data() を実行して返ってきた df をad_df という変数に入れる
ad_df = create_ad_data()

#----左のKPIカード----
#revenueを全部足す
total_revenue = ad_df["revenue"].sum()
#sessionを全部足す
total_sessions = ad_df["sessions"].sum()
#ROASの平均
avg_roas = ad_df["ROAS"].mean()

#----左KPIの差分表示用-----
#[前7日] [直近7日]を比較する

#データの一番新しい日付を取得
latest_date = ad_df["date"].max()

#最新日から7日間さかのぼったデータ
current_period = ad_df[
    ad_df["date"] > latest_date - pd.Timedelta(days=7)
]

#直近7日のさらに前の7日間
previous_period = ad_df[
    (ad_df["date"] <= latest_date - pd.Timedelta(days=7)) &
    (ad_df["date"] > latest_date - pd.Timedelta(days=14))
]

#df → データ,column → どの指標を比べるか,days → 期間（日数）
def calc_growth(df, column, days=7):
    #最新日を取得
    latest = df["date"].max()
    
    #直近期間の合計
    # Timedeltaは、datetime クラスの二つのインスタンス間の時間差をマイクロ秒精度で表す
    current = df[df["date"] > latest - pd.Timedelta(days=days)][column].sum()
    
    #前期間の合計
    previous = df[
        (df["date"] <= latest - pd.Timedelta(days=days)) &
        (df["date"] > latest - pd.Timedelta(days=days*2))
    ][column].sum()

    if previous == 0:
        return 0
    #(今 − 前) ÷ 前
    return (current - previous) / previous

#revenue、traffic、ROASを計算
rev_growth = calc_growth(ad_df, "revenue")
traffic_growth = calc_growth(ad_df, "sessions")
roas_growth = calc_growth(ad_df, "ROAS")


#日付変える→start_date, end_dateが変わる→callback発動→フィルター→グラフ更新
@callback(
    #中央の折れ線グラフ
    Output("main_line_chart", "figure"),
    #右の円グラフ
    Output("pie_chart", "figure"),
    #Revenue、childrenはdivの中身
    Output("revenue_value", "children"),
    #Revenueの数字、childrenはdivの中身
    Output("revenue_growth", "children"),
    #Traffic、childrenはdivの中身
    Output("traffic_value", "children"),
    #Trafficの数字、childrenはdivの中身
    Output("traffic_growth", "children"),
    #ROAS、childrenはdivの中身
    Output("roas_value", "children"),
    #ROASの数字、childrenはdivの中身
    Output("roas_growth", "children"),
    #日付フィルター、スタート日
    Input("date_filter", "start_date"),
    #日付フィルター、終了日
    Input("date_filter", "end_date"),
)



#日付と連動させる
def update_dashboard(start_date, end_date):

    end_date = pd.to_datetime(end_date)
    start_1m = end_date - pd.DateOffset(months=1)

    filtered_df = ad_df[
        (ad_df["date"] >= start_1m) &
        (ad_df["date"] <= end_date)
        ]

    # 折れ線グラフ
    fig = px.line(
        filtered_df,
        x="date",
        y="sessions",
        color="campaign",
        title="MONTH"
        )
    
    #円グラフ・キャンペーンごとのrevenue
    pie_data = filtered_df.groupby("campaign")["revenue"].sum().reset_index()
    
    fig_pie = px.pie(
        pie_data,
        names="campaign",
        values="revenue"
    )

    # KPI計算
    total_revenue = filtered_df["revenue"].sum()
    total_sessions = filtered_df["sessions"].sum()
    avg_roas = filtered_df["ROAS"].mean()

    # 増減率（直近7日ロジック再利用）
    rev_growth = calc_growth(filtered_df, "revenue")
    traffic_growth = calc_growth(filtered_df, "sessions")
    roas_growth = calc_growth(filtered_df, "ROAS")

    return (
        fig,
        fig_pie,
        f"¥{total_revenue:,.0f}",
        f"{rev_growth*100:+.1f}%",
        f"{total_sessions:,}",
        f"{traffic_growth*100:+.1f}%",
        f"{avg_roas:.2f}",
        f"{roas_growth*100:+.1f}%"
    )


#下のKPIカード用の集計関数
def calculate_kpis(filtered_df):
    sessions = filtered_df["sessions"].sum()
    conversions = filtered_df["conversions"].sum()
    cost = filtered_df["cost"].sum()
    revenue = filtered_df["revenue"].sum()

    cvr = conversions / sessions if sessions != 0 else 0
    cpa = cost / conversions if conversions != 0 else 0
    roas = revenue / cost if cost != 0 else 0

    return sessions, conversions, cvr, cpa, roas

# Trafficの増減
#フィルタを関数化・再利用(どこでも使える)
def filter_by_date(df, start_date, end_date):
    return df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]

# 増減率専用関数
def calculate_change(current_value, previous_value):
    if previous_value == 0:
        return 0
    #(今 - 前) ÷ 前
    return (current_value - previous_value) / previous_value

#下のKPIカード用のコールバック
@callback(
    Output("kpi-traffic", "children"),
    #Trafic差分
    Output("diff_traffic", "children"),
    Output("diff_traffic", "className"),
    #cvr差分
    Output("diff_cvr", "children"),
    Output("diff_cvr", "className"),
    #conversion差分
    Output("diff_conversion", "children"),
    Output("diff_conversion", "className"),
    #cpa差分
    Output("diff_cpa", "children"),
    Output("diff_cpa", "className"),
    Output("kpi-conversion", "children"),
    Output("kpi-cvr", "children"),
    Output("kpi-cpa", "children"),
    Input("date_filter", "start_date"),
    Input("date_filter", "end_date"),
)


#update_kpis
def update_kpis(start_date, end_date):

    # 今期間
    current_df = filter_by_date(ad_df, start_date, end_date)

    period_days = (
        pd.to_datetime(end_date) - pd.to_datetime(start_date)
    ).days

    prev_start = pd.to_datetime(start_date) - pd.Timedelta(days=period_days)
    prev_end = pd.to_datetime(start_date)

    # 前期間
    prev_df = filter_by_date(ad_df, prev_start, prev_end)

    # KPI取得
    sessions, conversions, cvr, cpa, roas = calculate_kpis(current_df)
    prev_sessions, prev_conversions, prev_cvr, prev_cpa, prev_roas = calculate_kpis(prev_df)

    # Traffic増減
    change = calculate_change(sessions, prev_sessions)
    change_class = get_change_class(change)

    # CVR増減
    diff_cvr = calculate_change(cvr, prev_cvr)
    cvr_change_class = get_change_class(diff_cvr)

    # Conversion増減
    diff_conversion = calculate_change(conversions, prev_conversions)
    conversions_change_class = get_change_class(diff_conversion)

    # cpa増減
    diff_cpa = calculate_change(cpa, prev_cpa)
    cpa_change_class = get_change_class(diff_cpa)

    return (
        f"{sessions:,}",
        f"{change:+.1%}",
        change_class,
        f"{diff_cvr:+.1%}",
        cvr_change_class,
        f"{diff_conversion:+.1%}",
        conversions_change_class,
        f"{diff_cpa:+.1%}",
        cpa_change_class,
        f"{conversions:,}",
        f"{cvr:.2%}",
        f"¥{cpa:,.0f}",
    )

#スパークラインは7日移動平均

#増減の色を切り替える関数（CSSで設定している）
def get_change_class(change):
    return f"kpi-change {'positive' if change >= 0 else 'negative'}"


# ---スパークライン Traffic ----------------------
#日時データを作る
ad_df["revenue_MA7"] = ad_df["revenue"].rolling(7).mean()

#差分計算
latest_7 = ad_df["revenue"].tail(7).sum()
prev_7 = ad_df["revenue"].tail(14).head(7).sum()
diff = (latest_7 - prev_7) / prev_7
#表示確認
#print(ad_df["revenue_MA7"])
#print(latest_7)
#print(prev_7)

def create_sparkline(df, metric, positive_is_good=True):

    ma_col = f"{metric}_MA7"

    trend = df[ma_col].iloc[-1] - df[ma_col].iloc[-3]

    if positive_is_good:
        color = "#16a34a" if trend > 0 else "#dc2626"
    else:
        color = "#16a34a" if trend < 0 else "#dc2626"

    fig = go.Figure()

    # 元データ（薄い）
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[metric],
        mode="lines",
        line=dict(width=1, color="rgba(0,0,0,0.15)"),
        hoverinfo="skip",
        showlegend=False
    ))

    # 移動平均
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[ma_col],
        mode="lines",
        line=dict(width=2, color=color),
        showlegend=False
    ))

    fig.update_layout(
        height=60,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig

@callback(
    Output("revenue-sparkline", "figure"),
    Input("revenue-sparkline", "id")
)

def update_revenue(value):
    # 日次で集計
    df_daily = (
        ad_df.groupby("date")
        .agg({
            "sessions": "sum",
            "cost": "sum",
            "conversions": "sum",
            "revenue": "sum"
        })
        .reset_index()
    )

    # 移動平均
    df_daily["revenue_MA7"] = df_daily["revenue"].rolling(7).mean()
    fig = create_sparkline(df_daily, "revenue", True)

    return fig

# ---スパークライン Traffic ----------------------
df_daily = (
    ad_df.groupby("date")
    .agg({
        "sessions": "sum",
        "cost": "sum",
        "conversions": "sum",
        "revenue": "sum"
    })
    .reset_index()
)
def create_sparkline_ma_only(df, metric, positive_is_good=True):

    ma_col = f"{metric}_MA7"

    trend = df[ma_col].iloc[-1] - df[ma_col].iloc[-3]

    if positive_is_good:
        color = "#16a34a" if trend > 0 else "#dc2626"
    else:
        color = "#16a34a" if trend < 0 else "#dc2626"

    fig = go.Figure()

    # 移動平均だけ
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[ma_col],
        mode="lines",
        line=dict(width=2, color=color),
        showlegend=False
    ))

    fig.update_layout(
        height=30,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig
#@callback(
#    Output("traffic-sparkline", "figure"),
#    Input("traffic-sparkline", "id")
#)
def update_traffic(_):

    df_daily = (
        ad_df.groupby("date")
        .agg({"sessions": "sum"})
        .reset_index()
    )

    df_daily["sessions_MA7"] = df_daily["sessions"].rolling(7).mean()

    fig = create_sparkline_ma_only(df_daily, "sessions", True)

    return fig

df_daily["sessions_MA7"] = df_daily["sessions"].rolling(7).mean()

## ---スパークライン ROAS ----------------------
df_daily = (
    ad_df.groupby("date")
    .agg({
        "sessions": "sum",
        "cost": "sum",
        "conversions": "sum",
        "revenue": "sum"
    })
    .reset_index()
)

df_daily["ROAS"] = df_daily["revenue"] / df_daily["cost"]
df_daily["ROAS_MA7"] = df_daily["ROAS"].rolling(7).mean()


def update_roas(_):

    df_daily = (
        ad_df.groupby("date")
        .agg({
            "cost": "sum",
            "revenue": "sum"
        })
        .reset_index()
    )

    df_daily["ROAS"] = df_daily["revenue"] / df_daily["cost"]
    df_daily["ROAS_MA7"] = df_daily["ROAS"].rolling(7).mean()

    fig = create_sparkline_ma_only(df_daily, "ROAS", True)

    return fig


#ここからレイアウト
layout = html.Div([
    #ナビゲーションリンク
    html.Nav([
        html.A("Overview", href="/", id="nav-overview", className="nav-link"),
        html.A("Deep Dive", href="/deepdive", id="nav-deepdive", className="nav-link"),
    ], className="navbar"),
    #サマリー
    html.Div([
        # アイコン部分
        html.Div(
            html.Img(
                src="/assets/graph.png",
                style={"width": "33px"}
            ),
            className="comment-icon"
    ),
        # テキスト部分
        html.Div(
            "広告CPAが直近14日で+18%悪化。一方でSEO経由CVRは改善傾向",
            className="comment-text"
        )
    ],
    className="comment-box"
),
    #ここに日付　カレンダーを出す
    html.Div([
    html.H4("Date"),
    dcc.DatePickerRange(
    id="date_filter",
    min_date_allowed=ad_df["date"].min(),
    max_date_allowed=ad_df["date"].max(),
    start_date=ad_df["date"].min(),
    end_date=ad_df["date"].max()
)], style={"margin-left":"1rem","margin-top":"2rem"}),

    # 左エリア（Revenue、Traffic、ROAS）
    html.Div([
        # 左カラム（KPIまとめる）
        html.Div([
            # Revenue
            html.Div([
                html.H2("Revenue"),
                html.H4(id="revenue_value"),
                # 差分とスパークライン
                html.Div([
                html.Span(id="revenue_growth"),
                dcc.Graph(
                id="revenue-sparkline",
                config={"displayModeBar": False},
                style={"width": "80px","height": "30px","padding-left":"1%"},
                className="sparkline"
            ) ],style={"display": "flex"})
            ], style={"margin-bottom": "20px"}),

            # Traffic
            html.Div([
                html.H3("Traffic"),
                html.H4(id="traffic_value"),
                # 差分
                html.Div([
                html.Span(id="traffic_growth",style={"margin-top": "1%"}),
                 ],style={"display": "flex"})
            ], style={"margin-bottom": "20px"}),

            # ROAS
            html.Div([
                html.H3("ROAS"),
                html.H4(id="roas_value"),
                # 差分
                html.Div([
                html.Span(id="roas_growth"),
                ],style={"display": "flex"})
            ])
        ], style={"width": "20%", "padding": "20px"}),

        # 中央
        html.Div([
        dcc.Graph(
            id="main_line_chart",
            config={"displayModeBar": False},
            style={"width": "100%"}
        )], style={
        "width": "55%",
        "box-sizing": "border-box"
    }),

        # 右
        html.Div(
            dcc.Graph(id="pie_chart"),
            style={"width": "25%"}
        )

    ], style={"display": "flex"}),
    # 下のKPIカード
    html.Div(
        children=[
        html.Div([
        html.H3("Traffic"),
        html.H4(id="kpi-traffic",style={"margin-bottom":"0"}),
        html.Span(
        id="diff_traffic",
    )
]),

        html.Div([
        html.H3("Conversion"),
        html.H4(id="kpi-conversion",style={"margin-bottom":"0"}),
        html.Span(
        id="diff_conversion",
    )
    ]),

        html.Div([
        html.H3("CVR"),
        html.H4(id="kpi-cvr",style={"margin-bottom":"0"}),
        html.Span(
        id="diff_cvr",
    )
]),

        html.Div([
        html.H3("CPA"),
        html.H4(id="kpi-cpa",style={"margin-bottom":"0"}),
        html.Span(
        id="diff_cpa",
    )
]),],style={"display": "flex","margin-top":"2%","justify-content":"space-between","width":"70%","margin-left":"10%"})
])

