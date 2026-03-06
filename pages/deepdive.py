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
#print(seo_df.shape)
#print(ad_df["CPC"])


# 増減率専用関数
def calculate_change(current_value, previous_value):

    current_value = float(current_value)
    previous_value = float(previous_value)

    if previous_value == 0:
        return 0.0

    return (current_value - previous_value) / previous_value

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


#コメント生成関数
def generate_comment(diff_cpa, diff_cpc):

    diff_cpa = float(diff_cpa or 0)
    cpc_diff = float(diff_cpc or 0)

    # CPA判定
    if diff_cpa > 0.1:
        cpa_status = f"{abs(diff_cpa):.1%}悪化"
    elif diff_cpa < -0.1:
        cpa_status = f"{abs(diff_cpa):.1%}改善"
    else:
        cpa_status = "横ばい"

     # CPC判定
    if cpc_diff >= 0.03:
        cpc_status = "改善"
    elif cpc_diff <= -0.03:
        cpc_status = "悪化"
    else:
        cpc_status = "横ばい"

    return html.Span([
        "CPAは",
        html.Strong(cpa_status),
        "。主因はCPC",
        html.Strong(cpc_status)
    ])


@callback(
    Output("comment-output", "children"),
    Input("kpi-data", "data")
)

def update_comment(data):

    if data is None:
        return ""

    diff_cpa = data["diff_cpa"]
    diff_cpc = data["diff_cpc"]

    return generate_comment(diff_cpa, diff_cpc)

@callback(
    Output("kpi-data", "data"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("campaign-dropdown", "value"),
)
def update_kpi_data(start, end, campaign):

    df = create_ad_data()
    df["date"] = pd.to_datetime(df["date"])

    if start and end:
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    if campaign:
        df = df[df["campaign"] == campaign]

    df = df.sort_values("date")

    latest_7 = df.tail(7)
    prev_7 = df.tail(14).head(7)

    diff_cpa = calculate_change(
        latest_7["CPA"].mean(),
        prev_7["CPA"].mean()
    )

    diff_cpc = calculate_change(
        latest_7["CPC"].mean(),
        prev_7["CPC"].mean()
    )

    return {
        "diff_cpa": diff_cpa,
        "diff_cpc": diff_cpc
    }

#ここからレイアウト
layout = html.Div([
    #ナビゲーションリンクはapp.pyに記述
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
        html.Div([
        dcc.Store(id="kpi-data"),
        html.Div(id="comment-output")
        ],
        id="deepdive-text",
        className="comment-text"
        )
    ],className="comment-box"
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
                style_header={"padding":"1.2%","font-weight": "bold","font-size":"1.2rem"},
            )  
            ], className="box_bottom"),

    ], className="row_bottom"),
])