import os
from gtts import gTTS, lang
from openai import OpenAI

from moviepy.editor import VideoFileClip, concatenate_audioclips
from openai import OpenAI
import re

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set log level if needed

def synthesize_audio(translated_text, target_language, translations="translations", simulate_male_voice=False):
    LANGUAGES = {
        "Afrikaans": "af",
        "Albanian": "sq",
        "Arabic": "ar",
        "Armenian": "hy",
        "Bengali": "bn",
        "Bosnian": "bs",
        "Catalan": "ca",
        "Chinese": "zh",
        "Croatian": "hr",
        "Czech": "cs",
        "Danish": "da",
        "Dutch": "nl",
        "English": "en",
        "Esperanto": "eo",
        "Estonian": "et",
        "Filipino": "tl",
        "Finnish": "fi",
        "French": "fr",
        "German": "de",
        "Greek": "el",
        "Gujarati": "gu",
        "Hebrew": "iw",
        "Hindi": "hi",
        "Hungarian": "hu",
        "Icelandic": "is",
        "Indonesian": "id",
        "Italian": "it",
        "Japanese": "ja",
        "Javanese": "jw",
        "Kannada": "kn",
        "Kazakh": "kk",
        "Khmer": "km",
        "Korean": "ko",
        "Kurdish": "ku",
        "Kyrgyz": "ky",
        "Lao": "lo",
        "Latin": "la",
        "Latvian": "lv",
        "Lithuanian": "lt",
        "Macedonian": "mk",
        "Malagasy": "mg",
        "Malay": "ms",
        "Malayalam": "ml",
        "Maltese": "mt",
        "Marathi": "mr",
        "Mongolian": "mn",
        "Nepali": "ne",
        "Norwegian": "no",
        "Persian": "fa",
        "Polish": "pl",
        "Portuguese": "pt",
        "Punjabi": "pa",
        "Romanian": "ro",
        "Russian": "ru",
        "Serbian": "sr",
        "Sinhala": "si",
        "Slovak": "sk",
        "Slovenian": "sl",
        "Spanish": "es",  # Corrected the language code for Spanish
        "Swahili": "sw",
        "Swedish": "sv",
        "Tamil": "ta",
        "Telugu": "te",
        "Thai": "th",
        "Turkish": "tr",
        "Ukrainian": "uk",
        "Urdu": "ur",
        "Uzbek": "uz",
        "Vietnamese": "vi",
        "Welsh": "cy",
        "Xhosa": "xh",
        "Yiddish": "yi",
        "Yoruba": "yo",
        "Zulu": "zu",
    }

    logger.info(f"translated_text: {translated_text}")

    # Make sure the translations directory exists
    if not os.path.exists(translations):
        os.makedirs(translations)

    target_language_code = LANGUAGES.get(target_language, None)  # Use None instead of "None"

    try:
        # Simulate a male voice by adjusting the pitch. Note: This is a workaround and may not produce desired results.
        slow = simulate_male_voice
        
        tts = gTTS(text=translated_text, lang=target_language_code, slow=slow)
        audio_filename = os.path.join(translations, f"translated_audio_{target_language_code}.mp3")
        tts.save(audio_filename)

        return audio_filename
    except Exception as e:
        logger.error(f"Error synthesizing audio: {e}")
        return None

TEXT_CHUNK = 4000

def split_text_into_chunks(text):
    """
    Split the text into chunks of maximum size TEXT_CHUNK without cutting in the middle of a sentence.
    """
    chunks = []
    current_chunk = ""
    # Regular expression pattern for matching punctuation marks in multiple languages

    punctuation_pattern = r'[\.,!?;:؛،।。]'

    # Find all matches of the punctuation pattern in the text
    # Split text into sentences based on punctuation marks
    sentences = re.split(punctuation_pattern, text)
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= TEXT_CHUNK:  # Add 2 for the '. ' separator
            # Add sentence to current chunk
            current_chunk += sentence + '. '
        else:
            # Start a new chunk
            chunks.append(current_chunk)
            current_chunk = sentence + '. '
    if current_chunk:  # Add any remaining text as a chunk
        chunks.append(current_chunk)
    return chunks

def insert_pause(chunk):
    """
    Replace occurrences of 'DYNAMIC MUSIC' with a pause of around 10 seconds.
    """
    return chunk.replace('DYNAMIC MUSIC', ' [PAUSE:10] ')

def synthesize_audio_openai(translated_text, target_language, translations="translations", api_key=None, simulate_male_voice=False):
    """
    Synthesize audio for the translated text.
    """
    audio_filename = os.path.join(translations, f"translated_audio_{target_language}.mp3")
    if os.path.exists(audio_filename):
        return audio_filename

    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key)

        # Set model parameter based on the target language
        model = 'tts-1'  # Adjust the model based on your preference

        # Set voice parameter based on voice type
        voice = 'onyx' if simulate_male_voice else 'fable'  # Male voice if simulate_male_voice is True, else female voice

        # Split translated text into chunks
        text_chunks = split_text_into_chunks(translated_text)

        # Synthesize audio for each chunk and concatenate them
        audio_chunks = []
        for chunk in text_chunks:
            chunk_with_pause = insert_pause(chunk)
            response = client.audio.speech.create(model=model, voice=voice, input=chunk_with_pause)
            audio_chunks.append(response.content)

        # Save the synthesized speech to an MP3 file
        audio_filename = os.path.join(translations, f"translated_audio_{target_language}.mp3")
        with open(audio_filename, "wb") as audio_file:
            for chunk in audio_chunks:
                audio_file.write(chunk)

        return audio_filename
    except Exception as e:
        print(f"Error synthesizing audio: {e}")
        return None

if __name__ == "__main__":
    translated_text = "Welcome to today's episode where we're diving into the cutting edge world of AI with a focus on GPT-4 all. I'm your host Darya and in this brief introduction we'll explore what GPT-4 all is all about. "
    translations_dir = "../translations"
    api_key = "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"

    result = synthesize_audio(translated_text, "en", translations_dir, simulate_male_voice=False, api_key=api_key)

    if result:
        print(f"Audio file successfully created: {result}")
    else:
        print("Failed to create audio file.")