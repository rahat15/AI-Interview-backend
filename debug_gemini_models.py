import google.generativeai as genai
import os
from core.config import settings

print(f"Checking API Key: {settings.gemini_api_key[:5]}... (Length: {len(settings.gemini_api_key)})")
genai.configure(api_key=settings.gemini_api_key)

print("\n--- Listing Available Models ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\n--- Testing Generation with 'gemini-1.5-flash' ---")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with gemini-1.5-flash: {e}")

print("\n--- Testing Generation with 'gemini-pro' ---")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with gemini-pro: {e}")
