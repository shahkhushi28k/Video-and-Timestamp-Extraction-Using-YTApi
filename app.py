import streamlit as st
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi as yta, NoTranscriptFound

# API key
API_KEY = 'AIzaSyCzAl1InDV_CrXNLYP4JPqQyNGqjOyJT_Q'
youtube = build('youtube', 'v3', developerKey=API_KEY)

def search_youtube(query, max_results=10):
    """Search YouTube for videos matching the query."""
    try:
        request = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=max_results
        )
        response = request.execute()

        videos = []
        for item in response['items']:
            video_id = item['id'].get('videoId')
            title = item['snippet']['title']
            description = item['snippet']['description']
            if video_id:
                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'description': description
                })
        return videos
    except Exception as e:
        st.error(f"Error searching YouTube: {e}")
        return []

def analyze_transcript(transcript, query):
    """Analyze the transcript to find time lapses where the query appears."""
    time_lapses = []
    query_lower = query.lower()

    for entry in transcript:
        text = entry['text']
        start_time = entry['start']
        if query_lower in text.lower():
            time_lapses.append({
                'time': start_time,
                'text': text
            })

    return time_lapses

def format_time(seconds):
    """Convert seconds to a formatted time string."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def get_transcript(video_id):
    """Retrieve the transcript for a given video ID."""
    languages_to_try = ['en']
    for lang in languages_to_try:
        try:
            transcript = yta.get_transcript(video_id, languages=[lang])
            return transcript
        except NoTranscriptFound:
            st.warning(f"No transcript found for video {video_id} in {lang}")
        except Exception as e:
            st.error(f"Error getting transcript for video {video_id}: {e}")
            break
    return None

def display_results(user_query, max_results=10):
    """Display search results with time lapses and text for the query."""
    videos = search_youtube(user_query, max_results)

    results = []
    for video in videos:
        transcript = get_transcript(video['video_id'])
        if transcript:
            time_lapses = analyze_transcript(transcript, user_query)
            results.append({
                'title': video['title'],
                'link': f"https://www.youtube.com/watch?v={video['video_id']}",
                'description': video['description'],
                'time_lapses': [
                    {
                        'time': format_time(t['time']),
                        'text': t['text']
                    } for t in time_lapses
                ]
            })
        else:
            st.warning(f"No transcript available for video {video['video_id']}")

    # Sort results by the number of time lapses in descending order
    results.sort(key=lambda x: len(x['time_lapses']), reverse=True)

    # Display results
    for i, result in enumerate(results):
        st.subheader(f"{i + 1}. {result['title']}")
        st.write(f"**Link:** [Watch Video]({result['link']})")
        st.write(f"**Description:** {result['description']}")
        if result['time_lapses']:
            st.write("**Time Lapse** | **Text**")
            for time_lapse in result['time_lapses']:
                st.write(f"{time_lapse['time']} | {time_lapse['text']}")
        else:
            st.write("No relevant time lapses found.")
        st.write("---------")

# Streamlit UI
st.title("YouTube Transcript Search")
user_query = st.text_input("Enter your search query:", "")
max_results = st.slider("Number of results to show:", min_value=1, max_value=20, value=10)

if user_query:
    display_results(user_query, max_results)
