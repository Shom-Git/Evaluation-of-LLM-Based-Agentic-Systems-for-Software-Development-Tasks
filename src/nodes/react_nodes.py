# ReAct workflow nodes for graph-based reasoning
from typing import Dict, Any
import re

def thinking_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node for analyzing the buggy code and identifying potential issues.
    """
    buggy_code = state.get("buggy_code", "")
    tests = state.get("tests", "")
    task_prompt = state.get("task_prompt", "")
    
    # Simple analysis without LLM - identify common patterns
    analysis = []
    
    # Check for common bug patterns
    if "return" not in buggy_code:
        analysis.append("Missing return statement")
    
    if "+" in buggy_code and "mul" in buggy_code.lower():
        analysis.append("Possible operator error: using + instead of *")
    
    if "-" in buggy_code and ("add" in buggy_code.lower() or "sum" in buggy_code.lower()):
        analysis.append("Possible operator error: using - instead of +")
        
    # Extract function name and parameters
    func_match = re.search(r"def\s+(\w+)\s*\((.*?)\)", buggy_code)
    if func_match:
        func_name = func_match.group(1)
        params = func_match.group(2)
        analysis.append(f"Function: {func_name} with parameters: {params}")
    
    thinking_result = {
        "code_analysis": analysis,
        "function_info": func_match.groups() if func_match else None,
        "thinking_complete": True
    }
    
    return {**state, **thinking_result}


def observation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node for observing test failures and error messages from previous attempts.
    """
    history = state.get("history", [])
    tests = state.get("tests", "")
    
    observations = []
    
    # Analyze test requirements
    if "assert" in tests:
        test_lines = [line.strip() for line in tests.split('\n') if line.strip().startswith('assert')]
        observations.append(f"Found {len(test_lines)} test assertions")
        
        for test_line in test_lines[:3]:  # Analyze first 3 tests
            observations.append(f"Test requirement: {test_line}")
    
    # Analyze previous failures if any
    if history:
        last_attempt = history[-1]
        if not last_attempt.get("passed", False):
            error_log = last_attempt.get("log", "")
            if "SyntaxError" in error_log:
                observations.append("Previous attempt had syntax errors")
            elif "AssertionError" in error_log:
                observations.append("Previous attempt failed test assertions")
            elif "NameError" in error_log:
                observations.append("Previous attempt had undefined variables")
            elif "TypeError" in error_log:
                observations.append("Previous attempt had type errors")
    
    observation_result = {
        "observations": observations,
        "test_count": len([line for line in tests.split('\n') if 'assert' in line]),
        "observation_complete": True
    }
    
    return {**state, **observation_result}


def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node for reasoning about the fix strategy based on analysis and observations.
    """
    code_analysis = state.get("code_analysis", [])
    observations = state.get("observations", [])
    buggy_code = state.get("buggy_code", "")
    
    reasoning = []
    fix_strategy = []
    
    # Combine analysis and observations to create reasoning
    reasoning.append("ANALYSIS: " + "; ".join(code_analysis))
    reasoning.append("OBSERVATIONS: " + "; ".join(observations))
    
    # Determine fix strategy based on common patterns
    if any("operator error" in analysis for analysis in code_analysis):
        if "using + instead of *" in str(code_analysis):
            fix_strategy.append("Replace + with * for multiplication")
        elif "using - instead of +" in str(code_analysis):
            fix_strategy.append("Replace - with + for addition")
    
    if any("syntax error" in obs.lower() for obs in observations):
        fix_strategy.append("Fix syntax errors in code structure")
    
    if any("assertion" in obs.lower() for obs in observations):
        fix_strategy.append("Ensure function logic matches test expectations")
    
    if not fix_strategy:
        fix_strategy.append("Analyze function logic step by step")
    
    reasoning_result = {
        "reasoning_steps": reasoning,
        "fix_strategy": fix_strategy,
        "reasoning_complete": True
    }
    
    return {**state, **reasoning_result}


def action_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node for applying the fix strategy and generating corrected code.
    """
    buggy_code = state.get("buggy_code", "")
    fix_strategy = state.get("fix_strategy", [])
    
    # Apply simple rule-based fixes
    corrected_code = buggy_code
    
    # Apply operator fixes
    if "Replace + with * for multiplication" in fix_strategy:
        corrected_code = re.sub(r'\breturn\s+([^+]+)\s*\+\s*([^+]+)', r'return \1 * \2', corrected_code)
    
    if "Replace - with + for addition" in fix_strategy:
        corrected_code = re.sub(r'\breturn\s+([^-]+)\s*-\s*([^-]+)', r'return \1 + \2', corrected_code)
    
    # If no rule-based fix was applied, the LLM node will handle it
    action_result = {
        "candidate_code": corrected_code,
        "rule_based_fix": corrected_code != buggy_code,
        "action_complete": True
    }
    
    return {**state, **action_result}


def should_use_llm(state: Dict[str, Any]) -> bool:
    """
    Decision function to determine if LLM is needed.
    """
    # Use LLM if rule-based fix wasn't successful
    return not state.get("rule_based_fix", False)


def workflow_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decision node to determine next step in workflow.
    """
    # Check if all ReAct steps are complete
    thinking_done = state.get("thinking_complete", False)
    observation_done = state.get("observation_complete", False) 
    reasoning_done = state.get("reasoning_complete", False)
    action_done = state.get("action_complete", False)
    
    if not thinking_done:
        next_step = "thinking"
    elif not observation_done:
        next_step = "observation"  
    elif not reasoning_done:
        next_step = "reasoning"
    elif not action_done:
        next_step = "action"
    elif should_use_llm(state):
        next_step = "llm"
    else:
        next_step = "execute"
    
    return {**state, "next_step": next_step}