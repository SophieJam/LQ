import openai
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

def generate_ai_response(user_input, quote="",author_name=""):
    messages = [
        {"role": "system", "content": f"Discuss the following quote in Japanese: 「{quote}」. The author of the quote is: {author_name}.Keep responses concise."},
        {"role": "user", "content": user_input}
    ]
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content.strip()

def generate_ai_feedback(user_input, quote="",author_name=""):
    messages = [
        {"role": "system", "content": f"The original quote is '{quote}'.The author of the quote is: {author_name}. The user customized this, so provide concise feedback in japanese. Provide examples to improve it as well"},
        {"role": "user", "content": user_input}
    ]
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content.strip()

def generate_image_prompt(quote="",author_name=""):
    messages = [
        {"role": "system", "content": f"You are an excellent prompt engineer. Create a prompt for generating an image based on a '{quote}' and its author '{author_name}'.Keep responses concise and under 200 words. You can make clear message for Japanese."}
    ]
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=100
    )
    return response.choices[0].message.content.strip()

def generate_image(prompt):
    response = client.images.generate(
        prompt=prompt,  
        n=1,
        size="256x256"  
    )
    image_url = response.data[0].url 
    return image_url