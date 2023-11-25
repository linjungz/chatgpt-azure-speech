#Note: The openai-python library support for Azure OpenAI is in preview.
      #Note: This code sample requires OpenAI Python library version 0.28.1 or lower.
import os
import openai
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from time import sleep


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
tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n" ]


def ask_and_reply(prompt): 
    message_text = [
        {"role":"system","content":"You are an AI assistant that helps people find information."},
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

    collected_messages = []
    last_tts_request = None

    for chunk in completion:
        # print(chunk)
        if len(chunk.choices) > 0:
            if "content" in chunk.choices[0].delta:
                print(chunk.choices[0].delta["content"], end='')

                chunk_message = chunk.choices[0].delta.content  # extract the chunk message from openai output
                collected_messages.append(chunk_message)  # aggregate the message

                if chunk_message in tts_sentence_end: # sentence end found
                    text = ''.join(collected_messages).strip() # join the recieved message together to build a sentence
                    if text != '': # if sentence only have \n or space, we could skip
                        
                        #streaming audio output
                        result = speech_synthesizer.start_speaking_text_async(text).get()
                        audio_data_stream = speechsdk.AudioDataStream(result)
                        audio_buffer = bytes(16000)
                        filled_size = audio_data_stream.read_data(audio_buffer)
                        while filled_size > 0:
                            filled_size = audio_data_stream.read_data(audio_buffer)

                        collected_messages.clear()

#main

ask_and_reply("Please explain how an air conditioner works in 200 words.")


    # print(chunk.choices[0].delta["content"], end='')

    