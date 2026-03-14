from core.llm.factory import LLMProvider, get_llm
from ..types import BrainCrashGraphState
from services.chat.utils import load_prompt
from datetime import date
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from services.chat.utils import load_prompt, export_messages_to_tuples
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent


async def main_node(state: BrainCrashGraphState):
    output_messages = [HumanMessage(content=f"""{state['user_query']}""")]
    # LLM and Prompt Setting ===========================================================================================
    llm = get_llm(
        state['provider'],
        state['model_name'],
        **state['model_config'])
    prompt = load_prompt('braincrash_chat_model/prompts/system_prompt.md')
    prompt = prompt.format(TODAY=date.today().isoformat())
    human_message = HumanMessage(content=f"""User Query: {state['user_query']}\nYour Response:\n""")
    messages = [SystemMessage(content=prompt)] + state['messages'] + [human_message]

    # Tool Setting =====================================================================================================
    search = GoogleSerperAPIWrapper()
    search_tool = Tool(
        name="WebSearch",
        func=search.run,
        # coroutine=search.arun,
        description="Search web for the latest information. This tool MUST be used when referring to financial data like stock prices, market data, or any real-time information. For Korean stocks, search with company name and '주가' or '현재가'. Always use this tool first before making any price-related statements.",
    )

    agent = create_react_agent(llm, [search_tool])
    async for event in agent.astream(
            {
                "messages": export_messages_to_tuples(messages)
            },
            stream_mode="values"
            # stream_mode="custom"  # stream_mode="values"
    ):
        try:
            new_msg = event["messages"][-1]
        except Exception as e:
            continue
        else:
            if not isinstance(new_msg, HumanMessage):
                output_messages.append(new_msg)
    return {"messages": output_messages}
