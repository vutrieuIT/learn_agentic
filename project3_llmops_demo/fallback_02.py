import sys, logging
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.llm_client import LLMClient

log = logging.getLogger("fallback")

local_llm = LLMClient(model="qwen2.5:3b", base_url="http://localhost:11434/v1", api_key="ollama")
api_llm = LLMClient(model="openai/gpt-oss-20b")

def route(task: str) -> LLMClient:
    hard_keys = ["so sánh", "phân tích", "vì sao", "chứng minh"]
    is_hard = any(key in task.lower() for key in hard_keys)
    return api_llm if is_hard else local_llm

def ask_with_fallback(task: str) -> str:
    primary = route(task)
    fallback = api_llm if primary is local_llm else local_llm
    primary_tag = "LOCAL" if primary is local_llm else "API"
    fallback_tag = "API" if primary is local_llm else "LOCAL"

    try:
        result = primary.ask(task)
        print(f"[{primary_tag}] ok")
        return result
    except Exception as e:
        log.warning("%s lỗi (%s: %s) -> fallback %s", primary_tag, type(e).__name__, e, fallback_tag)
        result = fallback.ask(task)
        print(f"[{fallback_tag}] (fallback từ {primary_tag}) ok")
        return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    print(ask_with_fallback("Thủ đô Pháp là gì?"))