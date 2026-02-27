import dash
from dash import html,dash_table,Input, Output, callback,ctx,dcc
import plotly.express as px
import pandas as pd

#seo_dataフォルダのseoデータをインポート
from data.seo_data import create_seo_data
#dataフォルダのadデータをインポート
from data.data import create_ad_data
from data.data import get_filtered_ad_data

#df = get_filtered_ad_data(start, end, campaign)

dash.register_page(__name__, path="/deepdive")

seo_df = create_seo_data()
#print(seo_df)
ad_df = create_ad_data()

print("Callback triggered")
print(seo_df.shape)

#CPA折れ線グラフ
@callback(
    Output("cpa-graph", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("campaign-dropdown", "value"),
)


def update_cpa(start, end, campaign):
    
    df = create_ad_data()
    df["date"] = pd.to_datetime(df["date"])

    if start and end:
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    if campaign:
        df = df[df["campaign"] == campaign]

    df = df.sort_values("date")

    # --- グラフ ---
    fig = px.line(df, x="date", y="CPA")
    fig.update_traces(line=dict(color="#1f4e8c", width=3))

    if len(df) >= 14:
        latest_7 = df.tail(7)
        prev_7 = df.tail(14).head(7)

        cpc_diff = (latest_7["CPC"].mean() - prev_7["CPC"].mean()) / prev_7["CPC"].mean()
        cvr_diff = (latest_7["CVR"].mean() - prev_7["CVR"].mean()) / prev_7["CVR"].mean()
    else:
        cpc_diff = 0
        cvr_diff = 0


    arrow_cpc = "↑" if cpc_diff > 0 else "↓"
    color_cpc = "green" if cpc_diff > 0 else "red"

    arrow_cvr = "↑" if cvr_diff > 0 else "↓"
    color_cvr = "green" if cvr_diff > 0 else "red"

    cpc_text = f"<span style='color:{color_cpc};'>CPC {arrow_cpc} {abs(cpc_diff):.1%}</span>"
    cvr_text = f"<span style='color:{color_cvr};'>CVR {arrow_cvr} {abs(cvr_diff):.1%}</span>"

    fig.update_layout(
        annotations=[
            dict(
                x=0.01,
                #テキストの座標
                y=1.1,
                xref="paper",
                yref="paper",
                text=f"{cpc_text} &nbsp;&nbsp; {cvr_text}",
                showarrow=False
            )
        ]
    )
    #Outputの順番=returnの順番、Outputの1番目=fig
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
            "CPAは+12%悪化。主因はCPC上昇。",
            className="comment-text"
        )
    ],
    className="comment-box"
),
    # 上段：日付とキャンペーン
    html.Div([
        html.Div([
            html.H4("Date"),
             #ここに日付　カレンダーを出す
            dcc.DatePickerRange(
            id="date-range",
            start_date="2024-01-01",
            end_date="2024-04-01"
        ),
        ], className="box"),

        html.Div([
            html.H4("Campaign"),

            dcc.Dropdown(
                id="campaign-dropdown",
                options=[
                    {"label": "Brand", "value": "Brand"},
                    {"label": "Non-Brand", "value": "Non-Brand"},
                    {"label": "Retargeting", "value": "Retargeting"},
                ],
                value="Brand"
            )
        ], className="box"),
    ], className="row"),

    # 下段：CPA表示とSEO表示
    html.Div([
        html.Div([
            html.H4("CPA表示"),
            html.Div(
            id="cpa-diff",
            #style={"margin-top": "10px"},
        ),
            dcc.Graph(id="cpa-graph")
            ], className="box_bottom"),

            html.Div([
                html.H4("SEO表示"),
                dash_table.DataTable(
                data=seo_df.to_dict("records"),
                columns=[{"name": i, "id": i} for i in seo_df.columns],
                sort_action="native",
                page_size=5,
                #style_header → ヘッダー全体
                style_header={"font-weight": "bold","font-size":"1rem"}
    )
            ], className="box_bottom"),

    ], className="row_bottom"),
])