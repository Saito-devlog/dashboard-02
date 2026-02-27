import dash
from dash import html
from data.data import create_ad_data
from data.seo_data import create_seo_data

ad_df = create_ad_data()
seo_df = create_seo_data()

app = dash.Dash(__name__, use_pages=True)

app.layout = html.Div([
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)