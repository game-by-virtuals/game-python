import os
from typing import TypedDict
import logging

from telegram import Update
from telegram.ext import ContextTypes, filters, MessageHandler

from game_sdk.game.chat_agent import Chat, ChatAgent
from telegram_plugin_gamesdk.telegram_plugin import TelegramPlugin
from test_telegram_game_functions import send_message_fn, send_media_fn, create_poll_fn, pin_message_fn, unpin_message_fn, delete_message_fn

game_api_key = os.environ.get("GAME_API_KEY")
telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

class ActiveUser(TypedDict):
    chat_id: int
    name: str

chat_agent = ChatAgent(
    prompt="You are a helpful assistant.",
    api_key=game_api_key,
)

active_users: list[ActiveUser] = []
active_chats: dict[int, Chat] = {}

if __name__ == "__main__":
    tg_plugin = TelegramPlugin(bot_token=telegram_bot_token)

    agent_action_space = [
        send_message_fn(tg_plugin),
        send_media_fn(tg_plugin),
        create_poll_fn(tg_plugin),
        pin_message_fn(tg_plugin),
        unpin_message_fn(tg_plugin),
        delete_message_fn(tg_plugin),
    ]

    async def default_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles incoming messages but ignores messages from the bot itself unless it's mentioned in a group chat."""

        # Ignore messages from the bot itself
        if update.message.from_user.id == tg_plugin.bot.id:
            logger.info("Ignoring bot's own message.")
            return

        user = update.message.from_user
        chat_id = update.message.chat.id
        chat_type = update.message.chat.type  # "private", "group", "supergroup", or "channel"
        bot_username = f"@{tg_plugin.bot.username}"

        logger.info(f"Update received: {update}")
        logger.info(f"Message received: {update.message.text}")

        name = f"{user.first_name} (Telegram's chat_id: {chat_id}, this is not part of the partner's name but important for the telegram's function arguments)"

        # Ignore group/supergroup messages unless the bot is mentioned
        if chat_type in ["group", "supergroup"] and bot_username not in update.message.text:
            logger.info(f"Ignoring group message not mentioning the bot: {update.message.text}")
            return

        if not any(u["chat_id"] == chat_id for u in active_users):
            active_users.append({"chat_id": chat_id, "name": name})
            logger.info(f"Active user added: {name}")
            logger.info(f"Active users: {active_users}")
            chat = chat_agent.create_chat(
                partner_id=str(chat_id),
                partner_name=name,
                action_space=agent_action_space,
            )
            active_chats[chat_id] = chat

        response = active_chats[chat_id].next(update.message.text.replace(bot_username, "").strip())  # Remove bot mention
        logger.info(f"Response: {response}")

        if response.message:
            await update.message.reply_text(response.message)

        if response.is_finished:
            active_chats.pop(chat_id)
            active_users.remove({"chat_id": chat_id, "name": name})
            logger.info(f"Chat with {name} ended.")
            logger.info(f"Active users: {active_users}")

    tg_plugin.add_handler(MessageHandler(filters.ALL, default_message_handler))

    # Start polling
    tg_plugin.start_polling()

    # Example of executing a function from Telegram Plugin to a chat without polling
    #tg_plugin.send_message(chat_id=829856292, text="Hello! I am a helpful assistant. How can I assist you today?")
