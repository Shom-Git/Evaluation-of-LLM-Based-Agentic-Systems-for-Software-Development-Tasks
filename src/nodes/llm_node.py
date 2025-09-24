#LLm node with ReAct-style reasoning for code debugging
import re
from typing import Dict, List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig

MODEL_ID = "bigcode/starcoder2-3b"

bnb_config = BitsAndBytesConfig(load_in_8bit=True)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    quantization_config=bnb_config
)
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer
)

def build_prompt(buggy_code: str, tests: str, history: List[Dict], task_prompt: str = "") -> str:
    """
    Build ReAct-style prompt for iterative code debugging.
    """
    system_content = (
        "You are an expert Python debugger and software engineer. Your task is to fix buggy Python code.\n\n"
        "CRITICAL RULES:\n"
        "1. ALWAYS provide complete, working Python code - never use placeholders\n"
        "2. Your code must be syntactically correct and executable\n"
        "3. Never write '[corrected code here]', '[your code here]', or similar placeholders\n"
        "4. Include proper indentation and complete function definitions\n"
        "5. Test your logic mentally before writing the code\n\n"
        "METHODOLOGY - Follow ReAct approach:\n"
        "1. THINK: Analyze the code structure and logic carefully\n"
        "2. OBSERVE: Study the test cases to understand expected behavior\n"
        "3. REASON: Identify the specific bug and plan the fix\n"
        "4. ACT: Write the complete corrected function\n\n"
        "Remember: Tests show the expected behavior - make your code match that behavior exactly."
    )
    
    # Build the user content with the task description
    user_content = ""
    if task_prompt:
        user_content += f"TASK DESCRIPTION:\n{task_prompt}\n\n"
    
    user_content += f"""BUGGY CODE:
```python
{buggy_code}
```

TESTS:
```python
{tests}
```
"""

    # Add ReAct-style reasoning from previous attempts
    if history:
        user_content += "\n=== PREVIOUS DEBUGGING ATTEMPTS ===\n"
        for h in history:
            user_content += f"\n--- Attempt {h['attempt']} ---\n"
            user_content += f"Status: {'PASSED' if h['passed'] else 'FAILED'}\n"
            if h.get('candidate_code'):
                user_content += f"Code tried:\n```python\n{h['candidate_code']}\n```\n"
            if h.get('log') and not h['passed']:
                user_content += f"Error observed:\n{h['log'][:500]}...\n"  # Limit error log length
            if h.get('reasoning'):
                user_content += f"Previous reasoning: {h['reasoning']}\n"
        # Add explicit feedback for the LLM
        last = history[-1]
        user_content += ("\nFEEDBACK: The previous attempt failed. "
                         "Check the error and the code you generated above. "
                         "Think carefully about why the error occurred and how to fix it. "
                         "Try to make the code pass all the tests for the task above.\n")

    user_content += """
=== YOUR TASK ===
Use the ReAct approach to fix the code:

THINK: Analyze the buggy code step by step. What is the intended functionality?
OBSERVE: What do the test failures and error messages tell us?
REASON: Why does this bug occur? What specific changes are needed?
ACT: Provide the COMPLETE corrected Python function.

IMPORTANT: 
- Your response must contain actual working Python code
- Never use placeholders like "[corrected code here]" or "[your code here]"
- Make sure the code is syntactically correct and follows Python standards
- Include all necessary imports and complete function definitions

Format your response exactly like this:
THINK: [Your analysis here]
OBSERVE: [What you observe from tests/errors]  
REASON: [Why the bug occurs and your fix strategy]
ACT:
```python
def function_name(...):
    # Complete working code here
    pass
```
"""
    
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]


def extract_code_and_reasoning(llm_output: str) -> Tuple[str, str]:
    """
    Extract code and reasoning from LLM output using ReAct format.
    """
    # Extract reasoning sections
    think_match = re.search(r"THINK:\s*(.*?)(?=OBSERVE:|REASON:|ACT:|$)", llm_output, re.DOTALL | re.IGNORECASE)
    observe_match = re.search(r"OBSERVE:\s*(.*?)(?=THINK:|REASON:|ACT:|$)", llm_output, re.DOTALL | re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.*?)(?=THINK:|OBSERVE:|ACT:|$)", llm_output, re.DOTALL | re.IGNORECASE)
    
    reasoning_parts = []
    if think_match:
        reasoning_parts.append(f"THINK: {think_match.group(1).strip()}")
    if observe_match:
        reasoning_parts.append(f"OBSERVE: {observe_match.group(1).strip()}")
    if reason_match:
        reasoning_parts.append(f"REASON: {reason_match.group(1).strip()}")
    
    reasoning = "\n".join(reasoning_parts)
    
    # Extract code from ACT section or code blocks with multiple patterns
    code_patterns = [
        r"ACT:\s*```python\s*(.*?)```",  # ACT: ```python ... ```
        r"ACT:\s*```\s*(.*?)```",        # ACT: ``` ... ```
        r"```python\s*(.*?)```",         # ```python ... ```
        r"```\s*(def\s+.*?)```",         # ``` def ... ```
        r"ACT:\s*(def\s+.*?)(?=\n\s*\n|\Z)",  # ACT: def ... (without code blocks)
    ]

    code = ""
    for pattern in code_patterns:
        match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE)
        if match:
            code = match.group(1).strip()
            break

    # Enhanced fallback: extract any function definition
    if not code or code == "[corrected code here]" or "corrected code here" in code.lower():
        function_matches = re.findall(r"(def\s+\w+.*?)(?=\ndef\s|\n\n|\Z)", llm_output, re.DOTALL)
        if function_matches:
            # Take the last/most complete function definition
            code = function_matches[-1].strip()

    # Final validation and cleanup
    if not code or "[" in code and "corrected" in code.lower():
        # If still no valid code, try to find any reasonable Python code block
        lines = llm_output.split('\n')
        code_lines = []
        in_code = False
        for line in lines:
            if line.strip().startswith('def '):
                in_code = True
                code_lines = [line]
            elif in_code:
                if line.strip() == '' or line.startswith('    ') or line.startswith('\t'):
                    code_lines.append(line)
                else:
                    break
        
        if code_lines:
            code = '\n'.join(code_lines).strip()

    return code, reasoning


def llm_node(state: Dict) -> Dict:
    """
    Main entry point for the LLM node with ReAct-style reasoning.
    """
    # Get task prompt from history if available
    task_prompt = ""
    if state.get("history") and state["history"]:
        task_prompt = state["history"][-1].get("prompt", "")
    elif "task_prompt" in state:
        task_prompt = state["task_prompt"]
    
    messages = build_prompt(
        state["buggy_code"], 
        state["tests"], 
        state.get("history", []),
        task_prompt
    )
    
    # For StarCoder2-3B, use plain string prompt (not chat template)
    prompt = messages[1]["content"]
    outputs = pipe(
        prompt,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.3,
        top_k=50,
        top_p=0.95,
        pad_token_id=pipe.tokenizer.eos_token_id
    )
    # Extract the generated response (remove the input prompt)
    full_response = outputs[0]["generated_text"]
    generated_response = full_response[len(prompt):].strip()
    
    # Extract both code and reasoning from ReAct output
    candidate, reasoning = extract_code_and_reasoning(generated_response)
    
    # Validation: ensure we have actual code
    if not candidate or candidate == "[corrected code here]" or len(candidate.strip()) < 10:
        # Fallback: create a minimal valid function if extraction failed
        candidate = """def placeholder_function():
    # LLM failed to generate proper code
    pass"""
        reasoning += "\n[ERROR: LLM failed to generate proper code, using placeholder]"
    
    return {
        **state, 
        "candidate_code": candidate, 
        "llm_raw_output": generated_response,
        "reasoning": reasoning
    }
