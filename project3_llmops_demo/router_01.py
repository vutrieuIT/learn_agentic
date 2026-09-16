import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.llm_client import LLMClient

local_llm = LLMClient(model="qwen2.5:3b", base_url="http://localhost:11434/v1", api_key="ollama")
api_llm = LLMClient(model="openai/gpt-oss-20b", max_tokens=4096)  # mặc định Groq

def route(task: str) -> LLMClient:
    hard_keys = ["so sánh", "phân tích", "vì sao", "chứng minh"]
    is_hard = any(key in task.lower() for key in hard_keys)
    return api_llm if is_hard else local_llm

TASKS = [
    "Thủ đô Pháp là gì?",
    "So sánh ưu nhược điểm giữa pgvector và Qdrant khi dữ liệu > 10 triệu vector.",
]

if __name__ == "__main__":
    for t in TASKS:
        llm = route(t)
        r = llm.ask(t)
        tag = "LOCAL" if llm is local_llm else "API"
        print(f"[{tag}] {t[:40]} -> {r[:60]}...")

    print("\n-- usage local --")
    print(local_llm.usage)
    print("-- usage api --")
    print(api_llm.usage)