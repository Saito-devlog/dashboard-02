import pandas as pd
import numpy as np

#| date | campaign | sessions | cost | conversions | revenue | CPC | CVR | CPA | ROAS |
def create_ad_data():
    np.random.seed(42)

    dates = pd.date_range("2024-01-01", periods=90)
    campaigns = ["Brand", "Non-Brand", "Retargeting"]

    data = []

    for date in dates:
        for campaign in campaigns:

            sessions = np.random.randint(80, 400)

            # キャンペーンごとにCVR差をつける
            if campaign == "Brand":
                cvr = np.random.uniform(0.08, 0.15)
            elif campaign == "Non-Brand":
                cvr = np.random.uniform(0.03, 0.07)
            else:
                cvr = np.random.uniform(0.05, 0.1)

            conversions = int(sessions * cvr)

            # CPCもキャンペーンごとに変える
            if campaign == "Brand":
                cpc = np.random.uniform(50, 100)
            elif campaign == "Non-Brand":
                cpc = np.random.uniform(100, 180)
            else:
                cpc = np.random.uniform(70, 130)

            cost = sessions * cpc
            revenue = conversions * np.random.uniform(8000, 15000)

            data.append([
                date,
                campaign,
                sessions,
                cost,
                conversions,
                revenue
            ])

    df = pd.DataFrame(data, columns=[
        "date",
        "campaign",
        "sessions",
        "cost",
        "conversions",
        "revenue"
    ])

    # KPI列も追加
    df["CPC"] = df["cost"] / df["sessions"]
    df["CVR"] = df["conversions"] / df["sessions"]
    df["CPA"] = df["cost"] / df["conversions"]
    df["ROAS"] = df["revenue"] / df["cost"]

    return df

def get_filtered_ad_data(start_date, end_date, campaign=None):

    df = create_ad_data()

    filtered = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]

    if campaign:
        filtered = filtered[filtered["campaign"] == campaign]

    return filtered.copy()