import pandas as pd
import isodate

def preprocess_video_data(df):
    numeric_cols = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)

    # Convert publication date to datetime and add weekday column
    df['publishedAt'] = pd.to_datetime(df['publishedAt'], errors='coerce')
    df['publishDayName'] = df['publishedAt'].dt.strftime('%A')

    # Convert video duration to seconds
    df['durationSecs'] = df['duration'].apply(lambda x: isodate.parse_duration(x)).astype('timedelta64[s]')

    # Count the number of tathgs
    df['tagCount'] = df['tags'].apply(lambda x: 0 if x is None else len(x))

    return df
