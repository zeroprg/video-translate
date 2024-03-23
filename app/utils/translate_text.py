# translate.py
import os
import time
import requests
from openai import OpenAI
from mistralai.client import MistralClient
import re
from mistralai.models.chat_completion import ChatMessage
from .tokenizer_limiter import read_approx_tokens, sent_tokenize, count_tokens

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) #Set log level if needed

def translate_text_with_ollama(source_text, target_language, api_key = None, prompt = None):
    """
    Translates a given text using the Mistral model from Ollama.

    Args:
        text_to_translate (str): The input text to be translated
        target_language (str): The target language for translation

    Returns:
        str: The translated text or None if an error occurs.
    """

    ollama_url = "http://localhost:11434/api/chat"  # Replace this URL with the actual Ollama instance's URL
    logging(source_text, target_language, api_key, prompt)
    # Construct the translation prompt
    if prompt:
        translation_prompt = f"{prompt}: {source_text}"
    else:
        translation_prompt = f"Translate the following text to {target_language}: {source_text} . Return only translated text"

    payload = {
        "model": "llama2",
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
                return translated_text

        else:
            error_message = f"Failed to translate text. HTTP Status Code: {response.status_code}"
            logger.warning(error_message)

    except Exception as e:
        logger.critical(f"An error occurred while attempting to contact the Ollama service: {e}")
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
            translation_prompt = f"Translate the following text to {target_language}: {source_text}"


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
        logger.info(f"Translated: {translated_text}")

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
            source_text = f"{prompt}: {source_text}"
        else:
            source_text = f"Left the SRT (SubRip Subtitle) file format unchangable translate following text to {target_language}: {source_text}"

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

def translate_api(text, target_language, api_key, translation_function, prompt=None,TEXT_PORTIONS =  230 ):

    translated_text_parts = []
    current_part_tokens = 0
    current_part = []
    
    # Split the source text into sentences
    source_sentences = sent_tokenize(text)  # Splitting source text into sentences
    
    for sentence in source_sentences:
        # Add the sentence to the current part
        current_part.append(sentence)

        # Count the tokens in the current part
        current_part_tokens += count_tokens(sentence)

        # If adding this sentence would exceed the desired number of tokens, translate the current part
        if current_part_tokens > TEXT_PORTIONS:
            # Translate the current part using the specified translation function
                        
            translated_part = translation_function(' '.join(current_part), target_language, api_key, prompt)

            # Append the translated part to the list if it's not None
            if translated_part is not None:
                translated_text_parts.append(translated_part)
            else:
                return None

            # Reset the current part and token count
            current_part = [sentence]
            current_part_tokens = count_tokens(sentence)

    # Translate the last part if it exists
    if current_part:
        # Translate the current part using the specified translation function
        translated_part = translation_function(' '.join(current_part), target_language, api_key, prompt)

        # Append the translated part to the list if it's not None
        if translated_part is not None:
            translated_text_parts.append(translated_part)

    # Combine the translated parts into the final translated text
    translated_text = '\n'.join(translated_text_parts)
    return translated_text


def translate_text(source_text, target_language, translators, prompt=None, audio_path=None):
    translated_text = None
     # Check if a corresponding text file already exists
    if audio_path is not None:
        # Convert to absolute path
        absolute_audio_path = os.path.abspath(audio_path)
        text_filename = os.path.splitext(absolute_audio_path)[0] + f" {target_language}.txt"
        if os.path.exists(text_filename):
            # If the text file exists, read its content and return it
            with open(text_filename, "r", encoding="utf-8") as text_file:
                translated_text = text_file.read()
            logger.info(f"Translated text loaded from file: {text_filename}")
            return translated_text

    preper_to_delete = []        

    for index, translator in enumerate(translators.values()):
        logger.debug(f"translator : {translator}")
        if "available" not in translator or not translator["available"]:
            continue

        api_key = translator.get("api_key")
        translation_function = translator['function']
        logger.debug(f"translation_function: {translation_function}")
        logger.debug(f"translators_func: {translators_func[translation_function]}")
        translation_function  = translators_func[translation_function]

        try:
            translated_text = translate_api(source_text, target_language, api_key, translation_function, prompt)
        except Exception as e:
            logger.warning(f"An error occurred while translating using {translator['name']}:{str(e)}.")
            logger.info(f"Skipping the current translator, trying the next one...")
                        # Remove translator record if error occurs
            preper_to_delete.append(index)
            continue

        if translated_text is None or len(translated_text.strip()) == 0:  # Check if translation result is empty
            logger.warning("Translation returned an empty result from the used translator.")  # Log a warning message in case of empty results
            preper_to_delete.append(index)
            continue
 
        break   # Include 'break' statement outside the try block for successful translations without errors or empty results
    try:
        for delet_it_index in  preper_to_delete:
            del translators[delet_it_index]
    except Exception as e:
        logger.warning(f"An error occurred while translating using {translator['name']}:{str(e)}.")
        return None

    # Save translated text to file if audio_path is provided
    if audio_path is not None and translated_text is not None:
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
    source_text = "This is a test sentence."
    target_language = "French"
    api_key = "your_openai_api_key"  # Ensure you replace this with your actual API key
    translated_text = openai_translate_text(source_text, target_language, api_key)
    if translated_text:
        print(f"Translated text: {translated_text}")
    else:
        print("Translation failed.")