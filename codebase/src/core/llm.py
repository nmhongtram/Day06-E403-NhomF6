"""LLM factory — creates ChatOpenAI instances from environment config."""

import os
from langchain_openai import ChatOpenAI


def get_llm(model_key: str = "OPENAI_MODEL_FAST") -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv(model_key, "gpt-4o-mini"),
        temperature=0,
    )


def get_smart_llm() -> ChatOpenAI:
    """Use the stronger model for QA + complex reasoning."""
    return get_llm("OPENAI_MODEL_SMART")
