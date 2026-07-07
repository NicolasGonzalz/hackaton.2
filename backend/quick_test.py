from backend.core import qwen_client

if __name__ == "__main__":
    print("Sending one test request to Qwen Cloud...")
    result = qwen_client.chat(
        "You are a helpful assistant.",
        "Say 'Agent Society is connected to Qwen Cloud' and nothing else.",
    )
    print("\nResponse:", result["text"])
    print(f"Latency: {result['latency_s']:.2f}s")