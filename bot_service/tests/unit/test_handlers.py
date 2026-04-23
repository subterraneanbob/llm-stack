from app.bot.handlers import BotMessage, prompt_handler, start_handler, token_handler
from tests.conftest import token_command


async def test_start(mock_message):
    # Бот отправляет приветствие при старте.
    await start_handler(mock_message.object)

    mock_message.validate_reply(BotMessage.GREETING)


async def test_token_missing_token(mock_redis, mock_message):
    # Бот просит указать токен при его отсутствии.
    await token_handler(mock_message.object, token_command(""))

    mock_message.validate_reply(BotMessage.MISSING_TOKEN)
    await mock_redis.validate_token(mock_message.tg_chat_id, None)


async def test_token_invalid_token(mock_redis, mock_message, invalid_access_token):
    # Бот просит выпустить новый токен взамен некорректного.
    await token_handler(mock_message.object, token_command(invalid_access_token))

    mock_message.validate_reply(BotMessage.INVALID_TOKEN)
    await mock_redis.validate_token(mock_message.tg_chat_id, None)


async def test_token_expired_token(mock_redis, mock_message, expired_access_token):
    # Бот просит выпустить новый токен взамен истекшего.
    await token_handler(mock_message.object, token_command(expired_access_token))

    mock_message.validate_reply(BotMessage.EXPIRED_TOKEN)
    await mock_redis.validate_token(mock_message.tg_chat_id, None)


async def test_token_save(mock_redis, mock_message, access_token):
    # Бот сохраняет корректный токен в Redis и сообщает об этом пользователю.
    await token_handler(mock_message.object, token_command(access_token))

    mock_redis.validate_token(mock_message.tg_chat_id, access_token)
    mock_message.validate_reply(BotMessage.TOKEN_SAVED)


async def test_prompt_missing_token(mock_redis, mock_message, mock_llm_request_task):
    # Бот просит выполнить команду /token при отсутствии токена.
    await prompt_handler(mock_message.object)

    mock_message.validate_reply(BotMessage.TOKEN_REQUIRED)
    mock_llm_request_task.was_not_triggered()


async def test_prompt_invalid_token(
    mock_redis, mock_message, mock_llm_request_task, invalid_access_token
):
    # Бот просит выполнить команду /token, если токен некорректный.
    # Этот тест кажется избыточным, т.к. сохранить невалидный токен нельзя.
    # Однако, эта ситуация может произойти, если секретный ключ для генерации JWT был ротирован,
    # а прошлые токены из Redis не были удалены.
    await mock_redis.set_token(mock_message.tg_chat_id, invalid_access_token)

    await prompt_handler(mock_message.object)

    mock_message.validate_reply(BotMessage.INVALID_TOKEN)
    mock_llm_request_task.was_not_triggered()


async def test_prompt_expired_token(
    mock_redis, mock_message, mock_llm_request_task, expired_access_token
):
    # Бот просит выполнить команду /token, если срок действия токен истёк.
    await mock_redis.set_token(mock_message.tg_chat_id, expired_access_token)

    await prompt_handler(mock_message.object)

    mock_message.validate_reply(BotMessage.EXPIRED_TOKEN)
    mock_llm_request_task.was_not_triggered()


async def test_prompt_trigger_task(
    mock_redis, mock_message, mock_llm_request_task, access_token
):
    # Бот принимает запрос пользователя, запускает задачу и сообщает пользователю об этом.
    await mock_redis.set_token(mock_message.tg_chat_id, access_token)

    await prompt_handler(mock_message.object)

    mock_message.validate_reply(BotMessage.REQUEST_ACCEPTED)
    mock_llm_request_task.was_triggered_with(mock_message.tg_chat_id, mock_message.text)
