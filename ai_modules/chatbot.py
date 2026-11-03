import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def chatbot_response(user_message):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {

        "Authorization": f"Bearer {API_KEY}",

        "Content-Type": "application/json"

    }

    data = {

        "model": "openai/gpt-3.5-turbo",

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

        json=data

    )

    result = response.json()

    return result['choices'][0]['message']['content']
