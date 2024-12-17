from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime  # Direct import for clarity
import os
import logging

logging.basicConfig(
    filename='/opt/airflow/data_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)
# Function to get channel stats using YouTube API
def get_channel_stats(youtube, channel_ids):
    """
    Scrape channel statistics like subscribers, views, and videos.
    
    Parameters:
    youtube: build object of the YouTube API client
    channel_ids: list of channel IDs to scrape
    
    Returns:
    A DataFrame containing channel stats for each channel
    """
    all_data = []
   
    # Making API request to get channel details
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=','.join(channel_ids)
    )
    response = request.execute()

    # Loop through the response and extract useful data
    for item in response['items']:
        data = {
            'channelName': item['snippet']['title'],
            'subscribers': item['statistics']['subscriberCount'],
            'views': item['statistics']['viewCount'],
            'totalVideos': item['statistics']['videoCount'],
            'playlistId': item['contentDetails']['relatedPlaylists']['uploads']
        }
        all_data.append(data)

    # Return the data as a DataFrame
    return pd.DataFrame(all_data)

# Function to get video IDs from a playlist
def get_video_ids(youtube, playlist_id):
    video_ids = []

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')

    return video_ids

# Function to get video details
def get_video_details(youtube, video_ids):
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response['items']:
            stats_to_keep = {
                'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                'contentDetails': ['duration', 'definition', 'caption']
            }
            video_info = {'video_id': video['id']}

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try:
                        video_info[v] = video[k][v]
                    except KeyError:
                        video_info[v] = None

            all_video_info.append(video_info)

    return pd.DataFrame(all_video_info)

# Function to get comments from videos
def get_comments_in_videos(youtube, video_ids):
    all_comments = []

    for video_id in video_ids:
        try:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=10,  # Limit to first 10 comments
                textFormat="plainText"
            )
            response = request.execute()

            comments_in_video = [
                comment['snippet']['topLevelComment']['snippet']['textOriginal']
                for comment in response.get('items', [])
            ]
            comments_in_video_info = {'video_id': video_id, 'comments': comments_in_video}

            all_comments.append(comments_in_video_info)

        except Exception as e:
            # Log the error for debugging purposes
            print(f'Could not get comments for video {video_id}: {e}')

    return pd.DataFrame(all_comments)

# Function to save the scraped data to a CSV file with a timestamp
def save_scraped_data(df, prefix="scraped_data"):
    # Use the directory we mounted as a volume
    output_dir = "Youtube-Web-scrapping-and-data-pipeline-in-Airflow/data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"Data saved to {filepath}")

# Main function to orchestrate the entire process
def main(youtube, channel_ids, playlist_id):
    # Get channel stats
    channel_stats = get_channel_stats(youtube, channel_ids)
    print("Channel Stats:", channel_stats)

    # Get video IDs from playlist
    video_ids = get_video_ids(youtube, playlist_id)
    print("Video IDs:", len(video_ids), video_ids[:5])

    # Get video details
    video_details = get_video_details(youtube, video_ids)
    print("Video Details:", video_details)

    # Get comments from videos
    comments = get_comments_in_videos(youtube, video_ids)
    print("Comments:", comments)

    # Save data to CSV
    save_scraped_data(channel_stats, "channel_stats")
    save_scraped_data(video_details, "video_details")
    save_scraped_data(comments, "comments")
    
