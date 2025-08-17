# AI Voice Assistant

An intelligent AI assistant that interacts via voice, maintains short-term and long-term memory, and can schedule events in Google Calendar.

---

## Features

- **Voice Input & Output**: Uses `sounddevice` and `ffmpeg` for voice recording and ElevenLabs for TTS playback.
- **AI Response Generation**: Powered by OpenAI's GPT models.
- **Memory System**: 
  - Short-term memory for ongoing conversation context.
  - Long-term memory with summarization and keyword extraction.
- **Google Calendar Integration**: Add events directly to your Google Calendar via natural language commands.

---

## File Structure
```text
ALASSISTANT/
├─ pycache/
├─ .venv/
├─ data/
│ └─ memory.json
├─ src/
│ ├─ assistant.py
│ ├─ calendar_service.py
│ └─ calendar_utils.py
├─ .env
├─ credentials.json
├─ LICENSE
├─ output.wav
├─ README.md
└─ token.json
```
---

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) installed and in PATH
- Python packages in `requirements.txt` (create using `pip freeze > requirements.txt`):
  ```text
  openai
  python-dotenv
  elevenlabs
  sounddevice
  numpy
  wavio
  google-api-python-client
  google-auth-httplib2
  google-auth-oauthlib
  dateparser
## Setup
### 1. Clone the repo:
```bash 
git clone https://github.com/your-username/your-repo.git
cd your-repo
```
### 2. Create and activate a virtual environment:
```bash
python -m venv .venv
```
# Windows
```bash
.venv\Scripts\activate
```
# macOS/Linux
    source .venv/bin/activate

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```
### 4. Set up environment variables in .env:
```bash 
ELEVENLABS_API_KEY=your_elevenlabs_api_key
OPENAI_TOKEN=your_openai_api_key
```
### 5. Set up Google Calendar API:

Place credentials.json in the root folder.

On first run, a browser will open to authenticate and generate token.json.

## Usage
### Run the assistant:
```bash
python src/assistant.py
```
The assistant will:

1. Record your voice input.

2. Transcribe it using OpenAI.

3. Generate a response.

4. Optionally create calendar events.

5. Play the response via ElevenLabs TTS.

6. Update short-term and long-term memory automatically.

## Notes
Make sure .gitignore ignores .venv/ and __pycache__/.

Memory files (data/memory.json) are required for long-term memory functionality.

Adjust recording device in record_audio() if needed.

The AI expects natural language input for creating calendar events, e.g., "Schedule a meeting tomorrow at 3 PM for 1 hour."