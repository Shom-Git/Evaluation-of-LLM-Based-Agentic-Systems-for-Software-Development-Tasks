import re
from typing import Dict, List
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_ID = "Qwen/Qwen3-0.6B"

# Load tokenizer and model (on GPU if available)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto")


def build_prompt(buggy_code: str, tests: str, history: List[Dict]) -> str:
    """
    Build the text prompt that will be sent to the LLM.
    Includes buggy code, tests, and results of previous attempts.
    """
    history_txt = []
    if history:
        for h in history:
            status = "PASSED" if h["passed"] else "FAILED"
            log = h["log"].splitlines()[:3]  # take first 3 lines of log
            history_txt.append(f"Attempt {h['attempt']}: {status}\n" + "\n".join(log))
    else:
        history_txt.append("No previous attempts.")

    # Собираем полный промпт с историей
    history_section = "\n".join(history_txt)
    
    return f"""You are a Python expert.
Fix the buggy code so that it passes the tests.

Buggy code:
```python
{buggy_code}
```

Tests:
```python
{tests}
```

History:
{history_section}

Output ONLY the fixed function inside a Python code block:
```python
<your_code_here>
```"""


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
    prompt = build_prompt(state["buggy_code"], state["tests"], state.get("history", []))

    # Encode prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Run generation
    out = model.generate(**inputs, max_new_tokens=512, do_sample=False)

    # Decode and extract candidate code
    decoded = tokenizer.decode(out[0], skip_special_tokens=True)
    candidate = extract_code(decoded, prompt)

    # Return updated state
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