import asyncio
from typing import List, Union
from telegram import Bot
from telegram.ext import ApplicationBuilder


def _run_async(coro):
    """
    Runs an async function safely.
    - If an event loop is running, it schedules the coroutine with `asyncio.create_task()`.
    - Otherwise, it starts a new event loop with `asyncio.run()`.
    """
    try:
        loop = asyncio.get_running_loop()
        return asyncio.create_task(coro)
    except RuntimeError:
        return asyncio.run(coro)


class TelegramPlugin:
    """
    A Telegram Bot SDK Plugin that integrates message handling and function-based execution.

    Features:
    - Handles user interactions in Telegram.
    - Supports function-based execution (e.g., sending messages, polls).
    - Manages active user sessions.

    Attributes:
        bot_token (str): The Telegram bot token, loaded from environment.
        application (Application): The Telegram application instance.
        bot (Bot): The Telegram bot instance.

    Example:
        ```python
        tgBot = TelegramPlugin(bot_token=os.getenv("TELEGRAM_BOT_TOKEN"))
        tgBot.start_polling()
        ```
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.application = ApplicationBuilder().token(self.bot_token).build()
        self.bot = self.application.bot

    def send_message(self, chat_id: Union[int, str], text: str):
        """Send a message to a chat safely while polling is running."""
        if not chat_id or not text:
            raise Exception("Error: chat_id and text are required.")

        return _run_async(self.bot.send_message(chat_id=chat_id, text=text))

    def send_media(
            self, chat_id: Union[int, str], media_type: str, media: str, caption: str = None
    ):
        """Send a media message (photo, document, video, audio) with an optional caption."""
        if not chat_id or not media_type or not media:
            raise Exception("Error: chat_id, media_type, and media are required.")

        if media_type == "photo":
            return _run_async(self.bot.send_photo(chat_id=chat_id, photo=media, caption=caption))
        elif media_type == "document":
            return _run_async(self.bot.send_document(chat_id=chat_id, document=media, caption=caption))
        elif media_type == "video":
            return _run_async(self.bot.send_video(chat_id=chat_id, video=media, caption=caption))
        elif media_type == "audio":
            return _run_async(self.bot.send_audio(chat_id=chat_id, audio=media, caption=caption))
        else:
            raise Exception("Error: Invalid media_type. Use 'photo', 'document', 'video', or 'audio'.")

    def create_poll(
            self, chat_id: Union[int, str], question: str, options: List[str], is_anonymous: bool = True,
            allows_multiple_answers: bool = False
    ):
        """Create a poll in a chat safely while polling is running."""
        if not chat_id or not question or not options:
            raise Exception("Error: chat_id, question, and options are required.")
        if not (2 <= len(options) <= 10):
            raise Exception("Poll must have between 2 and 10 options.")

        return _run_async(
            self.bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                is_anonymous=is_anonymous,
                allows_multiple_answers=allows_multiple_answers
            )
        )

    def pin_message(self, chat_id: Union[int, str], message_id: int):
        """Pin a message in the chat."""
        if chat_id is None or message_id is None:
            raise Exception("Error: chat_id and message_id are required to pin a message.")

        return _run_async(self.bot.pin_chat_message(chat_id=chat_id, message_id=message_id))

    def unpin_message(self, chat_id: Union[int, str], message_id: int):
        """Unpin a specific message in the chat."""
        if chat_id is None or message_id is None:
            raise Exception("Error: chat_id and message_id are required to unpin a message.")

        return _run_async(self.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id))

    def delete_message(self, chat_id: Union[int, str], message_id: int):
        """Delete a message from the chat."""
        if chat_id is None or message_id is None:
            raise Exception("Error: chat_id and message_id are required to delete a message.")

        return _run_async(self.bot.delete_message(chat_id=chat_id, message_id=message_id))

    def start_polling(self):
        """Start polling asynchronously in the main thread."""
        self.application.run_polling()

    def add_handler(self, handler):
        """Register a message handler for text messages."""
        self.application.add_handler(handler)
