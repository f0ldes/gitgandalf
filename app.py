from quart import Quart, request, jsonify
import telegram
import os
import logging
from dotenv import load_dotenv
import asyncio
from telegram.request import HTTPXRequest

load_dotenv()  # Load environment variables from .env file

app = Quart(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Verify environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
logger.info(f"BOT_TOKEN: {BOT_TOKEN}")

# Repository to update type mapping
REPO_UPDATE_MAPPING = {
    'portfolio_v2': {
        'head_commit': [-1002175201609],
        'pull_request': [-1002175201609, -4192197568],
    },
    'abovo-web-employers': {
        'head_commit': [-4192197568, -4210472507],
        'pull_request': [-4192197568]
        # 'head_commit': [-4210472507],
        # 'pull_request': [-4210472507],
    },
}


# Specific chat ID for additional notification on pull request
SPECIAL_CHAT_ID = -4192197568

# Configure the HTTPXRequest with custom pool settings
tg_request = HTTPXRequest(connection_pool_size=10)

bot = telegram.Bot(token=BOT_TOKEN, request=tg_request)

async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")

@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Webhook received!")
    
    if request.method == 'POST':
        data = await request.get_json()
        logger.info(f"Payload: {data}")

        repo_name = data['repository']['name'] if 'repository' in data else None
        if not repo_name or repo_name not in REPO_UPDATE_MAPPING:
            return jsonify({'status': 'repo not configured'}), 400
        
        update_mapping = REPO_UPDATE_MAPPING[repo_name]

        # Check for push events to main or master branch
        if 'ref' in data and (data['ref'] == 'refs/heads/main' or data['ref'] == 'refs/heads/master' or data['ref'] == 'refs/heads/dev'):
            logger.info("Push to main or master branch detected")
            if 'head_commit' in data and 'head_commit' in update_mapping:
                commit = data['head_commit']
                branch = data['ref'].split('/')[-1]
                message = (f"New push to {branch} by {commit['author']['name']}:\n"
                           f"Branch: {branch}\n"
                           f"Message: {commit['message']}\n"
                           f"Link: {commit['url']}")
                logger.info(f"Sending message: {message}")

                # Send message to all mapped chat IDs for head_commit
                for chat_id in update_mapping['head_commit']:
                    await send_message(chat_id, message)

        # Check for pull request events
        elif 'pull_request' in data:
            pr = data['pull_request']
            base_branch = pr['base']['ref']
            if pr['state'] == 'open' and base_branch in ['main', 'master', 'dev']:
                pr_message = (f"Pull request by {pr['user']['login']}:\n"
                              f"Branch: {pr['head']['ref']} -> {base_branch}\n"
                              f"Message: {pr['title']}\n"
                              f"Commit message: {pr['body']}\n"
                              f"Link: {pr['html_url']}")
                logger.info(f"Sending pull request message: {pr_message}")

                # Send message to all mapped chat IDs for pull_request
                for chat_id in update_mapping['pull_request']:
                    await send_message(chat_id, pr_message)

                # Also send to the special chat ID
                # await send_message(SPECIAL_CHAT_ID, pr_message)

        else:
            logger.info("Not a push to the main or master branch and not a relevant pull request")
        
        return jsonify({'status': 'success'}), 200

@app.route('/start', methods=['GET'])
async def start():
    for repo, updates in REPO_UPDATE_MAPPING.items():
        for update_type, chat_ids in updates.items():
            for chat_id in chat_ids:
                await send_message(chat_id, f"Bot is running and ready to send {update_type} updates for repository {repo}.")
    return 'Bot started!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)