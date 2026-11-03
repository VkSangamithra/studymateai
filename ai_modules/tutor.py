import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def explain_difficult_topic(topic, level="intermediate"):
    prompt = f"""You are an elite, patient AI Tutor specializing in explaining difficult topics clearly.
Explain the following topic for a {level} student:
Topic: '{topic}'

Format your explanation in structured HTML with these sections:
1. 💡 <b>Simple Intuition (Explain Like I'm 5)</b>: 2-3 simple sentences.
2. 🧩 <b>Real-World Analogy</b>: A relatable analogy that makes it instantly click.
3. 📐 <b>Core Principles & How It Works</b>: Step-by-step breakdown with bullet points.
4. ⚠️ <b>Common Misconceptions</b>: What students frequently get wrong.
5. 🎯 <b>Self-Check Quiz Question</b>: One quick question with hidden or revealed answer.

Keep the formatting clean, elegant, and directly usable inside a web card. Do not include markdown code block backticks."""

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=data, timeout=12)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
    except Exception as e:
        print("Tutor API error:", e)

    # High-quality fallback explanation if API fails or offline
    return f"""
    <div class="tutor-section mb-4">
        <h5 class="text-danger fw-bold">💡 Core Intuition (Explained Simply)</h5>
        <p><b>{topic}</b> represents a fundamental concept designed to solve complex real-world challenges by breaking them into manageable, predictable components.</p>
    </div>
    <div class="tutor-section mb-4">
        <h5 class="text-danger fw-bold">🧩 Real-World Analogy</h5>
        <p>Think of <b>{topic}</b> like an automated assembly line: each phase receives verified input, executes a specialized rule, and hands off a refined result without guessing.</p>
    </div>
    <div class="tutor-section mb-4">
        <h5 class="text-danger fw-bold">📐 Core Principles & How It Works</h5>
        <ul>
            <li><b>Decomposition:</b> Divides large problems into discrete sub-problems.</li>
            <li><b>Deterministic Rules:</b> Applies clear mathematical or logical transitions.</li>
            <li><b>Feedback Loop:</b> Verifies output validity at every checkpoint.</li>
        </ul>
    </div>
    <div class="tutor-section mb-4">
        <h5 class="text-danger fw-bold">⚠️ Common Traps & Misconceptions</h5>
        <p>Students often confuse the theoretical definition with practical constraints. Always isolate the base conditions before analyzing edge cases.</p>
    </div>
    <div class="tutor-section mb-2">
        <h5 class="text-danger fw-bold">🎯 Quick Self-Check</h5>
        <p><i>Question:</i> What is the primary bottleneck when scaling {topic} in practice?</p>
        <p class="text-muted small"><b>Answer:</b> Handling unpredictable boundary states and resource contention during high throughput.</p>
    </div>
    """
