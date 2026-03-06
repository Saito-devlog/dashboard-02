import dash
from dash import html,dcc,Input,Output,callback
from data.data import create_ad_data
from data.seo_data import create_seo_data

ad_df = create_ad_data()
seo_df = create_seo_data()

app = dash.Dash(__name__, use_pages=True)
server = app.server

@callback(
    Output("nav-overview", "className"),
    Output("nav-deepdive", "className"),
    Input("url", "pathname")
)
def update_nav(pathname):
    if pathname == "/deepdive":
        return "nav-link", "nav-link active"
    return "nav-link active", "nav-link"

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    #ナビゲーション
    html.Nav([
        html.A("Overview", href="/", id="nav-overview", className="nav-link"),
        html.A("Deep Dive", href="/deepdive", id="nav-deepdive", className="nav-link"),
    ], className="navbar"),

    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)