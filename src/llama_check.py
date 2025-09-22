import torch
from transformers import pipeline

pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", dtype=torch.bfloat16, device_map="auto")


messages = [
    {
        "role": "system",
        "content": (
            "You are a professional Python developer. "
            "You write fully working Python code, even for small models, "
            "and you clearly explain any bugs in the code. "
            "Always provide executable code first, then a brief explanation of the bug and the fix."
        ),
    },
    {
        "role": "user",
        "content": (
            "Here is a Python function that contains a bug:\n\n"
            "def add(a, b):\n"
            "    return a - b\n\n"
            "Please do the following:\n"
            "1. Correct the code so it works as intended.\n"
            "2. Provide the corrected, fully executable code first.\n"
            "3. After the code, write a short explanation of what was wrong and how you fixed it.\n"
            "Only modify the code as necessary."
        ),
    },
]
prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
outputs = pipe(prompt, max_new_tokens=256, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
print(outputs[0]["generated_text"])