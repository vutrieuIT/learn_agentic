import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.llm_client import LLMClient

CHEAP_MODEL = "openai/gpt-oss-20b"
STRONG_MODEL = "openai/gpt-oss-120b"

def route(task: str) -> str:
    """Rule-based: trả về tên model dựa trên độ khó ước lượng của task."""
    # TODO: tự viết heuristic, ví dụ:
    # - độ dài task
    # - có chứa từ khóa kiểu "so sánh", "phân tích", "vì sao", "chứng minh" -> STRONG
    # - câu hỏi tra cứu đơn giản, 1 fact -> CHEAP
    hard_keys = ["so sánh", "phân tích", "vì sao", "chứng minh"]
    is_hard = any(key in task.lower() for key in hard_keys)
    return STRONG_MODEL if is_hard else CHEAP_MODEL 
    # raise NotImplementedError

TASKS = [
    "Thủ đô Pháp là gì?",                                  # đơn giản
    "So sánh ưu nhược điểm giữa pgvector và Qdrant khi dữ liệu > 10 triệu vector, giải thích từng bước.",  # khó
    # đơn giản
    "html, css, js là gì?",
    # khó
    "vì sao database khi có nhiều record cần phải dùng index, có bao nhiêu loại, công dụng từng loại"
]

if __name__ == "__main__":
    MAX_TK = 8_000
    llm_routed = LLMClient(max_tokens=MAX_TK)
    llm_always_strong = LLMClient(model=STRONG_MODEL, max_tokens=MAX_TK)

    for t in TASKS:
        chosen = route(t)
        r = llm_routed.ask(t, model=chosen)
        print(f"[route={chosen}] {t[:40]}{'...' if len(t) > 40 else ''} -> {r[:60]}{'...' if len(r) > 40 else ''}")

    # gọi tất cả bằng STRONG_MODEL để so sánh cost
    for t in TASKS:
        llm_always_strong.ask(t)

    print("\n-- cost nếu route thông minh --")
    print(llm_routed.usage)
    print("-- cost nếu luôn dùng model mạnh --")
    print(llm_always_strong.usage)