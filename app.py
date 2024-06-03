from quart import Quart, request, jsonify
from telegram import Bot
import os
import logging
from dotenv import load_dotenv
from telegram.request import HTTPXRequest

load_dotenv()  # Load environment variables from .env file

app = Quart(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Verify environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
AUTHORIZED_CHAT_IDS = os.getenv('AUTHORIZED_CHAT_IDS')
logger.info(f"BOT_TOKEN: {BOT_TOKEN}")
logger.info(f"AUTHORIZED_CHAT_IDS: {AUTHORIZED_CHAT_IDS}")

# Convert AUTHORIZED_CHAT_IDS to a list of integers
AUTHORIZED_CHAT_IDS = [int(chat_id) for chat_id in AUTHORIZED_CHAT_IDS.split(',')]

# Configure the HTTPXRequest with custom pool settings
tg_request = HTTPXRequest(connection_pool_size=10)

bot = Bot(token=BOT_TOKEN, request=tg_request)

async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")

@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Webhook received!")
    
    data = await request.get_json()
    logger.info(f"Payload: {data}")

    # Check if it's a push event to the main branch
    if 'ref' in data and data['ref'] == 'refs/heads/main':
        logger.info("Push to main branch detected")
        if 'head_commit' in data:
            commit = data['head_commit']
            message = (f"New push to main by {commit['author']['name']}:\n"
                       f"{commit['message']}\n"
                       f"{commit['url']}")
            logger.info(f"Sending message: {message}")

            # Send message to all authorized chat IDs
            for chat_id in AUTHORIZED_CHAT_IDS:
                await send_message(chat_id, message)

        else:
            logger.info("No head_commit found in the payload")
    else:
        logger.info("Not a push to the main branch")
    
    return jsonify({'status': 'success'}), 200

@app.route('/start', methods=['GET'])
async def start():
    first_chat_id = AUTHORIZED_CHAT_IDS[0]
    await send_message(first_chat_id, "Bot is running and ready to send messages.")
    return 'Bot started!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)