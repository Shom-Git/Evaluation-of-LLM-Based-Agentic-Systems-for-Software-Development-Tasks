from langgraph.graph import StateGraph, START, END
from nodes.llm_node import llm_node
from nodes.sandbox_runner import run_in_sandbox
from nodes.react_nodes import thinking_node, observation_node, reasoning_node, action_node


# Sandbox node using dict-style state
def sandbox_node(state: dict) -> dict:
    candidate = state.get("candidate_code", "")
    tests = state.get("tests", "")
    attempt = state.get("attempt", 0)
    output_dir = state.get("task_dir", "")

    result = run_in_sandbox(candidate, tests, attempt, output_dir)
    state["test_result"] = result
    return state


# Build the ReAct-style agent graph
def build_react_agent_graph():
    graph = StateGraph(dict)  # use dict schema

    # Register nodes
    graph.add_node("thinking", thinking_node)
    graph.add_node("observation", observation_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("action", action_node)
    graph.add_node("llm", llm_node)
    graph.add_node("sandbox", sandbox_node)

    # Wire up edges
    graph.add_edge("thinking", "observation")
    graph.add_edge("observation", "reasoning")
    graph.add_edge("reasoning", "action")
    graph.add_edge("action", "llm")
    graph.add_edge("llm", "sandbox")

    # Define start and end
    graph.add_edge(START, "thinking")
    graph.add_edge("sandbox", END)

    # Compile the graph so it’s runnable
    return graph.compile()