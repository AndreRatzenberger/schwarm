"""Text function implementations."""

from typing import Optional

from ..context.context import Context
from .function import Function
from ..providers.simple_llm_provider import SimpleLLMProvider


async def summarize_text(
    context: Context,
    text: str,
    max_length: Optional[int] = None
) -> str:
    """Summarize the given text using an LLM provider.
    
    Args:
        context: The shared context object
        text: The text to summarize
        max_length: Optional target length for the summary
        
    Returns:
        A summary of the input text
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    # Get the LLM provider from context
    provider = context.get("llm_provider")
    if not isinstance(provider, SimpleLLMProvider):
        raise ValueError("LLM provider not found in context")
        
    # Construct the prompt
    prompt = f"Please summarize the following text"
    if max_length:
        prompt += f" in approximately {max_length} words"
    prompt += f":\n\n{text}"
    
    # Use the provider to generate the summary
    system_message = (
        "You are a helpful assistant specialized in creating clear and "
        "concise summaries while preserving the key information."
    )
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message
    )


# Create the function instance
summarize_function = Function(
    name="summarize",
    implementation=summarize_text,
    description="Summarizes text using an LLM provider"
)


async def translate_text(
    context: Context,
    text: str,
    target_language: str,
    source_language: Optional[str] = None
) -> str:
    """Translate the given text to the target language using an LLM provider.
    
    Args:
        context: The shared context object
        text: The text to translate
        target_language: The language to translate the text into
        source_language: Optional source language of the text
        
    Returns:
        Translated text
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    provider = context.get("llm_provider")
    if not isinstance(provider, SimpleLLMProvider):
        raise ValueError("LLM provider not found in context")
        
    prompt = f"Translate the following text into {target_language}"
    if source_language:
        prompt += f" from {source_language}"
    prompt += f":\n\n{text}"
    
    system_message = "You are a skilled multilingual assistant capable of accurate translations."
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message
    )

translate_function = Function(
    name="translate",
    implementation=translate_text,
    description="Translates text to a specified language using an LLM provider"
)



async def generate_text(
    context: Context,
    prompt: str,
    max_length: Optional[int] = 100
) -> str:
    """Generate creative or informative text based on a prompt.
    
    Args:
        context: The shared context object
        prompt: The input prompt to guide text generation
        max_length: Maximum length of the generated text
        
    Returns:
        Generated text
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    provider = context.get("llm_provider")
    if not isinstance(provider, SimpleLLMProvider):
        raise ValueError("LLM provider not found in context")
        
    system_message = (
        "You are a creative and knowledgeable assistant capable of generating engaging and "
        "informative text based on prompts."
    )
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message,
        max_length=max_length
    )

generate_function = Function(
    name="generate",
    implementation=generate_text,
    description="Generates text based on a given prompt using an LLM provider"
)


async def extract_information(
    context: Context,
    text: str,
    query: str
) -> str:
    """Extract specific information from the provided text.
    
    Args:
        context: The shared context object
        text: The text to analyze
        query: The specific information to extract
        
    Returns:
        Extracted information
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    provider = context.get("llm_provider")
    if not isinstance(provider, SimpleLLMProvider):
        raise ValueError("LLM provider not found in context")
        
    prompt = f"From the following text, extract information about {query}:\n\n{text}"
    
    system_message = "You are an analytical assistant capable of extracting precise information based on queries."
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message
    )

extract_function = Function(
    name="extract_information",
    implementation=extract_information,
    description="Extracts specific information from text based on a query using an LLM provider"
)


async def rewrite_text(
    context: Context,
    text: str,
    tone: Optional[str] = None,
    target_audience: Optional[str] = None
) -> str:
    """Rewrite the given text with a specified tone and/or for a target audience.
    
    Args:
        context: The shared context object
        text: The text to rewrite
        tone: Optional tone for the rewritten text (e.g., formal, casual)
        target_audience: Optional audience for the rewritten text
        
    Returns:
        Rewritten text
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    provider = context.get("llm_provider")
    if not isinstance(provider, SimpleLLMProvider):
        raise ValueError("LLM provider not found in context")
        
    prompt = "Rewrite the following text"
    if tone:
        prompt += f" in a {tone} tone"
    if target_audience:
        prompt += f" for a {target_audience} audience"
    prompt += f":\n\n{text}"
    
    system_message = "You are a skilled writer capable of rewriting text with clarity, style, and appropriate tone."
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message
    )

rewrite_function = Function(
    name="rewrite",
    implementation=rewrite_text,
    description="Rewrites text with a specified tone and/or for a target audience using an LLM provider"
)


async def analyze_sentiment(
    context: Context,
    text: str
) -> str:
    """Analyze the sentiment of the given text.
    
    Args:
        context: The shared context object
        text: The text to analyze
        
    Returns:
        Sentiment analysis result (e.g., Positive, Negative, Neutral)
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    provider = context.get("llm_provider")
    if not isinstance(provider, SimpleLLMProvider):
        raise ValueError("LLM provider not found in context")
        
    prompt = f"Analyze the sentiment of the following text and provide a concise summary:\n\n{text}"
    
    system_message = "You are a sentiment analysis expert capable of identifying emotional tones in text."
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message
    )

sentiment_function = Function(
    name="analyze_sentiment",
    implementation=analyze_sentiment,
    description="Analyzes the sentiment of text using an LLM provider"
)


async def levenshtein_distance(
    context: Context,
    string1: str,
    string2: str
) -> int:
    """Calculate the Levenshtein distance between two strings.
    
    Args:
        context: The shared context object (not used in this function)
        string1: The first string
        string2: The second string
        
    Returns:
        The Levenshtein distance as an integer
    """
    len1, len2 = len(string1), len(string2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        for j in range(len2 + 1):
            if i == 0:
                dp[i][j] = j
            elif j == 0:
                dp[i][j] = i
            elif string1[i - 1] == string2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    
    return dp[len1][len2]

levenshtein_function = Function(
    name="levenshtein_distance",
    implementation=levenshtein_distance,
    description="Calculates the Levenshtein distance between two strings without any AI involvement"
)

async def find_longest_word(
    context: Context,
    text: str
) -> str:
    """Find the longest word in the given text.
    
    Args:
        context: The shared context object (not used in this function)
        text: The text to analyze
        
    Returns:
        The longest word in the text
    """
    words = text.split()
    return max(words, key=len) if words else ""

longest_word_function = Function(
    name="find_longest_word",
    implementation=find_longest_word,
    description="Finds the longest word in a text without any AI involvement"
)

async def is_palindrome(
    context: Context,
    text: str
) -> bool:
    """Check if the given string is a palindrome.
    
    Args:
        context: The shared context object (not used in this function)
        text: The string to check
        
    Returns:
        True if the string is a palindrome, False otherwise
    """
    normalized_text = ''.join(char.lower() for char in text if char.isalnum())
    return normalized_text == normalized_text[::-1]

palindrome_function = Function(
    name="is_palindrome",
    implementation=is_palindrome,
    description="Checks if a string is a palindrome without any AI involvement"
)

async def count_words(
    context: Context,
    text: str
) -> int:
    """Count the number of words in the given text.
    
    Args:
        context: The shared context object (not used in this function)
        text: The text to analyze
        
    Returns:
        The word count as an integer
    """
    return len(text.split())

count_words_function = Function(
    name="count_words",
    implementation=count_words,
    description="Counts the number of words in a text without any AI involvement"
)


async def reverse_string(
    context: Context,
    text: str
) -> str:
    """Reverse the given string.
    
    Args:
        context: The shared context object (not used in this function)
        text: The string to reverse
        
    Returns:
        The reversed string
    """
    return text[::-1]

reverse_string_function = Function(
    name="reverse_string",
    implementation=reverse_string,
    description="Reverses a string without any AI involvement"
)
