from langchain_aws import ChatBedrockConverse

from k8s_ai_ops.llm.settings import LLMSettings


def create_bedrock_model(
    settings: LLMSettings,
) -> ChatBedrockConverse:

    model_id = (
        settings.bedrock_model_id
        or settings.model
    )

    if not model_id:
        raise ValueError(
            "AWS_BEDROCK_MODEL_ID or LLM_MODEL is required"
        )

    return ChatBedrockConverse(
        model=model_id,
        region_name=settings.aws_region,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )