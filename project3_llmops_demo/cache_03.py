import sys, hashlib, logging
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import redis
from shared.llm_client import LLMClient

log = logging.getLogger("cache")
r = redis.Redis(host="localhost", port=6380, decode_responses=True)

CACHE_TTL = 3600  # giây

def _cache_key(model: str, prompt: str) -> str:
    raw = f"{model}:{prompt}"
    return "llmcache:" + hashlib.sha256(raw.encode()).hexdigest()

def ask_cached(llm: LLMClient, prompt: str) -> tuple[str, bool]:
    """Trả về (content, is_cache_hit)."""
    key = _cache_key(llm.model, prompt)
    cached = r.get(key)
    if cached is not None:
        log.info("cache HIT: %s", key[:16])
        return cached, True

    result = llm.ask(prompt)
    r.set(key, result, ex=CACHE_TTL)
    log.info("cache MISS, đã lưu: %s", key[:16])
    return result, False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    local_llm = LLMClient(model="qwen2.5:3b", base_url="http://localhost:11434/v1", api_key="ollama")

    prompt = "Thủ đô Pháp là gì?"
    r1, hit1 = ask_cached(local_llm, prompt)
    r2, hit2 = ask_cached(local_llm, prompt)  # hỏi lại y hệt -> phải cache HIT

    print(f"lần 1: hit={hit1}")
    print(f"lần 2: hit={hit2}")
    print(local_llm.usage)  # kỳ vọng chỉ có 1 call thật (lần 2 không gọi model)