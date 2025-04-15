from typing import Tuple

from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument
from telegram_plugin_gamesdk.telegram_plugin import TelegramPlugin


def send_message_executable(tg_plugin: TelegramPlugin, chat_id: str, text: str) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        tg_plugin.send_message(chat_id=chat_id, text=text)
        return FunctionResultStatus.DONE, "Message sent successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}


def send_message_fn(bot: TelegramPlugin) -> Function:
    return Function(
        fn_name="send_message",
        fn_description="Send a text message to a Telegram chat",
        args=[
            Argument(name="chat_id", description="ID of the chat to send the message to", type="str"),
            Argument(name="text", description="Text message to send", type="str"),
        ],
        executable=lambda chat_id, text: send_message_executable(bot, chat_id, text),
    )


def send_media_executable(tg_plugin: TelegramPlugin, chat_id: str, media_type: str, media: str, caption: str = None) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        tg_plugin.send_media(chat_id=chat_id, media_type=media_type, media=media, caption=caption)
        return FunctionResultStatus.DONE, "Media sent successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}


def send_media_fn(bot: TelegramPlugin) -> Function:
    return Function(
        fn_name="send_media",
        fn_description="Send a media message to a Telegram chat",
        args=[
            Argument(name="chat_id", description="ID of the chat to send the message to", type="str"),
            Argument(name="media_type", description="Type of media to send (photo, document, video, audio)", type="str"),
            Argument(name="media", description="Media URL or file path to send", type="str"),
            Argument(name="caption", description="Optional caption for the media", type="str", optional=True),
        ],
        executable=lambda chat_id, media_type, media, caption=None: send_media_executable(bot, chat_id, media_type, media, caption),
    )


def create_poll_executable(tg_plugin: TelegramPlugin, chat_id: str, question: str, options: list[str], is_anonymous: bool = True, allows_multiple_answers: bool = False) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        tg_plugin.create_poll(chat_id=chat_id, question=question, options=options, is_anonymous=is_anonymous, allows_multiple_answers=allows_multiple_answers)
        return FunctionResultStatus.DONE, "Poll created successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}


def create_poll_fn(bot: TelegramPlugin) -> Function:
    return Function(
        fn_name="create_poll",
        fn_description="Create a poll in a Telegram chat",
        args=[
            Argument(name="chat_id", description="ID of the chat to create the poll in", type="str"),
            Argument(name="question", description="Question to ask in the poll", type="str"),
            Argument(name="options", description="List of options for the poll", type="List[str]"),
            Argument(name="is_anonymous", description="Whether the poll is anonymous (default: True)", type="bool", optional=True),
            Argument(name="allows_multiple_answers", description="Whether multiple answers are allowed (default: False)", type="bool", optional=True),
        ],
        executable=lambda chat_id, question, options, is_anonymous=False, allows_multiple_answers=False: create_poll_executable(bot, chat_id, question, options, is_anonymous, allows_multiple_answers),
    )


def pin_message_executable(tg_plugin: TelegramPlugin, chat_id: str, message_id: int) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        tg_plugin.pin_message(chat_id=chat_id, message_id=message_id)
        return FunctionResultStatus.DONE, "Message pinned successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}


def pin_message_fn(bot: TelegramPlugin) -> Function:
    return Function(
        fn_name="pin_message",
        fn_description="Pin a message in a Telegram chat",
        args=[
            Argument(name="chat_id", description="ID of the chat to pin the message in", type="str"),
            Argument(name="message_id", description="ID of the message to pin", type="int"),
        ],
        executable=lambda chat_id, message_id: pin_message_executable(bot, chat_id, message_id),
    )


def unpin_message_executable(tg_plugin: TelegramPlugin, chat_id: str, message_id: int) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        tg_plugin.unpin_message(chat_id=chat_id, message_id=message_id)
        return FunctionResultStatus.DONE, "Message unpinned successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}


def unpin_message_fn(bot: TelegramPlugin) -> Function:
    return Function(
        fn_name="unpin_message",
        fn_description="Unpin a message in a Telegram chat",
        args=[
            Argument(name="chat_id", description="ID of the chat to unpin the message in", type="str"),
            Argument(name="message_id", description="ID of the message to unpin", type="int"),
        ],
        executable=lambda chat_id, message_id: unpin_message_executable(bot, chat_id, message_id),
    )


def delete_message_executable(tg_plugin: TelegramPlugin, chat_id: str, message_id: int) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        tg_plugin.delete_message(chat_id=chat_id, message_id=message_id)
        return FunctionResultStatus.DONE, "Message deleted successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}


def delete_message_fn(bot: TelegramPlugin) -> Function:
    return Function(
        fn_name="delete_message",
        fn_description="Delete a message in a Telegram chat",
        args=[
            Argument(name="chat_id", description="ID of the chat to delete the message in", type="str"),
            Argument(name="message_id", description="ID of the message to delete", type="int"),
        ],
        executable=lambda chat_id, message_id: delete_message_executable(bot, chat_id, message_id),
    )
