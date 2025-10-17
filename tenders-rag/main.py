import src.agent


def main():
    print("[*] Initializing Romeo-the-Agent...")
    print("=" * 60)
    agent = src.agent.Agent()
    print("=" * 60)
    print("[OK] Agent ready! Ask me about Romeo and Juliet!\n")
    
    while True:
        user_text = input("You: ")
        if not user_text.strip():
            continue
        answer = agent.run_turn(user_text)
        print(f"\nAgent: {answer}\n")

if __name__ == "__main__":
    main()
