from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from core.llm.factory import LLMProvider


class BrainCrashGraphState(TypedDict):
    # LLM ==============================================================================================================
    provider: LLMProvider                                           # 모델 제공사 (anthropic, openai, gemini 등)
    model_name: Optional[str]                                       # 모델 이름
    model_config: dict                                              # temperature 등 모델 config

    # Chat =============================================================================================================
    user_query: str                                                 # 최신 유저 질의
    messages: Annotated[list, add_messages]                         # 대화 기록

    # Usage
    # TODO define usage vars
