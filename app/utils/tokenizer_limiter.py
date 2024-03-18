import re

def count_tokens(text):
    # Define the regular expression pattern to match words
    pattern = r'\b\w+\b'

    # Find all words in the text using the regular expression pattern
    words = re.findall(pattern, text)

    # Count the number of words
    num_tokens = len(words)

    return num_tokens

def sent_tokenize(text):
    # Define the regular expression pattern to match sentence boundaries
    pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'

    # Split the text using the regular expression pattern
    sentences = re.split(pattern, text)

    return sentences

def read_approx_tokens(text, num_tokens):
    """
    Read approximately num_tokens from the text without cutting it in the middle of a sentence.
    """
    # Split the text into words based on whitespace characters and punctuation
    words = re.findall(r'\b\w+\b', text)

    # Initialize variables
    tokens_count = 0
    result = []

    # Iterate through words and accumulate tokens until reaching num_tokens
    for word in words:
        tokens_count += 1
        if tokens_count <= num_tokens:
            result.append(word)
        else:
            break

    # Combine the selected words into a string
    selected_text = ' '.join(result)

    return selected_text
