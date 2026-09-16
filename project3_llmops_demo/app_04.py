import sys, uuid, hashlib, logging
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import redis
from shared.llm_client import LLMClient
from module4_llmops.observability_04 import traced_call

log = logging.getLogger("app")
r = redis.Redis(host="localhost", port=6380, decode_responses=True)
CACHE_TTL = 3600

local_llm = LLMClient(model="qwen2.5:3b", base_url="http://localhost:11434/v1", api_key="ollama")
api_llm = LLMClient(model="openai/gpt-oss-20b")

def route(task: str) -> LLMClient:
    hard_keys = ["so sánh", "phân tích", "vì sao", "chứng minh"]
    return api_llm if any(k in task.lower() for k in hard_keys) else local_llm

def _cache_key(model: str, prompt: str) -> str:
    return "llmcache:" + hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

def ask(task: str, trace_id: str) -> str:
    primary = route(task)
    fallback = api_llm if primary is local_llm else local_llm
    tag = "local" if primary is local_llm else "api"

    key = _cache_key(primary.model, task)
    cached = r.get(key)
    if cached is not None:
        return cached  # cache hit -> không gọi model, không cần trace

    messages = [{"role": "user", "content": task}]
    try:
        result = traced_call(primary, messages, trace_id, span_name=f"router:{tag}")
        r.set(key, result.content, ex=CACHE_TTL)
        return result.content
    except Exception:
        fb_tag = "api" if tag == "local" else "local"
        result = traced_call(fallback, messages, trace_id, span_name=f"fallback:{fb_tag}")
        r.set(_cache_key(fallback.model, task), result.content, ex=CACHE_TTL)
        return result.content

TASKS = [
    "Thủ đô Pháp là gì?",
    "So sánh ưu nhược điểm giữa pgvector và Qdrant khi dữ liệu > 10 triệu vector.",
    "Thủ đô Pháp là gì?",   # lặp lại -> phải cache hit, không log trace
]

if __name__ == "__main__":
    for t in TASKS:
        ask(t, str(uuid.uuid4()))
