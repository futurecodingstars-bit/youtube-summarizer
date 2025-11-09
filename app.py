import os
import streamlit as st
from google import genai
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

load_dotenv() 
API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(layout="wide")
st.title("AI-Powered YouTube Video Summarizer")

if not API_KEY:
    st.error("Error: GEMINI_API_KEY not found. Please ensure it is set in your .env file.")
    st.stop()

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Error initializing Gemini client: {e}")
    st.stop()

def get_video_id(url):
    """Extracts the YouTube video ID from a given URL."""
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

def extract_transcript(video_id, preferred_lang="en"):
    """Fetches YouTube transcript using new API structure."""
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)

        # Try manual transcript first
        try:
            transcript = transcript_list.find_transcript([preferred_lang])
        except:
            # fallback: auto-generated transcript
            transcript = transcript_list.find_generated_transcript([preferred_lang])

        transcript_data = transcript.fetch()

        transcript_text = " ".join([item.text for item in transcript_data])

        return transcript_text

    except TranscriptsDisabled:
        st.error("Transcripts are disabled for this YouTube video.")
    except NoTranscriptFound:
        st.error("No transcript found in the requested language.")
    except Exception as e:
        st.error(f"Transcript extraction error: {e}")
    
    return None

def summarize_transcript(transcript, gemini_client):
    """Uses Gemini AI model to produce a structured summary."""
    prompt = f"""
    You are an expert AI productivity assistant. Your task is to summarize the following YouTube video transcript
    for professionals and students seeking maximum efficiency. The output must be highly professional and
    structured using Markdown for readability.

    Provide the following sections:
    1. A short, punchy summary (2–3 sentences)
    2. Exactly 5 clear Highlights (bullet points)
    3. Exactly 3 actionable Takeaways (numbered list)

    ---TRANSCRIPT---
    {transcript}
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return "❌ Summary failed due to an AI API error."

url = st.text_input("Paste the YouTube Video URL:", placeholder="Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ")

if st.button("Summarize Video") and url:

    video_id = get_video_id(url)

    if not video_id:
        st.error("Invalid YouTube URL. Make sure it links to a specific video.")
    else:
        st.subheader(f"Processing Video ID: `{video_id}`")

        with st.spinner("Extracting transcript and generating summary..."):
            transcript = extract_transcript(video_id)

            if transcript:
                summary = summarize_transcript(transcript, client)

                st.markdown("---")
                st.subheader("✅ Structured Summary")
                st.markdown(summary)

