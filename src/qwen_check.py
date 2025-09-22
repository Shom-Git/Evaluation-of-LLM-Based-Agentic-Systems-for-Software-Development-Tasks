import sys
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "google/codegemma-2b"

def ask_qwen_about_bug(buggy_code, max_words=250):
    prompt = f"""
You are a Python expert. Analyze the following buggy code fix it and explain in less than {max_words} words what is wrong with it. Then, rewrite the function in a correct way check the suntaxis and the logic of the function name.
Also write only ones the buggy code then what you think was wrong and then ones show the correct code 
Do not rewrite duggy code and coorect code several times just correct the code and show the correct codee

Buggy code:
```python
{buggy_code}

"""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=512, do_sample=False)
    decoded = tokenizer.decode(out[0], skip_special_tokens=True)
    print(decoded)

if __name__ == "__main__":
    buggy_code = "def add(a, b):\n    return a - b"
    ask_qwen_about_bug(buggy_code, max_words=200)
