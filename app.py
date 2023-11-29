import os
import azure.cognitiveservices.speech as speechsdk
import openai
from dotenv import load_dotenv

import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Load environment variables from .env file
load_dotenv()

openai.api_type = "azure"
openai.api_base = "https://junlin-gpt4.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Should be the locale for the speaker's language.
speech_config.speech_recognition_language="en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI.
speech_config.speech_synthesis_voice_name='en-US-JennyMultilingualNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

# tts sentence end mark
tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n",]

def ask_and_reply(prompt, message_box):
    message_text = [
        {"role":"system","content":"You are an AI assistant that helps people find information. You need to be able to understand and answer questions about the world. Try to answer in one or two sentences. Be concise."},
        {"role":"user","content":prompt},
    ]

    completion = openai.ChatCompletion.create(
        engine="gpt-4-1106",
        messages = message_text,
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
    )

    print("OpenAI Request sent. Now waiting for response...")
    st.session_state.is_speaking = True

    collected_messages = []
    for chunk in completion:
        # print(chunk)
        if len(chunk.choices) > 0:
            if "content" in chunk.choices[0].delta:
                print("Chunk:", chunk.choices[0].delta["content"])
                chunk_message = chunk.choices[0].delta.content  # extract the chunk message from openai output
                collected_messages.append(chunk_message)  # aggregate the message

                if chunk_message[0] in tts_sentence_end: # sentence end found
                    text = ''.join(collected_messages).strip() # join the recieved message together to build a sentence
                    if text != '': # if sentence only have \n or space, we could skip
                        #streaming audio output
                        print("Now playing: {}".format(text))
                        message_box.write(f'ChatGPT: {text}')
                        result = speech_synthesizer.speak_text_async(text).get()
                        collected_messages.clear()
        if st.session_state.is_speaking == False:
            break

def stop_speaking():
    st.session_state.is_speaking = False

def record_voice():
    st.session_state.is_recording = True
    print(st.session_state.is_recording)
    # Get audio from the microphone and then send it to the TTS service.
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized speech: {}".format(speech_recognition_result.text))
        st.session_state.prompt_text = speech_recognition_result.text
        st.session_state.voice_recognized = True
        st.session_state.is_recording = False

    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))

    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

# UI

LOTTIE_URL = 'https://assets6.lottiefiles.com/packages/lf20_6e0qqtpa.json'

# Create the animation
def load_lottie(url):
    r = requests.get(url)
    if r.status_code != 200:
        return
    return r.json()

# Initialize session state
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "prompt_text" not in st.session_state:
    st.session_state.prompt_text = None
if "chat_text" not in st.session_state:
    st.session_state.chat_text = None
if "voice_recognized" not in st.session_state:
    st.session_state.voice_recognized = False
if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

lottie_anim = load_lottie(LOTTIE_URL)

st.set_page_config(page_title="ChatGPT Voice", page_icon='', layout='centered')

with st.container():
    left, right = st.columns([2, 3])
    with left:
        st_lottie(lottie_anim, speed=0.5, height=300, key="coding")
    with right:
        st.subheader('ChatGPT Voice Assistant')
        st.write('Press Record to start recording your voice.')

        rec_button = st.button(
            label="Record :microphone:", type='primary',
            on_click=record_voice,
            disabled=st.session_state.is_recording)
        
        stopo_button = st.button(
            label="Stop", type='primary',
            on_click=stop_speaking,
            disabled=not st.session_state.is_speaking)

        message_box = st.empty()
        if st.session_state.voice_recognized:
            message_box.write(f'You: {st.session_state.prompt_text}')

            # Send the prompt to OpenAI
            ask_and_reply(st.session_state.prompt_text, message_box)



    



