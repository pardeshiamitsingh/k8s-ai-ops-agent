import pytest
from pydantic import ValidationError

from k8s_ai_ops.llm.factory import LLMFactory
from k8s_ai_ops.llm.providers.fake import FakeChatModel
from k8s_ai_ops.llm.settings import LLMSettings


def test_fake_provider():

    settings = LLMSettings(
        provider="fake",
    )

    model = LLMFactory.create(settings)

    assert isinstance(
        model,
        FakeChatModel,
    )


def test_fake_provider_is_supported():

    settings = LLMSettings(
        provider="fake",
    )

    assert settings.provider == "fake"


def test_unsupported_provider():

    with pytest.raises(ValidationError):

        LLMSettings(
            provider="unsupported",
        )