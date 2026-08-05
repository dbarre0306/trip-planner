from unittest.mock import MagicMock, patch

import pytest

from trip_planner.integrations.openai_client import chat_completion, get_client, get_model


@pytest.fixture(autouse=True)
def _clear_caches():
    get_client.cache_clear()
    get_model.cache_clear()
    yield
    get_client.cache_clear()
    get_model.cache_clear()


@patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
@patch("trip_planner.integrations.openai_client.OpenAI")
def test_get_client_uses_api_key_from_env(mock_openai):
    get_client()

    mock_openai.assert_called_once_with(api_key="test-key")


@patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
@patch("trip_planner.integrations.openai_client.OpenAI")
def test_get_client_caches_the_client_instance(mock_openai):
    first = get_client()
    second = get_client()

    mock_openai.assert_called_once_with(api_key="test-key")
    assert first is second


@patch.dict("os.environ", {}, clear=True)
def test_get_client_raises_when_api_key_missing():
    with pytest.raises(RuntimeError):
        get_client()


@patch.dict("os.environ", {"MODEL": "gpt-4o-mini"})
def test_get_model_returns_model_from_env():
    assert get_model() == "gpt-4o-mini"


@patch.dict("os.environ", {"MODEL": "gpt-4o-mini"})
def test_get_model_caches_the_result():
    with patch.dict("os.environ", {"MODEL": "gpt-4o-mini"}):
        first = get_model()
    with patch.dict("os.environ", {"MODEL": "some-other-model"}):
        second = get_model()

    assert first == second == "gpt-4o-mini"


@patch.dict("os.environ", {}, clear=True)
def test_get_model_raises_when_model_missing():
    with pytest.raises(RuntimeError):
        get_model()


@patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "MODEL": "gpt-4o-mini"})
@patch("trip_planner.integrations.openai_client.OpenAI")
def test_chat_completion_calls_configured_model(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="hello"))]
    mock_client.chat.completions.create.return_value = mock_response

    result = chat_completion([{"role": "user", "content": "hi"}])

    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}]
    )
    assert result == "hello"
