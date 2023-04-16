import logging
from datetime import timedelta

from telegram import Update, User
from telegram.ext import Updater, Dispatcher, MessageHandler, Filters, CallbackContext

from mode import Mode
from skills.mute import mute_user_for_time
from utils.recognition import get_recognized_text

logger = logging.getLogger(__name__)

mode = Mode(mode_name="nastya_mode", default=True)

MAX_DURATION = 60  # seconds
VOICE_USER_MUTE_DURATION = timedelta(weeks=1)
EXCLUDING = ["@ravino_doul"]


@mode.add
def add_nastya_mode(upd: Updater, handlers_group: int):
    logger.info("registering nastya handlers")
    dp: Dispatcher = upd.dispatcher

    dp.add_handler(
        MessageHandler(
            (Filters.voice | Filters.video_note) & ~Filters.status_update,
            handle_nastya_mode,
            run_async=True,
        ),
        handlers_group,
    )


def handle_nastya_mode(update: Update, context: CallbackContext):
    user: User = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message

    if user.name in EXCLUDING:
        return

    message_type = message.voice or message.video_note
    duration = message_type.duration

    if duration > MAX_DURATION:
        message_text = f"🤫🤫🤫 @{user.username}! Слишком много наговорил..."
    else:
        file_id = message_type.file_id
        logger.info("%s sent message!", user.name)
        default_message = f"@{user.username} промямлил что-то невразумительное..."
        recognized_text = None

        try:
            recognized_text = get_recognized_text(file_id)
        except (AttributeError, ValueError, RuntimeError) as err:
            logger.exception("failed to recognize speech: %s", err)

        if recognized_text is None:
            message_text = default_message
        else:
            message_text = (
                f"🤫🤫🤫 Групповой чат – не место для войсов и кружочков, @{user.username}!"
                f"\n@{user.username} пытался сказать: {recognized_text}"
            )

    context.bot.send_message(chat_id=chat_id, text=message_text)

    try:
        mute_user_for_time(update, context, user, VOICE_USER_MUTE_DURATION)
    finally:
        context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
