# test_gemini_connection.py
# -*- coding: utf-8 -*-

import vertexai
from vertexai.generative_models import GenerativeModel

def test_gemini_pro():
    # Specify the Project ID and the primary region where Gemini is available
    PROJECT_ID = "openclaw-sandbox-env"
    LOCATION = "us-central1"

    print(f"Initializing Vertex AI (Project: {PROJECT_ID}, Location: {LOCATION})...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Instantiate the correct Gemini model (Updated to gemini-2.5-pro based on GCP availability)
    MODEL_ID = "gemini-2.5-pro"
    print(f"Loading Model: {MODEL_ID} ...")
    model = GenerativeModel(MODEL_ID)

    # Prompt for the connection test
    prompt = "Hello. Please reply with exactly one sentence confirming your model version."
    print(f"Sending prompt: '{prompt}'")

    try:
        response = model.generate_content(prompt)
        print("\n[SUCCESS] Connection Established!")
        print(f"Response from AI: {response.text}")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to {MODEL_ID}. Details:")
        print(e)

if __name__ == "__main__":
    test_gemini_pro()