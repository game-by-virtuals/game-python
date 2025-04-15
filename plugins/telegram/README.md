# Telegram Plugin for GAME SDK

## Overview

The **Telegram Plugin** is an integration for the **Game SDK** that enables AI-driven interactions on Telegram. This plugin allows AI agents to handle messages, execute commands, and engage users through text, media, and polls.

## Features

- **Send Messages** – AI agents can send text messages to users.
- **Send Media** – Supports sending photos, documents, videos, and audio.
- **Create Polls** – AI agents can generate interactive polls.
- **Pin & Unpin Messages** – Manage pinned messages in chats.
- **Delete Messages** – Remove messages dynamically.
- **AI-Powered Responses** – Leverages LLM to generate contextual replies.
- **Real-Time Polling** – Runs asynchronously with Telegram’s polling system.
- and more features to come!

## Installation
### Pre-requisites
Ensure you have Python 3.9+ installed. Then, install the plugin via **PyPI**:
### Steps
1. Install the plugin:
   ```sh bash
   pip install telegram-plugin-gamesdk
   ```
2. Ensure you have a Telegram bot token and GAME API key and set them as environment variables:
   ```sh bash
   export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
   export GAME_API_KEY="your-game-api-key"
   ```
3. Refer to the example and run the example bot:
   ```sh bash
   python examples/test_telegram.py
   ```

## Usage Examples
### Initializing the Plugin

```python
from telegram_plugin_gamesdk.telegram_plugin import TelegramPlugin

tg_bot = TelegramPlugin(bot_token='your-telegram-bot-token')
tg_bot.start_polling()
```

### Sending a Message
```python
tg_bot.send_message(chat_id=123456789, text="Hello from the AI Agent!")
```

### Sending Media
```python
tg_bot.send_media(chat_id=123456789, media_type="photo", media="https://example.com/image.jpg", caption="Check this out!")
```

### Creating a Poll
```python
tg_bot.create_poll(chat_id=123456789, question="What's your favorite color?", options=["Red", "Blue", "Green"])
```

### Pinning and Unpinning Messages
```python
tg_bot.pin_message(chat_id=123456789, message_id=42)
tg_bot.unpin_message(chat_id=123456789, message_id=42)
```

### Deleting a Message
```python
tg_bot.delete_message(chat_id=123456789, message_id=42)
```

## Integration with GAME Chat Agent
Implement a message handler to integrate the Telegram Plugin with the GAME Chat Agent:
```python
from telegram import Update
from telegram.ext import ContextTypes, filters, MessageHandler
from game_sdk.game.chat_agent import ChatAgent

chat_agent = ChatAgent(
    prompt="You are a helpful assistant.",
    api_key="your-game-api-key",
)

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

    if not any(u["chat_id"] == chat_id for u in active_users):
        # Ignore group/supergroup messages unless the bot is mentioned
        if chat_type in ["group", "supergroup"] and bot_username not in update.message.text:
            logger.info(f"Ignoring group message not mentioning the bot: {update.message.text}")
            return
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
```
You can refer to [test_telegram.py](examples/test_telegram.py) for details.
