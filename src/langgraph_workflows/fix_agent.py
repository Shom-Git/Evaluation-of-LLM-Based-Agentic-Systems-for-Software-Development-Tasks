# main workflow (building graph)

from langgraph.graph import StateGraph
from nodes.llm_node import llm_node
from nodes.run_tests_node import run_tests_node


def build_fix_agent():
    graph = StateGraph(dict)

    # Register nodes
    graph.add_node("llm", llm_node)
    graph.add_node("run_tests", run_tests_node)

    # Connect nodes
    graph.set_entry_point("llm")
    graph.add_edge("llm", "run_tests")

    return graph.compile()


if __name__ == "__main__":
    agent = build_fix_agent()

    # Example input
    example_state = {
        "buggy_code": "def add(a, b):\n    return a - b\n",
        "tests": "assert add(2, 3) == 5"
    }

    final_state = agent.invoke(example_state)

    print("=== Final State ===")
    print(final_state)
