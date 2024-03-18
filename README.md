# Multilingual Text-to-Speech API with OpenAI, MistralAI, and Media Processing

A Python FastAPI application using:

* [OpenAI](https://openai.com/) Whisper for text summarization
* [MistralAI's TTS (Text to Speech)](https://mistral.ai) model for generating speech output
* Processes audio files, generating multilingual summaries and synthesizing spoken translation(s).

## Prerequisites
1. Ensure you have the following prerequisites installed:
   * Python 3.7+ [Install Python](https://www.python.org/downloads/)
   * A preferred code editor such as Visual Studio Code [Install VSC](https://code.visualstudio.com/) or any other IDE of your choice.
2. Project Dependencies:

pip install -r requirements.txt

3. Configure log settings (if needed) in the `logging.conf` file.
4. Run FastAPI application using `uvicorn main:app --reload`.

## Usage
1. Provide an audio file and get multilingual summaries and text-to-speech synthesis for each target language via a POST request with an MP3 file attachment. For instance:

curl -X POST 'http://localhost:8000/transcribe' 

-H 'Content-Type: multipart/form-data; charset=UTF-8' 

-F 'file=@path_to_input_audio.mp3'


## Project Structure
```python
multilingual_text2speech_api/
├── app/
│   ├── api/
│   └── configs/
│      └── logging.conf
│   ├── models/
│   └── utils/
├── logs/
├── README.md

## Features

    Text summarization using OpenAI Whisper for input audio files.
    Supports various target languages for generating multilingual summaries (e.g., English to Spanish or English to Mandarin).
    Real-time speech synthesis in each supported language.

## Roadmap

    Implementing real-time speech recognition functionality to enable users to input audio through API requests.
    Increase the supported multilingual options by using other third-party APIs or models if desired.
    Creating a Graphic User Interface (GUI) for a more interactive and user-friendly experience.
