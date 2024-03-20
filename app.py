from fastapi import FastAPI, UploadFile, File, HTTPException
#import CORS middleware
from fastapi.middleware.cors import CORSMiddleware
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
import boto3
from botocore.exceptions import NoCredentialsError
import shutil

# Load environment variables
dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
s3_client = boto3.client('s3')


# Set your Stripe API key
#stripe.api_key = 'your_stripe_api_key'TODO Set up stripe api
#add CORS to the app


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3040",
    "http://localhost:3000",
    "https://maumasi.github.io/image-ai-response-mobile/",
    "https://image-ai-staging-86b1efe5762c.herokuapp.com/upload",
    "http://164.90.147.123/upload",
    "http://164.90.147.123",
    "https://soldai4.onrender.com",
    "https://sold-ai.com",
    "https://api.soldai.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
handler = Mangum(app)
# Mount a static directory to serve temporary images
app.mount("/temp_images", StaticFiles(directory="temp_images"), name="temp_images")

# Function to save image temporarily and return its URL
s3_client = boto3.client('s3')

async def save_temp_image_to_s3(file: UploadFile, bucket_name="soldai") -> str:
    try:
        # Generate a unique file name
        timestamp = str(time.time()).replace('.', '')[:10]
        unique_id = uuid.uuid4().hex[:6]
        extension = os.path.splitext(file.filename)[1]
        s3_file_name = f"{timestamp}_{unique_id}{extension}"

        # Read the file contents
        contents = await file.read()

        # Upload the file to S3
        s3_client.put_object(Body=contents, Bucket=bucket_name, Key=s3_file_name)#ACL='public-read'

        # Construct the S3 URL
        location = s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        if location is None:
            location = 'us-east-1'  # Default to us-east-1 if no location is returned
        s3_url = f"https://soldai.s3.{location}.amazonaws.com/{s3_file_name}"

        return s3_url

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))

#save files to localhost
async def save_temp_image(file: UploadFile) -> str:
    try:
        # Generate a unique file name
        timestamp = str(time.time()).replace('.', '')[:10]
        unique_id = uuid.uuid4().hex[:6]
        extension = os.path.splitext(file.filename)[1]
        file_name = f"{timestamp}_{unique_id}{extension}"

        # Save the file to the temp_images directory
        with open(f"temp_images/{file_name}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"http://localhost:8000/temp_images/{file_name}"
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
    prompt = '''Create a flowery desciption of the property shown in the images.'''
    image_urls = [await save_temp_image_to_s3(file) for file in files]
    #try:
    response = await query_gpt4_vision(image_urls, context, prompt)
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

#def query_stripe(email):
#    try:
#        # Query orders by email
#        orders = stripe.Order.list(email=email)
#
#        # Check if any orders exist
#        if not orders or len(orders.data) == 0:
#            return False
#
#        for order in orders.data:
#            # Extract order date and amount
#            order_date = datetime.fromtimestamp(order.created)
#            amount = order.amount  # Assuming amount is in cents
#
#            # Determine the time frame to check based on the amount
#            if amount == 1000:  # $10
#                time_frame = timedelta(days=30)
#            elif amount == 6000:  # $60
#                time_frame = timedelta(days=180)
#            elif amount == 12000:  # $120
#                time_frame = timedelta(days=365)
#            else:
#                continue  # Skip if amount does not match any criteria
#
#            # Check if the order is within the specified time frame
#            if datetime.now() - order_date < time_frame:
#                return True
#
#        # If no matching orders are found
#        return False
#
#    except Exception as e:
#        print(f"An error occurred: {e}")
#        return False
    
#and endpoint that takes an image url and returns a description
#@app.post("/generate-description/")
#async def generate_description(image_url: str, context: str = ""):
#    #try:
#    prompt = '''
#    Describe the items in the image. Provide as much detail as possible, including condition.
#    Using Auction Market Theory, estimate a buy price and a sell price for each item.
#    Inlclude whether the item is in demand or not, and any other relevant information.
#    Do not explain Auction Market Theory, just provide the prices.
#'''
#    full_prompt = f"{prompt}\n{context}"
#    response = await query_gpt4_vision([image_url], full_prompt)
#    #except Exception as e:
#    #    raise HTTPException(status_code=500, detail=str(e))
#
#    return {"response": response}
@app.post("/generate-description/")
async def generate_description(file: UploadFile = File(...), context: str = ""):
    # Save the uploaded image to S3 and get its URL
    temp_image_url = await save_temp_image_to_s3(file)
    
    # Use the S3 URL for GPT analysis as before
    prompt = '''
    Describe the items in the image. Provide as much detail as possible, including condition.
    '''
    full_prompt = f"{prompt}\n{context}"
    
    try:
        response = await query_gpt4_vision([temp_image_url], full_prompt)
    finally:
        # Optionally delete the image from S3 after analysis if it's no longer needed
        pass  # Implement S3 deletion logic here if needed

    return {"response": response}

#to run the app use uvicorn main:app --reload
#to run the app with tracing use uvicorn main:app --reload --log-level trace
#to run the app on a specific ip and port use uvicorn main:app --reload --host localhost --port 8000
#to run the app on a specific ip and port use uvicorn main:app --reload --host 0.0.0.0 --port 8000

math_with_multimedia_prompt = '''
Competency: Math With Multimedia Inputs (Text + Images)

Instructions: Multimedia reasoning

Description

Design tasks for the AI Assistant that test the ability to perform math with multimedia inputs.

How to design a task

First, you will need to source a suitable kind of image, which could be one that you already have access to, or based on a web search. Please choose images which convey information that you understand so that you can accurately assess how well the AI Assistant deals with your input. Please also try to choose images that you think users might plausibly have questions about if they did not have the same level of understanding as yourself. Please upload high resolution images only.

Once you have a suitable image, upload it (see detailed instructions in the task itself for more info), and create a suitable question, request or instruction for the AI Assistant. There are many different kinds of questions people might want an AI Assistant to answer. We give some general suggestions of types of task here, but please use your creativity to come up with as many as you can:

Answering math questions using a diagram, figure or graph (algebra, calculus, geometry, topology, set theory, tables)
Finding errors in an image containing equations of mathematical reasoning
Make statistical estimates of a quantity in an image using mathematical reasoning and approximations -Evaluate graphical proofs

Create a prompt based on the image to test the ability of an LLM to do math
'''
@app.post("/math-with-multimedia/")
async def math_with_multimedia(files: List[UploadFile] = File(...), context: str = ""):
    prompt = math_with_multimedia_prompt

    image_urls = [await save_temp_image_to_s3(file) for file in files]
    #image_urls = [await save_temp_image(file) for file in files]
    response = await query_gpt4_vision(image_urls, context=prompt, prompt=prompt)

    return {"response": response}