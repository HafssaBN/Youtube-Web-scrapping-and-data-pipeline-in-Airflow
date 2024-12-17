# dags/main_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime
from airflow.models import Variable

from scripts.scrapping import (
    get_channel_stats,
    get_video_ids,
    get_video_details,
    get_comments_in_videos,
    save_scraped_data
)
from scripts.preprocessing import preprocess_video_data
from scripts.data_analysis import analyze_video_performance
from scripts.sentiments import analyze_sentiment

import pandas as pd
import os
import nltk
import time

# Ensure NLTK stopwords are downloaded
nltk.download('stopwords')

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),  # Reduced retry delay
    'start_date': datetime(2024, 12, 16),  # Set your start date
}

# Initialize the DAG
with DAG(
    'video_data_processing_dag',
    default_args=default_args,
    description='A DAG for scraping, preprocessing, and analyzing video data',
    schedule_interval=timedelta(days=1),  # Adjust the schedule as needed
    catchup=False,
) as dag:

    # Task 1: Fetch Channel Statistics
    def fetch_channel_stats():
        from googleapiclient.discovery import build
        api_key = Variable.get("YOUTUBE_API_KEY")  # Using Airflow Variable
        youtube = build('youtube', 'v3', developerKey=api_key)
        channel_ids = ['UCoOae5nYA7VqaXzerajD0lg']  # Example channel IDs
        channel_stats = get_channel_stats(youtube, channel_ids)
        # Convert to DataFrame and save
        df = pd.DataFrame(channel_stats)
        df.to_csv('/opt/airflow/data/channel_stats.csv', index=False)
        print("Channel statistics fetched and saved.")

    fetch_channel_stats_task = PythonOperator(
        task_id='fetch_channel_stats',
        python_callable=fetch_channel_stats,
    )

    # Task 2: Fetch Video IDs from Playlist
    def fetch_video_ids():
        from googleapiclient.discovery import build
        api_key = Variable.get("YOUTUBE_API_KEY")  # Using Airflow Variable
        youtube = build('youtube', 'v3', developerKey=api_key)
        playlist_id = "UUoOae5nYA7VqaXzerajD0lg"  # Example playlist ID (uploads playlist)
        video_ids = get_video_ids(youtube, playlist_id)
        # Save video IDs to CSV
        df = pd.DataFrame(video_ids, columns=['video_id'])
        df.to_csv('/opt/airflow/data/video_ids.csv', index=False)
        print("Video IDs fetched and saved.")

    fetch_video_ids_task = PythonOperator(
        task_id='fetch_video_ids',
        python_callable=fetch_video_ids,
    )

    # Task 3: Fetch Video Details in Batches
    def fetch_video_details():
        from googleapiclient.discovery import build
        api_key = Variable.get("YOUTUBE_API_KEY")  # Using Airflow Variable
        youtube = build('youtube', 'v3', developerKey=api_key)
        # Read video IDs
        video_ids = pd.read_csv('/opt/airflow/data/video_ids.csv')['video_id'].tolist()
        video_details = get_video_details(youtube, video_ids)
        # Save video details to CSV
        df = pd.DataFrame(video_details)
        df.to_csv('/opt/airflow/data/video_details_raw.csv', index=False)
        print("Video details fetched and saved.")

    fetch_video_details_task = PythonOperator(
        task_id='fetch_video_details',
        python_callable=fetch_video_details,
    )

    # Task 4: Preprocess Video Data
    def preprocess_data():
        # Read raw video details
        df_raw = pd.read_csv('/opt/airflow/data/video_details_raw.csv')
        df_preprocessed = preprocess_video_data(df_raw)
        df_preprocessed.to_csv('/opt/airflow/data/video_details.csv', index=False)
        print("Data preprocessing completed and saved.")

    preprocess_data_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data,
    )

    # Task 5: Fetch Comments from Videos
    def fetch_comments():
        from googleapiclient.discovery import build
        api_key = 'AIzaSyAxs7uzwcGOqJftvR_p9gqZ2nT6KmwtKj4'  # Using Airflow Variable
        youtube = build('youtube', 'v3', developerKey=api_key)
        # Read video IDs
        video_ids = pd.read_csv('/opt/airflow/data/video_ids.csv')['video_id'].tolist()
        comments = get_comments_in_videos(youtube, video_ids)
        # Save comments to CSV
        df = pd.DataFrame(comments)
        df.to_csv('/opt/airflow/data/comments.csv', index=False)
        print("Comments fetched and saved.")

    fetch_comments_task = PythonOperator(
        task_id='fetch_comments',
        python_callable=fetch_comments,
    )

    # Task 6: Perform Sentiment Analysis on First 1000 Comments
    def perform_sentiment_analysis():
        # Read comments
        df_comments = pd.read_csv('/opt/airflow/data/comments.csv')
        comments_expanded = df_comments.explode('comments').reset_index(drop=True)
        comments_expanded.rename(columns={'comments': 'comment'}, inplace=True)
        comments_expanded.dropna(subset=['comment'], inplace=True)
        comments_expanded = comments_expanded[comments_expanded['comment'].str.strip() != '']
        
        # Limit to the first 1000 comments
        comments_to_analyze = comments_expanded.head(500)
        print(f"Performing sentiment analysis on {len(comments_to_analyze)} comments.")
        
        # Define batch size
        batch_size = 100  # Adjust based on your system's capability
        sentiments = []
        
        for start in range(0, len(comments_to_analyze), batch_size):
            end = start + batch_size
            batch_comments = comments_to_analyze['comment'].iloc[start:end].tolist()
            print(f"Analyzing comments {start + 1} to {min(end, len(comments_to_analyze))}...")
            batch_sentiments = analyze_sentiment(batch_comments)
            sentiments.extend(batch_sentiments)
            # Optional: Sleep to prevent rate limiting
            time.sleep(0.1)
        
        comments_to_analyze['sentiment'] = [result['label'] for result in sentiments]
        comments_to_analyze['sentiment_score'] = [result['score'] for result in sentiments]
        
        # Save sentiments to CSV
        comments_to_analyze.to_csv('/opt/airflow/data/comments_with_sentiment.csv', index=False)
        print("Sentiment analysis completed and saved.")

    sentiment_analysis_task = PythonOperator(
        task_id='sentiment_analysis',
        python_callable=perform_sentiment_analysis,
    )

    # Task 7: Save Data (Optional Placeholder)
    def save_data():
        # Assuming data is already saved in previous tasks
        print("Data saving step completed.")

    save_data_task = PythonOperator(
        task_id='save_data',
        python_callable=save_data,
    )

    # Task 8: Analyze Video Performance and Generate Plots
    def analyze_performance():
        # Read preprocessed video details
        df_video = pd.read_csv('/opt/airflow/data/video_details.csv')
        analyze_video_performance(df_video)
        print("Video performance analysis completed and plots saved.")

    analyze_performance_task = PythonOperator(
        task_id='analyze_performance',
        python_callable=analyze_performance,
    )

    # Define Task Dependencies
    fetch_channel_stats_task >> fetch_video_ids_task
    fetch_video_ids_task >> fetch_video_details_task
    fetch_video_details_task >> preprocess_data_task
    fetch_video_ids_task >> fetch_comments_task
    fetch_comments_task >> sentiment_analysis_task
    sentiment_analysis_task >> save_data_task
    save_data_task >> analyze_performance_task
