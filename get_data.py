from datasets import load_dataset
import json

# Загружаем Python-подмножество
dataset = load_dataset("bigcode/humanevalpack", split="test")

# Сохраняем в файл humanevalpack_python.jsonl в текущей папке
with open("humanevalpack_python.jsonl", "w") as f:
    for item in dataset:
        # Каждая строка — отдельный JSON объект
        f.write(json.dumps(item) + "\n")

print("Сохранено в humanevalpack_python.jsonl")
