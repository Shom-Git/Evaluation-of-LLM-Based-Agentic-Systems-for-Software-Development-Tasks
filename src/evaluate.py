import json


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


if __name__ == "__main__":
    dataset_path = "/home/coder/project/data/humanevalpack_python.jsonl"
    tasks = list(load_dataset(dataset_path))

    print(f"Loaded {len(tasks)} tasks from {dataset_path}")
    print("First example:", tasks[0])
