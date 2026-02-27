import dash
import pandas as pd
from dash import dcc, html, Input, Output, callback,ctx
from data.data import create_ad_data
import plotly.graph_objects as go


ad_df = create_ad_data()

layout = html.Div([
    dcc.Location(id="url"),

    html.Nav([
        html.A("Overview", href="/", id="nav-overview", className="nav-link"),
        html.A("Deep Dive", href="/deepdive", id="nav-deepdive", className="nav-link"),
    ], className="navbar"),

        # アイコン部分
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

    html.H2("Date"),
    dcc.DatePickerRange(
        id="date-picker",
        start_date=ad_df["date"].min(),
        end_date=ad_df["date"].max(),
    ),
    
   # KPIカード
    html.Div([
        html.Div("Revenue", className="kpi-label"),
        html.Div([
            html.Span("¥", className="currency-symbol"),
            html.Span(id="kpi-diff", className="kpi-value"),
        ], className="kpi-main-value"),
   # Revenueの差分テキスト
        html.Div([
            html.Div(
                id="kpi-change",
                className="kpi-change"
            ),

            dcc.Graph(
                id="kpi-sparkline",
                config={"displayModeBar": False},
                className="kpi-sparkline"
            )
        ], className="kpi-change-row"),

    ], className="kpi-card"),
    #KPIバー
    html.Div([
    html.Div(
        id="progress-bar-fill",   # ← これ必須
        className="progress-bar-fill"
    )
], className="progress-bar"),

    html.Div([
    html.H3("Traffic"),
    html.H2(id="kpi-traffic"),
    html.P(id="kpi-traffic-diff")
    ])   
])


@callback(
    #id="nav-overview" の className を書き換える
    Output("nav-overview", "className"),
    #id="nav-deepdive" の className を書き換える
    Output("nav-deepdive", "className"),
    Input("url", "pathname"),
    prevent_initial_call=False
)
def update_active(pathname):
    print("PATH RAW:", repr(pathname)) # ← デバッグ用

#<a class="nav-link">を<a class="nav-link active">に変える
    if pathname == "/":
        return "nav-link active", "nav-link"
    elif pathname == "/deepdive":
        return "nav-link", "nav-link active"
    return "nav-link", "nav-link"

@callback(
    #Outputはまとめて書く
    Output("kpi-diff", "children"),
    Output("kpi-change", "children"),
    Output("kpi-sparkline", "figure"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date")
)
def update_revenue(start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered = ad_df[
        (ad_df["date"] >= start_date) &
        (ad_df["date"] <= end_date)
    ]

    total = filtered["revenue"].sum()
    # 前期間計算
    delta = end_date - start_date

    prev_start = start_date - delta
    prev_end = start_date

    prev_df = ad_df[
        (ad_df["date"] >= prev_start) &
        (ad_df["date"] < prev_end)
    ]

    prev_total = prev_df["revenue"].sum()

    if prev_total != 0:
        change_rate = (total - prev_total) / prev_total
    else:
        change_rate = 0

    change_text = f"{change_rate*100:+.1f}%"

    # データ集計
    daily = filtered.groupby("date")["revenue"].sum().reset_index()


    # スパークライン作成
    fig = go.Figure(
        go.Scatter(
            x=daily["date"],
            y=daily["revenue"],
            #mode="lines+markers",
            #marker=dict(size=[0]*(len(daily)-1)+[6]),
            line=dict(width=1.5, color="rgba(59,130,246,0.8)"),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.15)"
        )
    )

    fig.update_layout(
        height=60,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5"
    )

    return (
        f"{total:,.0f}",
        change_text,
        fig
    )

@callback(
    Output("progress-bar-fill", "style"),
    Input("kpi-diff", "children")
)
def update_progress(value):
    progress_value = 60
    return {"width": f"{progress_value}%"}

@callback(
    #id="kpi-traffic" の children(中身)を更新する
    Output("kpi-traffic", "children"),
    Output("kpi-traffic-diff", "children"),
    Output("kpi-traffic-diff", "className"),
    #date-picker が変わったら実行する
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date")
)

#Inputの数と引数の数は一致する
def update_traffic(start_date, end_date):

    current, _, diff_rate = calculate_traffic_diff(
        ad_df,
        start_date,
        end_date
    )

    if diff_rate > 0:
        change_class = "kpi-change positive"
    elif diff_rate < 0:
        change_class = "kpi-change negative"
    else:
        change_class = "kpi-change"

    return (
        f"{current:,}",
        f"{diff_rate:+.1%}",
        change_class
    )
#traffic
def calculate_traffic(df, start_date, end_date):
    filtered = df[
        (df["date"] >= start_date) &
        (df["date"] <= end_date)
    ]
    return filtered["sessions"].sum()

def calculate_traffic_diff(df, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # 現在期間
    current_df = df[
        (df["date"] >= start_date) &
        (df["date"] <= end_date)
    ]
    current = current_df["sessions"].sum()

    # 期間の長さ
    period_length = (end_date - start_date).days + 1

    # 前期間
    prev_end = start_date - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=period_length - 1)

    prev_df = df[
        (df["date"] >= prev_start) &
        (df["date"] <= prev_end)
    ]
    prev = prev_df["sessions"].sum()

    diff = current - prev
    diff_rate = diff / prev if prev != 0 else 0

    return current, diff, diff_rate