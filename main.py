import os
import requests
import chainlit as cl
import logging
from chainlit import user_session
from chainlit.input_widget import Select
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# API Key and Endpoint
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_ENDPOINT = 'https://api.perplexity.ai/chat/completions'

headers = {
    'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
    'Content-Type': 'application/json'
}

# Initialize chat settings with model selection
@cl.on_chat_start
async def start():
    await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Select Model",
                values=["pplx-70b-online", "pplx-70b-chat", "pplx-7b-chat", "codellama-34b-instruct", "mixtral-8x7b-instruct"],
                initial_index=0
            )
        ]
    ).send()

    user_session.set('conversation_state', [])
    user_session.set('current_model', 'pplx-70b-online')
    await cl.Avatar(
        name="perplexed",
        url="https://pbs.twimg.com/profile_images/1715563899502608385/NB3G6tx3_400x400.jpg"
    ).send()

# Handle settings update
@cl.on_settings_update
async def setup_agent(settings):
    new_model = settings['Model']
    user_session.set('current_model', new_model)
    logging.debug(f"Model updated to: {new_model}")
    # Clear conversation state to apply new model
    user_session.set('conversation_state', [])

# Main chat function
@cl.on_message
async def perplexity_chat(message: cl.Message):
    conversation_state = user_session.get('conversation_state', [])
    current_model = user_session.get('current_model', 'pplx-70b-online')
    logging.debug(f"Current model: {current_model}")

    conversation_state.append({'role': 'user', 'content': message.content})

    # Prepare data for API request
    data = {
        'model': current_model,
        'messages': conversation_state,
        'config': {'stop_sequence': None}
    }

    response = requests.post(PERPLEXITY_API_ENDPOINT, headers=headers, json=data)

    if response.status_code == 200:
        model_message = response.json()['choices'][0]['message']['content']
        conversation_state.append({'role': 'system', 'content': model_message})
        user_session.set('conversation_state', conversation_state)
        await cl.Message(content=model_message).send()
    else:
        logging.error(f'Error: {response.status_code}, {response.text}')

if __name__ == '__main__':
    cl.run()
