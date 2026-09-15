"""Interactive terminal chat with the Sift agent.

Run with: uv run python main.py
"""

from app.agent.loop import run_agent


def main():
    print("Sift — ask a question about retrieval, NLP, or agents research.")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        result = run_agent(question)

        print(f"\nSift: {result['answer']}\n")
        if result.get("incomplete"):
            print("(note: hit the iteration cap before finishing)\n")


if __name__ == "__main__":
    main()
