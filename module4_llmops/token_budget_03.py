import sys, tiktoken
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.llm_client import LLMClient

ENCODING = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages: list[dict]) -> int:
    """Ước lượng số token của 1 list messages (kiểu chat)."""
    total_tk = 0
    for msg in messages:
        total_tk += len(ENCODING.encode(msg["content"]))
        total_tk += 4  # overhead ước lượng cho mỗi message (role, định dạng...)
    return total_tk

def trim_history(messages: list[dict], max_tokens: int) -> list[dict]:
    """Cắt bớt message cũ nhất (giữ system nếu có) tới khi tổng token <= max_tokens."""
    if not messages:
        return messages

    has_system = messages[0]["role"] == "system"
    system_prompt = [messages[0]] if has_system else []
    history = messages[1:] if has_system else list(messages)

    # bỏ dần message cũ nhất (đầu list) cho tới khi đạt budget
    while history and count_tokens(system_prompt + history) > max_tokens:
        history.pop(0)

    return system_prompt + history


if __name__ == "__main__":
    # giả lập 1 agent loop dài: system + nhiều turn user/assistant
    messages = [{"role": "system", "content": "Bạn là trợ lý kỹ thuật."}]
    for i in range(15):
        messages.append({"role": "user", "content": f"Câu hỏi số {i}: giải thích index database là gì và tại sao cần nó, cho ví dụ."})
        messages.append({"role": "assistant", "content": f"Trả lời số {i}: index giúp tra cứu nhanh hơn bằng cách..." * 5})

    est = count_tokens(messages)
    print(f"ước lượng trước khi gọi: {est} token, {len(messages)} messages")

    trimmed = trim_history(messages, max_tokens=500)
    print(f"sau khi cắt (budget=500): {count_tokens(trimmed)} token, {len(trimmed)} messages")
    print("system còn giữ:", trimmed[0]["content"])
    print("message đầu tiên còn lại (sau system):", trimmed[1]["content"][:50])

    # so sánh ước lượng vs thật
    llm = LLMClient()
    r = llm.chat(trimmed, max_tokens=8_000)
    print(f"\nước lượng: {count_tokens(trimmed)} | thật (usage.prompt_tokens): {r.prompt_tokens}")