# translate.py
import os
import time
import requests
from openai import OpenAI
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage


import re
from .tokenizer_limiter import sent_tokenize, count_tokens

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) #Set log level if needed

# Regular expression pattern
pattern = r'The text is written in (\w+) and translates to (\w+):'


def translate_text_with_ollama(source_text, target_language, api_key = None, prompt = None , model="llama2"):
    """
    Translates a given text using the Mistral model from Ollama.

    Args:
        text_to_translate (str): The input text to be translated
        target_language (str): The target language for translation

    Returns:
        str: The translated text or None if an error occurs.
    """

    ollama_url = "http://localhost:11434/api/chat"  # Replace this URL with the actual Ollama instance's URL
    #ollama_url = "http://localhost:11434/api/completion"
    logging(source_text, target_language, api_key, prompt)
    # Construct the translation prompt
    if prompt:
        translation_prompt = f"{prompt}: {source_text}"
    else:
        translation_prompt = f"Translate the following text from original language to [{target_language}] while conveying the appropriate emotional tone. Use emotion tags to guide the tone of the translated speech. Text to be translated:[{source_text}]"



    payload = {
        "model": model,
        "messages": [{"role": "user", "content": translation_prompt}],
        "stream": False
    }

    try:
        start_time = time.time()
        response = requests.post(ollama_url, json=payload)  # Make the request

        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            logger.debug(f"Received status code 200. Elapsed time for API call: {elapsed_time} seconds")

            response_data = response.json()
            #print(response_data)
            translated_text = response_data['message']['content'] if len(response_data) > 0 else None

            if translated_text is not None:
                logger.debug(f"Text translated successfully. Translation: {translated_text}")

                # Remove subtext
                translated_text = re.sub(pattern, '', translated_text)
                return translated_text

        else:
            error_message = f"Failed to translate text. HTTP Status Code: {response.status_code}"
            logger.warning(error_message)

    except Exception as e:
        logger.critical(f"An error occurred while attempting to contact the Ollama service: {e}")
        return None
    
    return None 

def openai_translate_text(source_text, target_language, api_key, prompt=None):    
    logging(source_text, target_language, api_key, prompt=None)
    try:
        # Initialize the OpenAI client with your organization and API key
        client = OpenAI(api_key=api_key)

        # Construct the translation prompt
        if prompt:
            translation_prompt = f"{prompt}: {source_text}"
        else:
            translation_prompt = f"Translate the following text from original language to [{target_language}] while conveying the appropriate emotional tone. Use emotion tags to guide the tone of the translated speech. Text to be translated:[{source_text}]"


        # Make the API call using the client
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Specify the model you're using for translation

            messages=[
                {"role": "system", "content": "You are  a highly intelligent translator."},
                {"role": "user", "content": translation_prompt}
            ],
            temperature=0.9
        )

        # Extract and return the translated text from the response
        translated_text = response.choices[0].message.content.strip() if response.choices else None
       
        return translated_text
    except Exception as e:
        logger.error(f"Error translating text with OpenAI: {e}")
        return None



def mistralai_translate_text(source_text, target_language, api_key, prompt=None):
    logging(source_text, target_language, api_key, prompt=None)
    try:
        model = "mistral-large-latest"
        client = MistralClient(api_key=api_key)
        
        if prompt:
            translation_prompt = f"{prompt}: {source_text}"
        else:
            translation_prompt = f"Translate the following text from original language to [{target_language}] while conveying the appropriate emotional tone. Use emotion tags to guide the tone of the translated speech. Text to be translated:[{source_text}]"


        messages = [
                ChatMessage(role="user", content=source_text)
        ]

        # No streaming
        chat_response = client.chat(
            model=model,
            messages=messages,
        ) 
       
        translated_text = chat_response.choices[0].message.content

        return translated_text
    except Exception as e:
        logger.error(f"Error translating text with MistralAI: {e}")       
        return None


translators_func= {
    "openai_translate_text": openai_translate_text,
    "translate_text_with_ollama": translate_text_with_ollama,
    "mistralai_translate_text": mistralai_translate_text
}

def translate_api(text, target_language, api_key, translation_function, prompt=None, text_portions=230):
    translated_text_parts = []
    current_part_tokens = 0
    current_part = []
    source_sentences = sent_tokenize(text)

    for sentence in source_sentences:
        current_part.append(sentence)
        current_part_tokens += count_tokens(sentence)

        if current_part_tokens > text_portions:
            translated_part = translation_function(' '.join(current_part), target_language, api_key, prompt)
            if translated_part:
                translated_text_parts.append(translated_part)
            else:
                return None

            current_part = [sentence]
            current_part_tokens = count_tokens(sentence)

    if current_part:
        translated_part = translation_function(' '.join(current_part), target_language, api_key, prompt)
        if translated_part:
            translated_text_parts.append(translated_part)

    translated_text = '\n'.join(translated_text_parts)
    return translated_text

def translate_text(source_text, target_language, translators, prompt=None, audio_path=None):
    translated_text = None
    for translator_name, translator_info in translators.items():
        translation_function = translator_info['function']
        api_key = translator_info.get("api_key")
        logger.debug(f"translation_function: {translation_function}")
        translation_function  = translators_func[translation_function]
        logger.debug(f"translators_func: {translation_function}")
        

        try:
            translated_text = translate_api(source_text, target_language, api_key, translation_function, prompt)
        except Exception as e:
            logger.critical(f"An error occurred while translating using {translator_info['name']}: {str(e)}.")
            continue

        if translated_text:
            break

    if not translated_text:
        logger.error("All translation attempts failed.")
        return None

    # Save translated text to file if audio_path is provided
    if audio_path is not None:
        absolute_audio_path = os.path.abspath(audio_path)
        text_filename = os.path.splitext(absolute_audio_path)[0] + f" {target_language}.txt"
        with open(text_filename, "w", encoding="utf-8") as text_file:
            text_file.write(translated_text)
        logger.info(f"Translated text saved to file: {text_filename}")

    logger.info(f"Translated: {translated_text}")
    return translated_text

def logging(source_text, target_language, api_key, prompt=None):
    logger.info(f"[Function]: {__name__}: Starting call with these inputs:")
    logger.info(f"source_text: [{source_text}]")
    logger.info(f"target_language: [{target_language}]")
    logger.info(f"api_key: [{api_key}]")

    if prompt is not None:
        logger.info(f"prompt: [{prompt}]")


# Example usage
if __name__ == "__main__":

    from utils.AudioVideoTranslator import translators
    source_text = "This is a test sentence."
    target_language = "French"
    api_key = "your_openai_api_key"  # Ensure you replace this with your actual API key
    translated_text = translate_text(source_text, target_language, translators )
    
    if translated_text:
        print(f"Translated text: {translated_text}")
    else:
        print("Translation failed.")