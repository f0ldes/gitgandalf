from flask import Flask, request, jsonify
import telegram
import os
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN') #token here
AUTHOROIZED_CHAT_IDS = [int(chat_id) for chat_id in 
                       os.getenv('AUTHORIZED_CHAT_IDS').split(',')]
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    logging.info("Webhook received!")
    
    if request.method == 'POST':
        data = request.json
        logging.info(f"Payload: {data}")
        chat_id = None

        # Extract chat ID from the incoming update
        if 'message' in data:
            chat_id = data['message']['chat']['id']
        elif 'channel_post' in data:
            chat_id = data['channel_post']['chat']['id']
        
        logging.info(f"Chat ID: {chat_id}")

        # Check if the chat ID is authorized
        if chat_id in AUTHOROIZED_CHAT_IDS:
            logging.info("Chat ID is authorized")
            
            # Process the webhook payload to get the necessary information
            # Example for GitHub:
            if 'ref' in data and data['ref'] == 'refs/heads/main':
                if 'head_commit' in data:
                    commit = data['head_commit']
                    message = (f"New push to main by {commit['author']['name']}:\n"
                               f"{commit['message']}\n"
                               f"{commit['url']}")
                    logging.info(f"Sending message: {message}")
                    bot.send_message(chat_id=chat_id, text=message)
                    logging.info("Message sent successfully")
                else:
                    logging.info("No head_commit found in the payload")
            else:
                logging.info("Not a push to the main branch")
        else:
            logging.info("Chat ID is not authorized")
        
        return jsonify({'status': 'success'}), 200
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0' ,port=port)