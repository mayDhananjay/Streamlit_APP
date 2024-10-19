import streamlit as st
import pandas as pd
import cv2
import datetime
from moviepy.editor import VideoFileClip, AudioFileClip
import speech_recognition as sr
import requests
import asyncio
import edge_tts
import moviepy.video.fx as vfx

# Set up the Streamlit page configuration
st.set_page_config(page_title='AI Video Generator', layout='wide')

# Create the app title and subtitle
st.title('🎥 AI Video Generator')
st.subheader('Upload a video file to enhance it with AI-generated audio.')

# File uploader for video files
uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save the uploaded video to a file
    with open("uploaded_video.mp4", "wb") as f:
        f.write(uploaded_file.read())

    # Display the uploaded video in a smaller size
    st.video("uploaded_video.mp4")

    # Extract audio from the uploaded video
    video = VideoFileClip("uploaded_video.mp4")
    audio = video.audio
    audio.write_audiofile("original_audio.wav")

    # Create a video capture object to calculate video duration
    data = cv2.VideoCapture('uploaded_video.mp4')
    frames = data.get(cv2.CAP_PROP_FRAME_COUNT)  # Get total frames
    fps = data.get(cv2.CAP_PROP_FPS)  # Get frames per second
    seconds = round(frames / fps)  # Calculate total duration in seconds
    video_time = datetime.timedelta(seconds=seconds)  # Format as timedelta

    # Extract text from the audio using speech recognition
    r = sr.Recognizer()
    with sr.AudioFile('original_audio.wav') as source:
        audio_data = r.record(source)
        Audio_txt = r.recognize_google(audio_data)  # Convert audio to text
        st.write("Extracted Text: ")
        st.success(Audio_txt)  # Display extracted text

    # AI Text generation using OpenAI
    azure_openai_key = "22ec84421ec24230a3638d1b51e3a7dc"  # API key
    azure_openai_endpoint = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"  # Endpoint

    if azure_openai_key and azure_openai_endpoint:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_openai_key
        }
        data = {
            "messages": [{
                "role": "user",
                "content": f"{Audio_txt}, and the video time is {video_time}. Please generate text that perfectly syncs with the video time while improving the text and avoiding filler words, aiming for a creative tone."
            }],
            "max_tokens": 150  # Limit response length
        }

        # Make a request to OpenAI
        response = requests.post(azure_openai_endpoint, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            improved_text = result["choices"][0]["message"]["content"].strip()  # Get improved text
            st.write("Improved Text: ")
            st.success(improved_text)  # Display improved text
        else:
            st.error(f"Error: {response.status_code} - {response.text}")  # Display error message
    else:
        st.warning("Please enter all required details.")

    # Function to convert text to speech
    async def text_to_speech(text: str) -> str:
        output_file = 'videoTest.mp3'  # Output file name
        communicate = edge_tts.Communicate(text, 'en-AU-WilliamNeural')  # Choose voice
        await communicate.save(output_file)  # Save audio file
        return output_file

    # Check if improved text exists
    if 'improved_text' in locals():
        output_audio_file = asyncio.run(text_to_speech(improved_text))  # Generate audio from improved text

        # Merge the new audio back into the video
        audio_clip = AudioFileClip(output_audio_file)

        # Ensure the audio syncs with the video length
        if audio_clip.duration < video.duration:
            audio_clip = audio_clip.fx(vfx.loop, duration=video.duration)  # Loop audio
        else:
            audio_clip = audio_clip.subclip(0, video.duration)  # Trim audio to match video length

        final_video = video.set_audio(audio_clip)  # Set the new audio to the video
        final_video.write_videofile("myVideo.mp4", codec="libx264", audio_codec="aac")  # Save the final video

        # Download button for the final video
        st.success("Video has been processed and is ready for download.")
        with open("myVideo.mp4", "rb") as file:
            st.download_button(label="Download Final Video", data=file, file_name="myVideo.mp4")
