from flask import Flask, request, jsonify
import telegram
import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

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
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("Webhook received!")
    
    if request.method == 'POST':
        data = request.json
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
                    bot.send_message(chat_id=chat_id, text=message)
                    logger.info(f"Message sent to {chat_id}")

            else:
                logger.info("No head_commit found in the payload")
        else:
            logger.info("Not a push to the main branch")
        
        return jsonify({'status': 'success'}), 200

@app.route('/start', methods=['GET'])
def start():
    first_chat_id = AUTHORIZED_CHAT_IDS[0]
    bot.send_message(chat_id=first_chat_id, text="Bot is running and ready to send messages.")
    return 'Bot started!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)