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
    ad_df["date"] >= latest_date - pd.Timedelta(days=7)
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

#月単位にまとめる（折れ線グラフで使う）
ad_df["date"] = pd.to_datetime(ad_df["date"])

ad_df["month"] = (
    ad_df["date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

monthly_df = (
    ad_df
    .groupby(["month", "campaign"], as_index=False)
    .agg({"sessions": "sum"})
)
#週単位にまとめる（折れ線グラフで使う）
ad_df["week"] = (
    ad_df["date"]
    .dt.to_period("W-MON")
    .dt.to_timestamp()
)

weekly_df = (
    ad_df
    .groupby(["week", "campaign"], as_index=False)
    .agg({"sessions": "sum"})
)

#日付変える→start_date, end_dateが変わる→callback発動→フィルター→グラフ更新
#returnの位置と合わせる
@callback(
    #中央の折れ線グラフ
    Output("main_line_chart", "figure"),

    #右の円グラフ
    Output("pie_chart", "figure"),
    #Revenue、childrenはdivの中身
    Output("revenue_value", "children"),
    #Revenueの数字、childrenはdivの中身
    Output("revenue_growth", "children"),
    Output("revenue_growth", "className"),
    #Traffic、childrenはdivの中身
    Output("traffic_value", "children"),
    #Trafficの数字、childrenはdivの中身
    Output("traffic_growth", "children"),
    Output("traffic_growth", "className"),
    #ROAS、childrenはdivの中身
    Output("roas_value", "children"),
    #ROASの数字、childrenはdivの中身
    Output("roas_growth", "children"),
    Output("roas_growth", "className"),
    #日付フィルター、スタート日
    Input("date_filter", "start_date"),
    #日付フィルター、終了日
    Input("date_filter", "end_date"),
    #タブ切り替え
    Input("tab-switch", "value"),
)



#日付と連動させる
def update_dashboard(start_date, end_date, tabs):

    end_date = pd.to_datetime(end_date)
    start_1m = end_date - pd.DateOffset(months=1)

    filtered_df = ad_df[
        (ad_df["date"] >= start_1m) &
        (ad_df["date"] <= end_date)
        ]

    # 折れ線グラフ
    if tabs == "month":
        filtered_df["period"] = (
            filtered_df["date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
    else:
        filtered_df["period"] = (
            filtered_df["date"]
            .dt.to_period("W-MON")
            .dt.to_timestamp()
        )

    grouped_df = (
        filtered_df
        .groupby(["period", "campaign"], as_index=False)
        .agg({"sessions": "sum"})
    )

    fig = px.line(
        grouped_df,
        x="period",
        y="sessions",
        color="campaign",
        color_discrete_map={
            "Brand": "#00bfff",
            "Retargeting": "#1877F2",
            "Non-Brand": "#b0c4de"
        }
    )

    #円グラフ・キャンペーンごとのrevenue
    pie_data = filtered_df.groupby("campaign")["revenue"].sum().reset_index()
    
    fig_pie = px.pie(
        pie_data,
        names="campaign",
        values="revenue",
        color="campaign",
        #穴をあける
        hole=0.4,
        height=513, 
        color_discrete_map={
        "Brand": "#6495ed",
        "Retargeting": "#1877F2",
        "Non-Brand": "#b0c4de",
        }
    )
    fig_pie.update_layout(
    margin=dict(t=30, b=30, l=40, r=0),
)

    # KPI計算
    total_revenue = filtered_df["revenue"].sum()
    total_sessions = filtered_df["sessions"].sum()
    avg_roas = filtered_df["ROAS"].mean()

    # 増減率（直近7日ロジック再利用）
    rev_growth = calc_growth(filtered_df, "revenue")
    traffic_growth = calc_growth(filtered_df, "sessions")
    roas_growth = calc_growth(filtered_df, "ROAS")

    #Revenuneの増減の数字
    rev_growth_text = f"{rev_growth*100:+.1f}%"
    rev_growth_class = get_growth_class(rev_growth)

    #Trafficの増減の数字
    traffic_growth_text = f"{traffic_growth*100:+.1f}%"
    traffic_growth_class = get_growth_class(traffic_growth)
    
    #ROASの増減の数字
    roas_growth_text = f"{roas_growth*100:+.1f}%"
    roas_growth_class = get_growth_class(roas_growth)
    #矢印を入れる
    arrow = "↑" if rev_growth >= 0 else "↓"
    rev_growth_text = f"{arrow} {rev_growth*100:+.1f}%"
    rev_growth_class = get_growth_class(rev_growth)

    return (
        fig,
        fig_pie,
        f"{int(total_revenue / 1000):,}k",
        traffic_growth_text,
        traffic_growth_class,
        f"{total_sessions:,}",
        rev_growth_text,
        rev_growth_class,
        f"{avg_roas:.2f}",
        roas_growth_text,
        roas_growth_class,
    )

#左のKPIカードの差分テキスト／className切り替えるための関数
def get_growth_class(value):
    return "kpi-change positive" if value >= 0 else "kpi-change negative"

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


#コメント生成関数
def generate_comment(diff_cpa, diff_cvr):

    diff_cpa = float(diff_cpa or 0)
    diff_cvr = float(diff_cvr or 0)

    # CPA判定
    if diff_cpa > 0.1:
        cpa_status = f"{abs(diff_cpa):.1%}悪化"
    elif diff_cpa < -0.1:
        cpa_status = f"{abs(diff_cpa):.1%}改善"
    else:
        cpa_status = "横ばい"

    # CVR判定
    if diff_cvr >= 0.03:
        cvr_status = "改善"
    elif diff_cvr <= -0.03:
        cvr_status = "悪化"
    else:
        cvr_status = "横ばい"
    print(type(diff_cpa), diff_cpa)
    
    return html.Span([
        "広告CPAが直近期間で",
        html.Strong(cpa_status),
        "。一方でSEO経由CVRは",
        html.Strong(cvr_status),
        "傾向。"
    ])

# 増減率専用関数
def calculate_change(current_value, previous_value):

    current_value = float(current_value)
    previous_value = float(previous_value)

    if previous_value == 0:
        return 0.0

    return (current_value - previous_value) / previous_value

#増減の色を切り替える関数（CSSで設定している）
def get_change_class(change, reverse=False):

    # 0は色つけないならここで処理
    if change == 0:
        return "kpi-change neutral"

    if reverse:
        is_positive = change < 0
    else:
        is_positive = change >= 0

    return f"kpi-change {'positive' if is_positive else 'negative'}"

#下のKPIカード用のコールバック
@callback(
    Output("kpi-traffic", "children"),
    #Trafic差分
    Output("diff_traffic", "children"),
    Output("diff_traffic", "className"),
    Output("kpi-traffic", "className"),
    #cvr差分
    Output("diff_cvr", "children"),
    Output("diff_cvr", "className"),
    Output("kpi-cvr", "className"),
    #conversion差分
    Output("diff_conversion", "children"),
    Output("diff_conversion", "className"),
    Output("kpi-conversion", "className"),
    #cpa差分
    Output("diff_cpa", "children"),
    Output("diff_cpa", "className",),
    Output("kpi-cpa", "className"),
    Output("kpi-conversion", "children"),
    Output("kpi-cvr", "children"),
    Output("kpi-cpa", "children"),
    Output("comment-text", "children"),
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

    # cpa増減(cpaは増えるとよくないから)
    diff_cpa = calculate_change(cpa, prev_cpa)
    cpa_change_class = get_change_class(diff_cpa, reverse=True)

    comment_text = generate_comment(diff_cpa, diff_cvr)


   #Dashは、変数名が同じでもOutputの順番に値を当てはめるだけ 
    return (
        f"{sessions:,}",
        f"{change:+.1%}",
        change_class,
        change_class,
        f"{diff_cvr:+.1%}",
        cvr_change_class,
        cvr_change_class,
        f"{diff_conversion:+.1%}",
        conversions_change_class,
        conversions_change_class,
        f"{diff_cpa:+.1%}",
        cpa_change_class,
        cpa_change_class,
        f"{conversions:,}",
        f"{cvr:.2%}",
        f"¥{cpa:,.0f}",
        comment_text
    )

#日時データを作る
ad_df["revenue_MA7"] = ad_df["revenue"].rolling(7).mean()

#差分計算
latest_7_revenue = ad_df["revenue"].tail(7).sum()
prev_7_revenue = ad_df["revenue"].tail(14).head(7).sum()

diff = (latest_7_revenue - prev_7_revenue) / prev_7_revenue



#表示確認
#print(ad_df["revenue_MA7"])
#print(latest_7)
#print(prev_7)


#ここからレイアウト
layout = html.Div([
    #ナビゲーションリンクはapp.pyに記述
    #サマリー
    html.Div([
        # アイコン部分
        html.Div(
            html.Img(
                src="/assets/graph.png",
                style={"width": "35px"}
            ),
            className="comment-icon"
    ),
        # テキスト部分
        html.Div(
            id="comment-text",
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
)], style={"margin-left":"2rem","margin-top":"2rem","margin-bottom":"2rem"}),

    # 左エリア（Revenue、Traffic、ROAS）
    html.Div([
        # 左カラム（KPIまとめる）
        html.Div([
            # Revenue
            html.Div([
                html.H2("Revenue"),
                html.H4(id="revenue_value"),
                # 差分
                html.Div([
                html.Span(id="revenue_growth"),
                 ],style={"display": "flex"})
            ], style={"margin-bottom": "20px"}),
                #KPIバー
                html.Div([
                html.Div(
                id="progress-bar-fill",   # ← これ必須
                className="progress-bar-fill"
                )
            ], className="progress-bar"),

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
        ], style={"width": "20%", "padding": "20px","margin-left":"2rem",}),

        # 中央
        html.Div([
        dcc.Tabs(
        id="tab-switch",
        value="month",
        children=[
            dcc.Tab(label="MONTH", value="month"),
            dcc.Tab(label="WEEK", value="week"),
        ]
        ),
        html.Div(id="tabs-content"),
        dcc.Graph(
            id="main_line_chart",
            config={"displayModeBar": False},
            style={"width": "100%"}
        )], style={
        "width": "46%",
        "box-sizing": "border-box",
        "padding-right":"2%",
    }),

        # 右
        html.Div(
            dcc.Graph(id="pie_chart"),
            style={"width": "26%","margin-right":"3%"}
        )

    ], style={"display": "flex"}),
    # 下のKPIカード
    html.Div(
        children=[
        html.Div([
        html.H3("Traffic",style={"margin-top":"0"}),
        html.H4(id="kpi-traffic",className="rev_growth_class"),
        html.Span(
        id="diff_traffic",
        )
    ],className="bottom-kpi-card"),

        html.Div([
        html.H3("Conversion",style={"margin-top":"0"}),
        html.H4(id="kpi-conversion"),
        html.Span(
        id="diff_conversion",
    )
    ],className="bottom-kpi-card"),

        html.Div([
        html.H3("CVR",style={"margin-top":"0"}),
        html.H4(id="kpi-cvr"),
        html.Span(
        id="diff_cvr",
    )
],className="bottom-kpi-card"),

        html.Div([
        html.H3("CPA",style={"margin-top":"0"}),
        html.H4(id="kpi-cpa"),
        html.Span(
        id="diff_cpa",
    )
],className="bottom-kpi-card"),],style={"display": "flex","margin-top":"2%","justify-content":"space-between","width":"96%"})
])

