import os
from typing import TypedDict
import logging

from telegram import Update
from telegram.ext import ContextTypes, filters, MessageHandler

from game_sdk.game.chat_agent import Chat, ChatAgent
from telegram_plugin_gamesdk.telegram_plugin import TelegramPlugin
# Import RAG components
from rag_pinecone_gamesdk.rag_pinecone_plugin import RAGPineconePlugin
from rag_pinecone_gamesdk.rag_pinecone_game_functions import query_knowledge_fn, add_document_fn
from rag_pinecone_gamesdk.search_rag import RAGSearcher
from rag_pinecone_gamesdk.rag_pinecone_game_functions import (
    advanced_query_knowledge_fn, get_relevant_documents_fn
)
from rag_pinecone_gamesdk import DEFAULT_INDEX_NAME, DEFAULT_NAMESPACE

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../telegram/examples')))
from test_telegram_game_functions import send_message_fn, send_media_fn, create_poll_fn, pin_message_fn, unpin_message_fn, delete_message_fn
from dotenv import load_dotenv

load_dotenv()


game_api_key = os.environ.get("GAME_API_KEY")
telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
# Add RAG environment variables
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Print environment variable status
print(f"GAME API Key: {'✓' if game_api_key else '✗'}")
print(f"Telegram Bot Token: {'✓' if telegram_bot_token else '✗'}")
print(f"Pinecone API Key: {'✓' if pinecone_api_key else '✗'}")
print(f"OpenAI API Key: {'✓' if openai_api_key else '✗'}")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

class ActiveUser(TypedDict):
    chat_id: int
    name: str

# Update the prompt to include RAG capabilities
chat_agent = ChatAgent(
    prompt="""You are VIN (Virtuals Digital Intern). You are a helpful assistant with access to a knowledge base through RAG (Retrieval-Augmented Generation) capabilities.

""",
    api_key=game_api_key,
)

active_users: list[ActiveUser] = []
active_chats: dict[int, Chat] = {}

if __name__ == "__main__":
    tg_plugin = TelegramPlugin(bot_token=telegram_bot_token)
    
    # Initialize RAG plugins
    rag_plugin = RAGPineconePlugin(
        pinecone_api_key=pinecone_api_key,
        openai_api_key=openai_api_key,
        index_name=DEFAULT_INDEX_NAME,
        namespace=DEFAULT_NAMESPACE
    )
    
    # Initialize advanced RAG searcher
    rag_searcher = RAGSearcher(
        pinecone_api_key=pinecone_api_key,
        openai_api_key=openai_api_key,
        index_name=DEFAULT_INDEX_NAME,
        namespace=DEFAULT_NAMESPACE,
        llm_model="gpt-4o-mini",  # You can change this to "gpt-3.5-turbo" for faster, cheaper responses
        temperature=0.0,
        k=4  # Number of documents to retrieve
    )

    # Add RAG functions to the action space
    agent_action_space = [
        # Telegram functions
        send_message_fn(tg_plugin),
        send_media_fn(tg_plugin),
        create_poll_fn(tg_plugin),
        pin_message_fn(tg_plugin),
        unpin_message_fn(tg_plugin),
        delete_message_fn(tg_plugin),
        
        # RAG functions
        query_knowledge_fn(rag_plugin),
        add_document_fn(rag_plugin),
        advanced_query_knowledge_fn(rag_searcher),
        get_relevant_documents_fn(rag_searcher),
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

        # Handle non-text messages
        if update.message.text is None:
            logger.info("Received a non-text message, skipping processing")
            return

        # For group chats, only respond when the bot is mentioned or when it's a direct reply to the bot's message
        if chat_type in ["group", "supergroup"]:
            if (bot_username not in update.message.text and 
                (update.message.reply_to_message is None or 
                 update.message.reply_to_message.from_user.id != tg_plugin.bot.id)):
                logger.info("Ignoring group message not mentioning or replying to the bot")
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

        try:
            response = active_chats[chat_id].next(update.message.text.replace(bot_username, "").strip())  # Remove bot mention
            logger.info(f"Response: {response}")

            if response.message:
                await update.message.reply_text(response.message)

            if response.is_finished:
                active_chats.pop(chat_id)
                active_users.remove({"chat_id": chat_id, "name": name})
                logger.info(f"Chat with {name} ended.")
                logger.info(f"Active users: {active_users}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await update.message.reply_text("I'm sorry, something went wrong. Please try again later.")

    tg_plugin.add_handler(MessageHandler(filters.ALL, default_message_handler))

    # Start polling
    print("Starting Telegram bot with RAG capabilities...")
    tg_plugin.start_polling()

    # Example of executing a function from Telegram Plugin to a chat without polling
    #tg_plugin.send_message(chat_id=829856292, text="Hello! I am a helpful assistant. How can I assist you today?")
