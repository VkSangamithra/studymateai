import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Ordered list of free, fast, reliable models on OpenRouter
MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free",
    "baidu/ernie-5.5-flash-preview:free",
    "google/gemma-4-26b-a4b-it:free",
    "thinkingmachines/inkling-2-small:free"
]

def chatbot_response(user_message):
    global API_KEY
    if not API_KEY:
        load_dotenv(override=True)
        API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Try available models in order
    for model in MODELS:
        try:
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    message_obj = result["choices"][0].get("message", {})
                    content = message_obj.get("content", "")
                    if content and content.strip():
                        return content.strip()
            else:
                print(f"[chatbot] Model {model} returned status {response.status_code}: {response.text[:120]}")
        except Exception as e:
            print(f"[chatbot] Exception calling {model}: {e}")
            continue

    # Fallback response if all API models fail or offline
    return (
        "I analyzed your question, but the AI service is currently experiencing high load or connectivity issues. "
        "Please verify your internet connection or try asking again in a few moments."
    )
