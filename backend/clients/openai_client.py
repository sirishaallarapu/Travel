from openai import OpenAI
import os

# This assumes your API key is in the environment variable OPENAI_API_KEY
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # or load from settings if needed
)
