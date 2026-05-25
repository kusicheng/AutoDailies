import requests
import json
import os


def call_gemini_connections(words: list[str]) -> dict:
    """
    call gemini 2.5 flash via Openrouter to solve the Connections puzzle.
    
    Args: 
      words: list of up to 16 words and at least 8 words from the Connections game
        
    Returns:
      dict: the model's response parsed as JSON
    """
    #read the prompt template from connections.txt
    prompt_path = os.path.join(os.path.dirname(__file__), "api", "connections.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    #format words in the same way connections_extractor prints them
    words_formatted = "\n".join(f"[{i+1}] {word}" for i, word in enumerate(words))
    
    #combine prompt template with the words
    full_prompt = f"{prompt_template}\n\n{words_formatted}"
    
    #get API key from environment variable
    api_key = r"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"
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        })
    )
    
    response.raise_for_status()
    result = response.json()
    
    #extract the content from the response
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    #try to parse the content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Return raw content if not valid JSON
        return {"raw_response": content}


def call_gemini_wordle(feedback: str) -> dict:
    """
    Call Gemini 2.5 Flash via OpenRouter to suggest the next Wordle guess.
    
    Args:
        feedback: String containing previous guesses and their feedback
        
    Returns:
        dict: The model's response parsed as JSON with suggested_word
    """
    # Read the prompt template from wordle.txt
    prompt_path = os.path.join(os.path.dirname(__file__), "api", "wordle.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Combine prompt template with the feedback
    full_prompt = f"{prompt_template}\n{feedback}"
    
    # Get API key from environment variable
    api_key = r"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"
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        })
    )
    
    response.raise_for_status()
    result = response.json()
    
    # Extract the content from the response
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Try to parse the content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Return raw content if not valid JSON
        return {"raw_response": content}


if __name__ == "__main__":
    #test with sample words
    test_words = [
        "Croc", "Loafer", "Moccasin", "Slipper",
        "Witness", "Arms", "Fruit", "Hug",
        "Python", "Boa", "Cobra", "Moccasin",
        "Monitor", "Survey", "Track", "Watch"
    ]
    
    result = call_gemini_connections(test_words)
    print(json.dumps(result, indent=2))
