import json
from openai import OpenAI
import os 
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import sounddevice as sd
import numpy as np
import wavio
import src.calendar_service as cs
import src.calendar_utils as cu
import dateparser
from datetime import datetime, timedelta, timezone


# Load environment variables from .env file
load_dotenv()
print("Loading environment variables...")
# Retrieve API keys from environment variables
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")
openai_api_key = os.getenv("OPENAI_TOKEN")

if not eleven_labs_api_key:
    raise ValueError("API key not found. Please set the ELEVENLABS_API_KEY environment variable.")

if not openai_api_key:
    raise ValueError("API key not found. Please set the OPENAI_TOKEN environment variable.")

openai = OpenAI(api_key=openai_api_key)
elevenlabs = ElevenLabs(api_key=eleven_labs_api_key)

system_prompt = """
You are a proactive AI assistant with the ability to schedule events in the user's Google Calendar. 
When the user provides input, do the following:

1. Understand the user's intent:
   - If the user wants to schedule a calendar event, extract:
     - title of the event
     - start time just the time, e.g., "18:00"
     - end time just the time, e.g., "19:00" if no end time is provided, calculate it based on a default duration of 1 hour
     - optional description
   - If the user provides a duration instead of an end time, calculate the end_time automatically.
   - If the user input is not related to scheduling, no action is needed.

2. Always respond in a **single JSON object** with two keys:
   - "message": A concise, professional, and helpful natural language response suitable for TTS output. 
        Correct transcription errors silently, summarize key points, suggest 1-3 next actions if relevant, 
        and keep responses under 150 words unless more detail is requested.
   - "action": A JSON object for function execution or null if no action is required:
     - "action_type": "create_event"
     - "title": string
     - "start_time": string 
     - "end_time": string 
     - "description": string (optional)

3. Do not mention if short-term or long-term memory is empty. Do not include any extra explanations. 
Only output valid, parseable JSON.
"""

def parse_to_iso(natural_time, default_tz="Australia/Sydney"):
    # Convert natural language like "6pm tonight" to a datetime
    dt = dateparser.parse(
        natural_time,
        settings={"TIMEZONE": default_tz, "RETURN_AS_TIMEZONE_AWARE": True}
    )
    if dt is None:
        raise ValueError(f"Could not parse time: {natural_time}")
    return dt.isoformat()

def record_audio(filename="output.wav", duration=5, fs=44100, device=1):
    print("Recording started...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, device=device)
    sd.wait()  # Wait until recording is finished
    wavio.write(filename, audio_data, fs, sampwidth=2)
    print(f"Recording saved as {filename}")

def summarize_memory(memory):
    """ 
    Summarize the memory content.
    This function extracts key points from the memory file and suggests keywords for long-term retrieval.
    """
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. Summarize the following memory content into a concise summary. "
                    "Also, generate a list of 3-5 keywords that best capture the topics, actions, and important entities in this memory, this is based off the original prompt to capture the way the user interacts with the assistant."
                    "so they can be used to retrieve relevant memories later. "
                    "Return strictly as JSON with 'summary' and 'keywords'. "
                    "Example: {\"summary\": \"User loves pizza and orders it often.\", \"keywords\": [\"pizza\", \"food\", \"preference\"]}"
                )
            },
            {
                "role": "user",
                "content": f"{memory}"
            }
        ]
    )
    
    summary_str = response.choices[0].message.content

    # Convert to JSON
    try:
        summary_json = json.loads(summary_str)  # {'summary': ..., 'keywords': [...]}
    except json.JSONDecodeError:
        print("Error: Could not parse summary as JSON.")
        summary_json = {"summary": summary_str, "keywords": []}
    
    return summary_json
def get_relevant_long_term_memory(user_prompt):
    """
    Retrieve relevant long-term memory based on the user prompt.
    This function searches the long-term memory for relevant topics.
    """

    memory_file = "data/memory.json"
    
    # Load existing memory
    with open(memory_file, "r") as f:
        memory = json.load(f)
    
    relevant_memory = []
    for item in memory["long_term"]:
    # Check if any keyword matches
        if any(keyword.lower() in user_prompt.lower() for keyword in item["keywords"]):
            relevant_memory.append(item["summary"])
    print("Relevant long-term memory:", relevant_memory)
    return relevant_memory

def update_memory(role, content):
    """
    Update the memory with the latest interaction.
    This function appends the new interaction to the memory file.
    """
    memory_file = "data/memory.json"
    
    # Load existing memory
    with open(memory_file, "r") as f:
        memory = json.load(f)
    
    # Append new interaction
    memory["short_term"].append({"role": role, "content": content})

    if memory["short_term"] and len(memory["short_term"]) >= 6:
        old_message = memory["short_term"].pop(0) # remove the oldest message if we have more than 6 messages
        summary = summarize_memory([old_message])  # pass a list of messages
        memory["long_term"].append(summary)
    
    # Save updated memory
    with open(memory_file, "w") as f:
        json.dump(memory, f, indent=2)
    
    print("Memory updated.")

def assistant(prompt, memory_file="data/memory.json"):
    short_term_memory = []
    # Load existing memory
    with open(memory_file, "r") as f:
        memory = json.load(f)

    short_term_memory = memory["short_term"]

    if memory.get("long_term") and len(memory["long_term"]) > 0:
        long_term_memory = get_relevant_long_term_memory(prompt)
    else:
        long_term_memory = []
        print("No long-term memory to retrieve.")
        
    # Call Chat API
    response = openai.chat.completions.create(
        model="gpt-4-turbo",  # or "gpt-4-1106-preview" or "gpt-3.5-turbo"
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": f"Here is the recent conversation: {short_term_memory}. Relevant long-term facts: {long_term_memory} User request: {prompt}"
            }
        ]

    )

    # Print the actual response content
    
    text = response.choices[0].message.content

    return text

def play_character(text):
    # Generate and play voice with ElevenLabs
    
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio)


def transcribe_audio(filename="output.wav"):

    audio_file = open(filename, "rb")

    transcription = openai.audio.transcriptions.create(
        model="gpt-4o-transcribe", 
        file=audio_file, 
        response_format="text"
    )
    
    return transcription
    
def handle_json(reponse):
    try:
        response_json = json.loads(reponse)
    except json.JSONDecodeError:
        print("Error: Assistant output is not valid JSON")
        response_json = None
    if response_json:
        # Pass message to Eleven Labs TTS
        text = response_json["message"]

    # Call calendar function if action exists
    if response_json.get("action") and response_json["action"]["action_type"] == "create_event":
        action = response_json["action"]
        title = action.get("title")
        start_time = parse_to_iso(action.get("start_time"))
        end_time = parse_to_iso(action.get("end_time"))
        description = action.get("description")  # optional
    
        cu.create_event(cs.get_service(), title, start_time, end_time, description)

    return text

if __name__ == "__main__":
    record_audio(duration=10)  # Record for 10 seconds
    prompt = transcribe_audio()
    robert_response = assistant(prompt)
    response_text = handle_json(robert_response)  # Handle the JSON response
    update_memory("user", prompt)
    update_memory("assistant", response_text)
    play_character(response_text)  # Play the character's response