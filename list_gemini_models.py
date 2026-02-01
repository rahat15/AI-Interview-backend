"""
List all available Gemini models
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("=" * 80)
print("Available Gemini Models")
print("=" * 80)

# List all models
models = genai.list_models()

print(f"\nTotal models found: {len(list(models))}\n")

# Re-list to iterate (generator can only be consumed once)
for model in genai.list_models():
    print(f"📦 Model: {model.name}")
    print(f"   Display Name: {model.display_name}")
    print(f"   Description: {model.description}")
    print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
    
    # Check if supports generateContent
    if 'generateContent' in model.supported_generation_methods:
        print(f"   ✅ Supports generateContent (Can be used for interviews)")
    else:
        print(f"   ❌ Does NOT support generateContent")
    
    print()

print("=" * 80)
print("\n🎯 Recommended Models for Interview System:")
print("-" * 80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        # Filter for commonly used models
        if 'flash' in model.name.lower() or 'pro' in model.name.lower():
            model_id = model.name.replace('models/', '')
            print(f"  • {model_id}")
            print(f"    Display: {model.display_name}")
            print(f"    Description: {model.description[:100]}...")
            print()

print("=" * 80)
