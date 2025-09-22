
import re
from typing import Dict, List
import torch
from transformers import pipeline

MODEL_ID = "Qwen/Qwen3-0.6B"

# Use Hugging Face pipeline for chat models
pipe = pipeline(
    "text-generation",
    model=MODEL_ID,
    dtype=torch.bfloat16,
    device_map="auto"
)


def build_prompt(buggy_code: str, tests: str, history: List[Dict]) -> str:
    """
    Build the text prompt that will be sent to the LLM.
    Includes buggy code, tests, and results of previous attempts.
    """
    # Build chat-style messages for the pipeline
    system_content = (
        "You are a professional Python developer. "
        "You write fully working Python code, even for small models, "
        "and you clearly explain any bugs in the code. "
        "Always provide executable code first, then a brief explanation of the bug and the fix."
    )
    user_content = (
        f"Here is a Python function that contains a bug:\n\n{buggy_code}\n\n"
        "Please do the following:\n"
        "1. Correct the code so it works as intended.\n"
        "2. Provide the corrected, fully executable code first.\n"
        "3. After the code, write a short explanation of what was wrong and how you fixed it.\n"
        "Only modify the code as necessary."
    )
    # Optionally, add history and error logs to user_content for multi-step reasoning
    if history:
        for h in history:
            user_content += f"\n\nAttempt {h['attempt']} - Passed: {h['passed']}\nCandidate code:\n{h.get('candidate_code','')}\nError log:\n{h['log']}\n"
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    return messages


def extract_code(output: str, prompt: str) -> str:
    """
    Extract only Python code from LLM output.
    Supports ```python ... ``` fenced blocks and raw def statements.
    """
    # Сначала ищем блок ```python ... ```
    m = re.search(r"```python(.*?)```", output, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    
    # Потом любой блок с ```
    m = re.search(r"```(.*?)```", output, re.DOTALL)
    if m:
        return m.group(1).strip()
    
    # Ищем функцию def
    m = re.search(r"(def\s+\w+\s*\(.*)", output, re.DOTALL)
    if m:
        return m.group(1).strip()
    
    # Если вывод начинается с промпта, убираем его
    if output.startswith(prompt):
        return output[len(prompt):].strip()
    
    return output.strip()


def llm_node(state: Dict) -> Dict:
    """
    Main entry point for the LLM node.
    Takes current agent state, builds prompt, calls model,
    and extracts candidate fixed code.
    """
    messages = build_prompt(state["buggy_code"], state["tests"], state.get("history", []))
    prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    outputs = pipe(prompt, max_new_tokens=512, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
    decoded = outputs[0]["generated_text"]
    candidate = extract_code(decoded, prompt)
    return {**state, "candidate_code": candidate, "llm_raw_output": decoded}


# Для тестирования
if __name__ == "__main__":
    # Пример использования
    test_state = {
        "buggy_code": "def add(a, b):\n    return a - b",
        "tests": "assert add(2, 3) == 5\nassert add(0, 0) == 0",
        "history": []
    }
    
    result = llm_node(test_state)
    print("Candidate code:")
    print(result["candidate_code"])