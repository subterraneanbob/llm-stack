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
        await message.answer(
            (
                "Срок действия JWT-токена истёк. "
                "Пожалуйста, запросите новый токен у сервиса авторизации, "
                "а затем выполните команду /token <JWT>."
            )
        )
    except InvalidTokenError:
        await message.answer(
            (
                "Предоставлен некорректный JWT-токен. "
                "Пожалуйста, запросите новый токен у сервиса авторизации, "
                "а затем выполните команду /token <JWT>."
            )
        )


@router.message(CommandStart())
async def start_handler(message: Message):
    """
    Обработчик /start.
    """
    await message.answer(
        (
            "Этот бот позволяет отправлять запросы к LLM через OpenRouter. "
            "Для начала работы необходима авторизация по JWT-токену. "
            "Пожалуйста, выполните команду /token <JWT>."
        )
    )


@router.message(Command("token"))
async def token_handler(message: Message, command: CommandObject):
    """
    Обработчик /token <JWT>.
    """

    token = (command.args or "").strip()

    if not token:
        await message.answer(
            "Пожалуйста, укажите корректный токен после команды (/token <JWT>)."
        )
        return

    if not (claims := await validate_token_and_reply(token, message)):
        return

    await get_redis().set(
        token_key(message.from_user.id), token, exat=claims.get("exp")
    )

    await message.answer("Токен сохранён. Теперь можете отправить запрос LLM.")


@router.message(F.text)
async def prompt_handler(message: Message):
    """
    Обработчик запросов пользователя к LLM. Требует валидный JWT-токен (команда /token).
    """
    tg_chat_id = message.from_user.id

    token = await get_redis().get(token_key(tg_chat_id))

    if not token:
        await message.answer(
            "Пожалуйста, сначала выполните команду /token <JWT> для авторизации."
        )
        return

    if not await validate_token_and_reply(token, message):
        return

    await message.answer("Запрос принят. Пожалуйста, ожидайте ответ LLM.")
    llm_request.delay(tg_chat_id=tg_chat_id, prompt=message.text)
