import argparse
from langgraph_workflows.fix_agent import build_fix_agent


def run_single():
    agent = build_fix_agent()
    state = {
        "buggy_code": "def mul(a, b):\n    return a + b\n",
        "tests": "assert mul(2, 3) == 6"
    }
    result = agent.invoke(state)
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["single", "eval"], default="single")
    args = parser.parse_args()

    if args.mode == "single":
        run_single()
    else:
        print("Evaluation mode not implemented yet")
