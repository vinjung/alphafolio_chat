from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def export_messages_to_tuples(messages):
    role_map = {
        SystemMessage: "system",
        HumanMessage: "user",
        AIMessage: "assistant"
    }

    return [(role_map.get(type(m), "unknown"), m.content) for m in messages]
