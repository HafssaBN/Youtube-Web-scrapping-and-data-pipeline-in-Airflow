# Airflow YouTube Data Pipeline

## Overview

This project sets up an Apache Airflow DAG to scrape, preprocess, and analyze YouTube video data using Docker and Docker Compose.

## Features

- **Scraping:** Fetch channel statistics, video IDs, video details, and comments from YouTube.
- **Preprocessing:** Clean and prepare the scraped data for analysis.
- **Sentiment Analysis:** Analyze the sentiment of the first 1000 comments.
- **Data Analysis:** Generate performance metrics and visualizations for YouTube videos.

## Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your_username/airflow-youtube-pipeline.git
   cd airflow-youtube-pipeline
