from agents.orchestrator import Orchestrator


def main():
    travel_agent = Orchestrator("gemini-2.5-flash", "google-genai", temperature=0)

    print("Chatbot du lịch khởi động! Gõ 'exit' để thoát.\n")

    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Tạm biệt! Hẹn gặp lại chuyến sau.")
            break

        response = travel_agent.run(question=user_input)
        print(f"Bot: {response}\n")

        # Manual memory management:
        # print(f"Tokens: {travel_agent.total_tokens}")
        # print("-" * 50)


if __name__ == "__main__":
    main()