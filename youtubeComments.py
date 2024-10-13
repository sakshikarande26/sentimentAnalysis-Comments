import os
import re
import streamlit as st
import matplotlib.pyplot as plt
from textblob import TextBlob
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import requests

# Load the .env file
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("YOUTUBE_API_KEY")

# Function to extract video ID from URL
def get_video_id(youtube_url):
    url_data = urlparse(youtube_url)
    query = parse_qs(url_data.query)
    return query["v"][0]

# Function to fetch comments
def fetch_comments(video_id):
    comments = []
    next_page_token = ''
    while len(comments) < 600:
        url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=100&key={api_key}&pageToken={next_page_token}"
        response = requests.get(url)
        if response.status_code != 200:
            st.error("Error fetching comments.")
            return comments

        data = response.json()
        for item in data['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return comments

# Function to perform sentiment analysis
def analyze_sentiment(comments):
    positive_comments, negative_comments, neutral_comments = [], [], []
    for comment in comments:
        analysis = TextBlob(comment)
        if analysis.sentiment.polarity > 0:
            positive_comments.append(comment)
        elif analysis.sentiment.polarity < 0:
            negative_comments.append(comment)
        else:
            neutral_comments.append(comment)
    return positive_comments, negative_comments, neutral_comments

# Function to get top comments
def get_top_comments(comments, n=3):
    sorted_comments = sorted(comments, key=lambda c: TextBlob(c).sentiment.polarity)
    return sorted_comments[:n], sorted_comments[-n:]

# Function to visualize results
def visualize_sentiment(positive_comments, negative_comments, neutral_comments):
    positive_count = len(positive_comments)
    negative_count = len(negative_comments)
    neutral_count = len(neutral_comments)

    labels = ['Positive', 'Negative', 'Neutral']
    comment_counts = [positive_count, negative_count, neutral_count]

    # Create pie chart
    fig1, ax1 = plt.subplots()
    colors = ['#FFB6C1', '#FF69B4', '#D8BFD8']
    ax1.pie(comment_counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Sentiment Distribution')

    # Create bar graph
    fig2, ax2 = plt.subplots()
    ax2.bar(labels, comment_counts, color=['#FFB6C1', '#FF69B4', '#D8BFD8'])
    plt.ylabel('Comment Count')
    plt.title('Sentiment Count Bar Graph')

    return fig1, fig2

# Streamlit app interface
st.title("YouTube Comment Sentiment Analysis")

# Get user input for YouTube URL
youtube_url = st.text_input("Enter YouTube URL:")

if youtube_url:
    try:
        # Process the URL and fetch comments
        video_id = get_video_id(youtube_url)
        st.write("Fetching comments...")
        comments = fetch_comments(video_id)

        # Perform sentiment analysis
        st.write("Analyzing sentiments...")
        positive_comments, negative_comments, neutral_comments = analyze_sentiment(comments)

        # Display sentiment breakdown
        st.write(f"Positive comments: {len(positive_comments)}")
        st.write(f"Negative comments: {len(negative_comments)}")
        st.write(f"Neutral comments: {len(neutral_comments)}")

        # Get top 3 most positive and negative comments
        top_negative, top_positive = get_top_comments(positive_comments + negative_comments)

        st.write("Top 3 Most Positive Comments:")
        for comment in top_positive:
            st.write(comment)

        st.write("Top 3 Most Negative Comments:")
        for comment in top_negative:
            st.write(comment)

        # Display sentiment distribution pie chart
        st.write("Sentiment Distribution (Pie Chart):")
        fig1, fig2 = visualize_sentiment(positive_comments, negative_comments, neutral_comments)
        st.pyplot(fig1)

        # Display sentiment count bar graph
        st.write("Sentiment Count (Bar Graph):")
        st.pyplot(fig2)

    except Exception as e:
        st.error(f"An error occurred: {e}")
