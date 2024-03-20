from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
import mangum
from typing import List
from openai import OpenAI

#from openai.error import RateLimitError, OpenAIError
import os
import dotenv
#from PIL import Image
import io
#import stripe
from datetime import datetime, timedelta
import time
import uuid
import os
from mangum import Mangum
# Load environment variables
dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# Set your Stripe API key
#stripe.api_key = 'your_stripe_api_key'TODO Set up stripe api

app = FastAPI()
handler = Mangum(app)
# Mount a static directory to serve temporary images
app.mount("/temp_images", StaticFiles(directory="temp_images"), name="temp_images")

# Function to save image temporarily and return its URL
async def save_temp_image(file: UploadFile, temp_dir="temp_images") -> str:
    try:
        os.makedirs(temp_dir, exist_ok=True)
        timestamp = str(time.time()).replace('.', '')[:10]
        unique_id = uuid.uuid4().hex[:6]
        extension = os.path.splitext(file.filename)[1]
        new_filename = f"{timestamp}_{unique_id}{extension}"
        temp_file = os.path.join(temp_dir, new_filename)

        with open(temp_file, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)

        return f"http://127.0.0.1:8000/{temp_dir}/{new_filename}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

# Function to send query to GPT-4 Vision API with error handling
async def query_gpt4_vision(image_urls: List[str], context: str, prompt: str = ""):
    #prompt = "Describe each image in as much detail as possbile. If you can't assist with an image, explain why."
    

    #try:
    messages = [{"role": "system", "content": prompt}]

    if context:
        messages.append({"role": "user", "content": context})

    # Add each image to the messages
    for img_url in image_urls:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this image:"},
                {"type": "image_url", "image_url": {"url": img_url}}
            ]
        })

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=4096  # Adjust max_tokens if needed
    )

    # Extract and format the response for each image
    #response_content = [message.content for message in response.choices[0].message if message.role == 'assistant']
    response_content = response.choices[0].message.content.strip()
    #response_content = response

    return response_content

    #except Exception as e:
    #    raise HTTPException(status_code=429, detail=str(e))

# Endpoint to handle image upload and processing
@app.post("/generate-listing/")
async def generate_listing(files: List[UploadFile] = File(...), context: str = ""):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum of 10 images can be uploaded")

    image_urls = [await save_temp_image(file) for file in files]
    #try:
    response = await query_gpt4_vision(image_urls, context)
    #except Exception as e:
    #    print(e)
    #    raise HTTPException(status_code=500, detail=str(e))

    #for img_url in image_urls:
    #    os.remove(img_url.replace(r"http://127.0.0.1:8000/", ""))#TODO change to your url

    return {"response": response}

@app.post("/check_auth/")
def check_auth(email:str):
    is_authenticated = query_stripe("email")
    return {"is_authenticated": is_authenticated}

def query_stripe(email):
    try:
        # Query orders by email
        orders = stripe.Order.list(email=email)

        # Check if any orders exist
        if not orders or len(orders.data) == 0:
            return False

        for order in orders.data:
            # Extract order date and amount
            order_date = datetime.fromtimestamp(order.created)
            amount = order.amount  # Assuming amount is in cents

            # Determine the time frame to check based on the amount
            if amount == 1000:  # $10
                time_frame = timedelta(days=30)
            elif amount == 6000:  # $60
                time_frame = timedelta(days=180)
            elif amount == 12000:  # $120
                time_frame = timedelta(days=365)
            else:
                continue  # Skip if amount does not match any criteria

            # Check if the order is within the specified time frame
            if datetime.now() - order_date < time_frame:
                return True

        # If no matching orders are found
        return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
#and endpoint that takes an image url and returns a description
@app.post("/generate-description/")
async def generate_description(image_url: str, context: str = ""):
    #try:
    prompt = '''
    Describe the items in the image. Provide as much detail as possible, including condition.
    Using Auction Market Theory, estimate a buy price and a sell price for each item.
    Inlclude whether the item is in demand or not, and any other relevant information.
    Do not explain Auction Market Theory, just provide the prices.
'''
    full_prompt = f"{prompt}\n{context}"
    response = await query_gpt4_vision([image_url], full_prompt)
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))

    return {"response": response}


#to run the app use uvicorn main:app --reload
#to run the app with tracing use uvicorn main:app --reload --log-level trace
#to run the app on a specific ip and port use uvicorn main:app --reload --host localhost --port 8000
#to run the app on a specific ip and port use uvicorn main:app --reload --host 0.0.0.0 --port 8000