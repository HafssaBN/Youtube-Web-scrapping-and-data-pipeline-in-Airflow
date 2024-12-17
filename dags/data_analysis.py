# data_analysis.py

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from wordcloud import WordCloud
from nltk.corpus import stopwords
import seaborn as sns
import pandas as pd
import os
import re

def save_plot(fig, filename):
    """
    Saves a matplotlib figure to the specified directory with the given filename.

    Parameters:
    - fig: The matplotlib figure object.
    - filename: The name of the file to save the plot as.
    """
    # Define the output directory
    output_dir = os.path.join('data', 'plots')  # Local 'data/plots' directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Define the full path for the plot
    filepath = os.path.join(output_dir, filename)
    
    # Save the figure
    fig.savefig(filepath, bbox_inches='tight')  # Ensure layout fits
    print(f"Plot saved to {filepath}")

def analyze_video_performance(video_df):
    """
    Analyzes video performance based on views, likes, comments, and duration.

    Parameters:
    video_df (DataFrame): DataFrame containing preprocessed video data
    """
    # === Debugging: Inspect Data Types ===
    print("\n=== Data Types of video_df ===")
    print(video_df.dtypes)
    
    print("\n=== Unique Values in 'publishDayName' ===")
    print(video_df['publishDayName'].unique())
    
    # === Ensure 'publishDayName' is String ===
    if video_df['publishDayName'].dtype != 'object':
        print("\nConverting 'publishDayName' to string...")
        video_df['publishDayName'] = video_df['publishDayName'].astype(str)
    
    # === Ensure 'durationSecs' is Integer ===
    if video_df['durationSecs'].dtype != 'int64':
        print("\nConverting 'durationSecs' to integer...")
        video_df['durationSecs'] = video_df['durationSecs'].astype(int)
    
    # === Clean 'title' for Plotting to Remove Emojis ===
    video_df['title_plot'] = video_df['title'].apply(
        lambda x: re.sub(r'[^A-Za-z\s]', '', x) if isinstance(x, str) else x
    )
    
    # === Best Performing Videos ===
    try:
        top_videos = video_df.sort_values('viewCount', ascending=False).head(9)
        ax = sns.barplot(x='title_plot', y='viewCount', data=top_videos)
        plt.xticks(rotation=90, ha='right')  # Rotate x-axis labels
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}K'.format(x/1000)))
        plt.title("Top 9 Best Performing Videos")
        plt.tight_layout()  # Adjust layout to prevent label cutoff
        save_plot(plt.gcf(), 'top_9_best_performing_videos.png')
        plt.close()
    except Exception as e:
        print(f"Error plotting Top 9 Best Performing Videos: {e}")
    
    # === Worst Performing Videos ===
    try:
        worst_videos = video_df.sort_values('viewCount', ascending=True).head(9)
        ax = sns.barplot(x='title_plot', y='viewCount', data=worst_videos)
        plt.xticks(rotation=90, ha='right')  # Rotate x-axis labels
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}K'.format(x/1000)))
        plt.title("Top 9 Worst Performing Videos")
        plt.tight_layout()
        save_plot(plt.gcf(), 'top_9_worst_performing_videos.png')
        plt.close()
    except Exception as e:
        print(f"Error plotting Top 9 Worst Performing Videos: {e}")
    
    # === View Distribution per Video ===
    try:
        sns.violinplot(x='channelTitle', y='viewCount', data=video_df)
        plt.title("View Distribution per Video")
        plt.tight_layout()
        save_plot(plt.gcf(), 'view_distribution_per_video.png')
        plt.close()
    except Exception as e:
        print(f"Error plotting View Distribution per Video: {e}")
    
    # === Views vs. Likes and Comments ===
    try:
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
        
        # Views vs. Comments
        sns.scatterplot(data=video_df, x='commentCount', y='viewCount', ax=ax[0])
        ax[0].set_title("Views vs. Comments")
        ax[0].set_xlabel("Comments")
        ax[0].set_ylabel("Views")
        
        # Views vs. Likes
        sns.scatterplot(data=video_df, x='likeCount', y='viewCount', ax=ax[1])
        ax[1].set_title("Views vs. Likes")
        ax[1].set_xlabel("Likes")
        ax[1].set_ylabel("Views")
        
        plt.tight_layout()
        save_plot(fig, 'views_vs_likes_and_comments.png')
        plt.close(fig)
    except Exception as e:
        print(f"Error plotting Views vs. Likes and Comments: {e}")
    
    # === Video Duration Distribution ===
    try:
        sns.histplot(data=video_df, x='durationSecs', bins=30, kde=False)
        plt.title("Video Duration Distribution")
        plt.xlabel("Duration (seconds)")
        plt.ylabel("Number of Videos")
        plt.tight_layout()
        save_plot(plt.gcf(), 'video_duration_distribution.png')
        plt.close()
    except Exception as e:
        print(f"Error plotting Video Duration Distribution: {e}")
    
    # === Wordcloud for Video Titles ===
    try:
        # Remove stopwords from titles
        stop_words = set(stopwords.words('english'))
        video_df['title_no_stopwords'] = video_df['title_plot'].apply(
            lambda x: ' '.join([word for word in x.split() if word.lower() not in stop_words])
        )
        
        all_words = ' '.join(video_df['title_no_stopwords'].tolist())
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=2000, 
            height=1000, 
            random_state=1, 
            background_color='black',
            colormap='viridis', 
            collocations=False
        ).generate(all_words)
        
        # Plot and save word cloud
        plt.figure(figsize=(20, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.tight_layout()
        wordcloud_filename = 'video_titles_wordcloud.png'
        plt.savefig(os.path.join('data', 'plots', wordcloud_filename), bbox_inches='tight')
        plt.close()
        print(f"Word cloud saved to data/plots/{wordcloud_filename}")
    except Exception as e:
        print(f"Error generating Word Cloud: {e}")
    
    # === Upload Schedule by Day of the Week ===
    try:
        day_counts = video_df['publishDayName'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ).fillna(0).astype(int).reset_index()
        day_counts.columns = ['Day', 'Count']
        
        ax = sns.barplot(x='Day', y='Count', data=day_counts)
        plt.title("Upload Schedule by Day of the Week")
        plt.xlabel("Day of the Week")
        plt.ylabel("Number of Uploads")
        plt.tight_layout()
        save_plot(plt.gcf(), 'upload_schedule_by_day_of_week.png')
        plt.close()
    except Exception as e:
        print(f"Error plotting Upload Schedule by Day of the Week: {e}")
