from app.services.openrouter_client import make_chat_completion


async def test_make_chat_completion(mock_openrouter_client):
    # Проверка клиента OpenRouter:
    # - тело запроса содержит заданный промпт
    # - корректный HTTP запрос был отправлен

    prompt = "What is a skeleton's favorite instrument?"
    expected_answer = "The trom-bone."
    mock_openrouter_client.setup(expected_answer)

    answer = make_chat_completion(prompt)

    assert answer == expected_answer
    mock_openrouter_client.verify_request(prompt)
    mock_openrouter_client.verify_route_call()
