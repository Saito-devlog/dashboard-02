import pandas as pd
import numpy as np

#SEOデータ
def create_seo_data():
    keywords = ["Keyword01", "Keyword02", "Keyword03", "Keyword04", "Keyword05"]

    sessions = np.random.randint(5000, 10000, size=5)
    conversions = (sessions * np.random.uniform(0.02, 0.05, size=5)).astype(int)

    seo_df = pd.DataFrame({
        "keyword": keywords,
        "sessions": sessions,
        "conversions": conversions,
    })

    seo_df["cvr"] = seo_df["conversions"] / seo_df["sessions"]
    seo_df["cvr"] = (seo_df["cvr"] * 100).round(2)

    
    return seo_df

