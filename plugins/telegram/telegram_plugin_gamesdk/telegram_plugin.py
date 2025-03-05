from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument


class TelegramPlugin:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = Bot(token=self.bot_token)
        self.application = Application.builder().token(self.bot_token).build()

    def start_polling(self):
        self.application.run_polling()

    def stop_polling(self):
        self.application.stop()

    def on_message(self, handler):
        async def message_handler(update: Update, context: CallbackContext):
            handler(update.message)

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    def get_functions(self):
        return [
            self.send_message_function(),
            self.send_media_function(),
            self.create_poll_function()
        ]

    def send_message_function(self):
        async def executable(args, logger):
            chat_id = args.get('chat_id')
            text = args.get('text')

            if not chat_id or not text:
                return FunctionResultStatus.FAILED, "Both chat_id and text are required."

            try:
                await self.bot.send_message(chat_id=chat_id, text=text)
                return FunctionResultStatus.DONE, "Message sent successfully."

            except Exception as e:
                logger(f"Error: {e}")
                return FunctionResultStatus.FAILED, f"An error occurred while sending the message: {e}"

        return Function(
            fn_name="send_message",
            fn_description="Send a text message to a Telegram chat.",
            args=[
                Argument(
                    name="chat_id",
                    description="Chat ID or username",
                    type="string",
                ),
                Argument(
                    name="text",
                    description="Message content",
                    type="string",
                )
            ],
            executable=executable
        )

    def send_media_function(self):
        async def executable(args, logger):
            chat_id = args.get('chat_id')
            media_type = args.get('media_type')
            media = args.get('media')
            caption = args.get('caption', '')

            if not chat_id or not media_type or not media:
                return FunctionResultStatus.FAILED, "chat_id, media_type, and media are required."

            try:
                if media_type == 'photo':
                    await self.bot.send_photo(chat_id=chat_id, photo=media, caption=caption)
                elif media_type == 'document':
                    await self.bot.send_document(chat_id=chat_id, document=media, caption=caption)
                elif media_type == 'video':
                    await self.bot.send_video(chat_id=chat_id, video=media, caption=caption)
                elif media_type == 'audio':
                    await self.bot.send_audio(chat_id=chat_id, audio=media, caption=caption)
                else:
                    return FunctionResultStatus.FAILED, f"Unsupported media_type: {media_type}"

                return FunctionResultStatus.DONE, f"{media_type.capitalize()} sent successfully."

            except Exception as e:
                logger(f"Error: {e}")
                return FunctionResultStatus.FAILED, f"Failed to send media: {e}"

        return Function(
            fn_name="send_media",
            fn_description="Send a media message (photo, document, video, etc.) with an optional caption.",
            args=[
                Argument(
                    name="chat_id",
                    description="Target chat identifier where media will be sent.",
                    type="string",
                ),
                Argument(
                    name="media_type",
                    description="Type of media to send: 'photo', 'document', 'video', 'audio'.",
                    type="string",
                ),
                Argument(
                    name="media",
                    description="File ID or URL of the media to send.",
                    type="string",
                ),
                Argument(
                    name="caption",
                    description="Optional text caption accompanying the media.",
                    type="string",
                )
            ],
            executable=executable
        )

    def create_poll_function(self):
        async def executable(args, logger):
            chat_id = args.get('chat_id')
            question = args.get('question')
            options = args.get('options')
            is_anonymous = args.get('is_anonymous', True)

            if not chat_id or not question or not options:
                return FunctionResultStatus.FAILED, "chat_id, question, and options are required."

            try:
                options_list = [opt.strip() for opt in options.split(',')]
                if len(options_list) < 2:
                    return FunctionResultStatus.FAILED, "At least two options are required for a poll."

                await self.bot.send_poll(chat_id=chat_id, question=question, options=options_list, is_anonymous=is_anonymous)

                return FunctionResultStatus.DONE, "Poll created successfully."

            except Exception as e:
                logger(f"Error: {e}")
                return FunctionResultStatus.FAILED, f"Failed to create poll: {e}"

        return Function(
            fn_name="create_poll",
            fn_description="Create an interactive poll to gather user opinions.",
            args=[
                Argument(
                    name="chat_id",
                    description="Chat ID or username where the poll will be created.",
                    type="string",
                ),
                Argument(
                    name="question",
                    description="Main poll question.",
                    type="string",
                ),
                Argument(
                    name="options",
                    description="Comma-separated list of answer options.",
                    type="string",
                ),
                Argument(
                    name="is_anonymous",
                    description="Whether poll responses are anonymous.",
                    type="boolean",
                )
            ],
            executable=executable
        )
