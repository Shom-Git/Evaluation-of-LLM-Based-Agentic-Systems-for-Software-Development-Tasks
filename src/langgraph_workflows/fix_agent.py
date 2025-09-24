# main workflow (building graph)

import os, time
from pathlib import Path
from typing import Dict
from nodes.llm_node import llm_node
from nodes.sandbox_runner import run_in_sandbox
from nodes.react_nodes import (
    thinking_node, 
    observation_node, 
    reasoning_node, 
    action_node, 
    workflow_decision_node
)
from langgraph_workflows.react_graph import build_react_agent_graph


BASE_DIR = Path("/home/coder/project/experiments")
# For Linux environments, you can also use: Path("/tmp/experiments") or Path.home() / "experiments"
MAX_STEPS = 3

def _make_task_dir(task_id: str):
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = BASE_DIR / f"{task_id}_{ts}"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def run_react_workflow(state: Dict) -> Dict:
    """
    Run a single iteration of the ReAct workflow using LangGraph StateGraph.
    """
    graph = build_react_agent_graph()
    state = graph.invoke(state)
    return state

def run_fix_agent_for_example(buggy: str, tests: str, task_id="task", task_prompt: str = "") -> Dict:
    task_dir = _make_task_dir(task_id)
    state = {
        "buggy_code": buggy,
        "tests": tests,
        "history": [],
        "task_prompt": task_prompt,
        "task_dir": task_dir,
        "attempt": 0
    }

    for attempt in range(MAX_STEPS):
        state["attempt"] = attempt
        # Reset per-attempt flags for ReAct workflow
        state.update({
            "thinking_complete": False,
            "observation_complete": False,
            "reasoning_complete": False,
            "action_complete": False,
            "rule_based_fix": False
        })
        # Run the ReAct workflow
        state = run_react_workflow(state)
        candidate = state["candidate_code"]
        # Run candidate in sandbox
        result = state.get("test_result", {})
        # Collect reasoning from all ReAct steps
        reasoning_parts = []
        if state.get("code_analysis"):
            reasoning_parts.append(f"ANALYSIS: {'; '.join(state['code_analysis'])}")
        if state.get("observations"):
            reasoning_parts.append(f"OBSERVATIONS: {'; '.join(state['observations'])}")
        if state.get("fix_strategy"):
            reasoning_parts.append(f"STRATEGY: {'; '.join(state['fix_strategy'])}")
        if state.get("reasoning"):
            reasoning_parts.append(f"LLM REASONING: {state['reasoning']}")
        combined_reasoning = "\n".join(reasoning_parts)
        # Log attempt with comprehensive reasoning
        state["history"].append({
            "attempt": attempt,
            "passed": result.get("passed", False),
            "log": result.get("log", "")[:1000],
            "candidate_code": candidate,
            "reasoning": combined_reasoning,
            "rule_based_fix": state.get("rule_based_fix", False)
        })
        # Save log to file
        log_file = Path(task_dir) / f"cand_{attempt}.log"
        with open(log_file, "w") as f:
            f.write(result.get("log", ""))
        # Save candidate file (already done in run_in_sandbox)
        if result.get("passed", False):
            state.update(final_status="solved", final_file=result.get("candidate_file", None), task_dir=task_dir)
            return state
    state.update(final_status="unsolved", task_dir=task_dir)
    return state