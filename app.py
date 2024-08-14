import re
import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from googletrans import Translator

# Configure the Google API key directly
genai.configure(api_key="AIzaSyAcCjCbYvY3nk9cGTSTq4Odw5wHoJxfyHQ")

# Regular expression to extract video code
def extract_video_code(youtube_url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, youtube_url)
    
    if match:
        return match.group(1)
    else:
        return None

# Getting the transcript data from YouTube videos
def extract_transcript_details(youtube_video_url, target_language):
    try:
        video_id = extract_video_code(youtube_video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript_text = ""
        found_transcript = False
        
        for transcript in transcript_list:
            if transcript.language_code == target_language:
                st.write(f"Using transcript in original language: {transcript.language_code}")
                transcript_data = transcript.fetch()
                for i in transcript_data:
                    transcript_text += " " + i["text"]
                found_transcript = True
                break
            elif transcript.is_translatable and transcript.language_code != target_language:
                st.write(f"Translating transcript from {transcript.language_code} to {target_language}")
                translated_transcript = transcript.translate(target_language)
                transcript_data = translated_transcript.fetch()
                for i in transcript_data:
                    transcript_text += " " + i["text"]
                found_transcript = True
                break
        
        if not found_transcript:
            raise NoTranscriptFound("No suitable transcript found for the specified language.")
        
        return transcript_text

    except NoTranscriptFound as e:
        st.error(f"NoTranscriptFound: {e}")
        return None
    except ValueError as ve:
        st.error(f"ValueError: {ve}")
        return None
    except Exception as e:
        st.error(f"An error occurred during transcript extraction: {e}")
        return None

# Generate summary based on the prompt 
def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

# Translate summary into the desired language
def translate_summary(summary, target_language):
    if target_language == 'en':
        return summary  # No translation needed
    try:
        translator = Translator()
        translation = translator.translate(summary, dest=target_language)
        return translation.text
    except Exception as e:
        st.error(f"An error occurred during translation: {e}")
        return summary  # Fallback to original summary if translation fails

# Define the prompt variable
prompt = "Act as a YouTube video summarizer which will take the transcript of the video and provide the summary within 200 words. Provide the summary of the text given."

st.title("YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter your YouTube Link:")
target_language = st.text_input("Enter the language code for translation (e.g., 'es' for Spanish, 'fr' for French, 'en' for English):", value='en')

if youtube_link:
    video_id = extract_video_code(youtube_link)
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

if st.button("Get Detailed Notes"):
    st.write("Fetching transcript...")
    transcript_text = extract_transcript_details(youtube_link, target_language)

    if transcript_text:
        st.write("Generating summary...")
        summary = generate_gemini_content(transcript_text, prompt)
        
        if summary:
            st.write("Translating summary if necessary...")
            summary = translate_summary(summary, target_language)
            st.markdown("## Detailed Notes:")
            st.write(summary)

