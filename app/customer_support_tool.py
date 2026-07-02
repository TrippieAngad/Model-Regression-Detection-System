import json
import os
import yaml as y
from pathlib import Path
from dotenv import load_dotenv
from google import genai as gemini

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
client = gemini.Client(api_key =GEMINI_KEY )


def email_classifier(email:str)-> json:
    BASE_DIR = Path(__file__).resolve().parent.parent
    PROMPT_PATH = BASE_DIR / "prompts" / "email_classifier_v1.yaml"

    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        prompt_config = y.safe_load(file) # stores a dict
    
    prompt_to_send = prompt_config["prompt"] 
    model_to_use = prompt_config["model_used"]
    
    response = client.models.generate_content(model = model_to_use, contents = f"prompt: {prompt_to_send}. Email instance to use: {email}")
    return response.text


print(email_classifier("I was charged twice for my subscription."))


