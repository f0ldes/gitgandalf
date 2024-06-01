from flask import Flask, request
import telegram
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN') #token here
AUTHROIZED_CHAT_IDS = [int(chat_id) for chat_id in 
                       os.getnv('AUTHORIZED_CHAT_IDS').split(',')]
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        chat_id = None
        
        if 'message' in data:
            chat_id = data['message']['chat']['id']
        elif 'channel_post' in data:
            chat_id = data['channel_post']['chat']['id']

        if chat_id in AUTHROIZED_CHAT_IDS:

            if 'ref' in data and data['ref'] == 'refs/heads/main':
                if 'head_commit' in data:
                    commit = data['head_commit']
                    message = f"Blavla  by {commit['author']['name']}: \n{commit['message']}\n{commit['url']}"
                    bot.send_message(chat_id=chat_id, text=message)
        return '', 200
    

if __name__ == '__main__':
    app.run(port=5000)