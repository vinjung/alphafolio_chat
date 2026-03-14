from .types import BrainCrashGraphState
from langgraph.graph import StateGraph, START, END
from .nodes import main_node

workflow = StateGraph(BrainCrashGraphState)
workflow.add_node("main", main_node)
workflow.add_edge(START, "main")
workflow.add_edge("main", END)
braincrash_graph = workflow.compile()
