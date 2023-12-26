import os
import requests
import chainlit as cl
import logging
from chainlit import user_session
from chainlit.input_widget import Select
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to help with debugging
logging.basicConfig(level=logging.DEBUG)

# Retrieve API key from environment and set up the API endpoint
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_ENDPOINT = 'https://api.perplexity.ai/chat/completions'

# Set up the headers for the HTTP requests to the API
headers = {
    'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
    'Content-Type': 'application/json'
}

# Function called at the start of the chat, setting up chat settings
@cl.on_chat_start
async def start():
    # Display chat settings for model selection
    await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Select Model",
                values=[
                    "pplx-70b-online",
                    "pplx-70b-chat",
                    "pplx-7b-chat",
                    "codellama-34b-instruct",
                    "mixtral-8x7b-instruct"
                ],
                initial_index=0
            )
        ]
    ).send()

    # Initialize the user session with default values
    user_session.set('conversation_state', [])
    user_session.set('current_model', 'pplx-70b-online')

    # Set up the chatbot avatar
    await cl.Avatar(
        name="perplexed",
        url="https://pbs.twimg.com/profile_images/1715563899502608385/NB3G6tx3_400x400.jpg"
    ).send()

# Function to handle updates to chat settings (like model changes)
@cl.on_settings_update
async def setup_agent(settings):
    # Update the current model in the user session
    new_model = settings['Model']
    user_session.set('current_model', new_model)
    logging.debug(f"Model updated to: {new_model}")

    # Clear the conversation state to ensure the new model is used
    user_session.set('conversation_state', [])

# Function to handle incoming messages from the user
@cl.on_message
async def perplexity_chat(message: cl.Message):
    # Retrieve the current state of the conversation
    conversation_state = user_session.get('conversation_state', [])
    current_model = user_session.get('current_model', 'pplx-70b-online')

    # Display a loader while processing the message
    loader_message = cl.Message(content="")
    await loader_message.send()

    # Append the user's message to the conversation state
    conversation_state.append({'role': 'user', 'content': message.content})

    # Create the data payload for the API request
    data = {
        'model': current_model,
        'messages': conversation_state,
        'config': {'stop_sequence': None}
    }

    # Make a post request to the Perplexity API
    response = requests.post(PERPLEXITY_API_ENDPOINT, headers=headers, json=data)

    # If the response is successful, process and display it
    if response.status_code == 200:
        model_message = response.json()['choices'][0]['message']['content']
        conversation_state.append({'role': 'system', 'content': model_message})
        user_session.set('conversation_state', conversation_state)

        # Update the loader message with the actual content
        loader_message.content = model_message
        await loader_message.update()
    else:
        # If there's an error, log it and update the message to show the error
        logging.error(f'Error: {response.status_code}, {response.text}')
        loader_message.content = "An error occurred."
        await loader_message.update()

# Run the chatbot application
if __name__ == '__main__':
    cl.run()
