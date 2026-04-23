from typing import Any

from aiogram import F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message


from app.core.errors import InvalidTokenError, TokenExpiredError
from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis, token_key
from app.tasks.llm_tasks import llm_request


router = Router()

# Бот доступен только в личных сообщениях
router.message.filter(F.chat.type == ChatType.PRIVATE)


class BotMessage:
    """
    Сообщения, которые бот может отправить пользователю.
    """

    GREETING = (
        "Этот бот позволяет отправлять запросы к LLM через OpenRouter. "
        "Для начала работы необходима авторизация по JWT-токену. "
        "Пожалуйста, выполните команду /token <JWT>."
    )
    EXPIRED_TOKEN = (
        "Срок действия JWT-токена истёк. "
        "Пожалуйста, запросите новый токен у сервиса авторизации, "
        "а затем выполните команду /token <JWT>."
    )
    INVALID_TOKEN = (
        "Предоставлен некорректный JWT-токен. "
        "Пожалуйста, запросите новый токен у сервиса авторизации, "
        "а затем выполните команду /token <JWT>."
    )
    MISSING_TOKEN = "Пожалуйста, укажите корректный токен после команды (/token <JWT>)."
    TOKEN_REQUIRED = (
        "Пожалуйста, сначала выполните команду /token <JWT> для авторизации."
    )
    TOKEN_SAVED = "Токен сохранён. Теперь можете отправить запрос LLM."
    REQUEST_ACCEPTED = "Запрос принят. Пожалуйста, ожидайте ответ LLM."


async def validate_token_and_reply(
    token: str, message: Message
) -> dict[str, Any] | None:
    """
    Проверяет токен доступа и отправляет инструкцию пользователю,
    если токен неверный или истёк срок действия.

    Args:
        token (str): Токен доступа.
        message (Message): Сообщение чата, на которое нужно дать ответ с инструкцией.

    Returns:
        dict[str, Any] | None: Словарь полей, указанных в токене, или None,
            если токен не удалось проверить.
    """
    try:
        return decode_and_validate(token)
    except TokenExpiredError:
        await message.answer(BotMessage.EXPIRED_TOKEN)
    except InvalidTokenError:
        await message.answer(BotMessage.INVALID_TOKEN)


@router.message(CommandStart())
async def start_handler(message: Message):
    """
    Обработчик /start.
    """
    await message.answer(BotMessage.GREETING)


@router.message(Command("token"))
async def token_handler(message: Message, command: CommandObject):
    """
    Обработчик /token <JWT>.
    """

    token = (command.args or "").strip()

    if not token:
        await message.answer(BotMessage.MISSING_TOKEN)
        return

    if not (claims := await validate_token_and_reply(token, message)):
        return

    # Сохраняем токен на срок его действия
    await get_redis().set(
        token_key(message.from_user.id), token, exat=claims.get("exp")
    )

    await message.answer(BotMessage.TOKEN_SAVED)


@router.message(F.text)
async def prompt_handler(message: Message):
    """
    Обработчик запросов пользователя к LLM. Требует валидный JWT-токен (команда /token).
    """
    tg_chat_id = message.from_user.id
    token = await get_redis().get(token_key(tg_chat_id))

    if not token:
        await message.answer(BotMessage.TOKEN_REQUIRED)
        return

    if not await validate_token_and_reply(token, message):
        return

    await message.answer(BotMessage.REQUEST_ACCEPTED)
    llm_request.delay(tg_chat_id=tg_chat_id, prompt=message.text)
