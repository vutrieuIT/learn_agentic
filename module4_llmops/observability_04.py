import sys, time, json, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from shared.llm_client import LLMClient, _cost

@dataclass
class TraceEvent:
    trace_id: str
    span_name: str          # vd "llm_call", "tool:get_distance"
    model: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float | None
    latency_s: float
    status: str              # "ok" | "error"
    error: str | None = None
    finish_reason: str | None = None

def log_event(event: TraceEvent):
    print(json.dumps(asdict(event), ensure_ascii=False))

def traced_call(llm: LLMClient, messages, trace_id, span_name="llm_call", **extra):
    t0 = time.perf_counter()
    try:
        r = llm.chat(messages, **extra)
        log_event(TraceEvent(
            trace_id=trace_id, span_name=span_name, model=r.model,
            prompt_tokens=r.prompt_tokens, completion_tokens=r.completion_tokens,
            cost_usd=_cost(r.model, r.prompt_tokens, r.completion_tokens),  # có thể tính lại bằng PRICING trong llm_client.py
            latency_s=time.perf_counter() - t0, status="ok", finish_reason=r.finish_reason
        ))
        return r
    except Exception as e:
        log_event(TraceEvent(
            trace_id=trace_id, span_name=span_name, model=None,
            prompt_tokens=None, completion_tokens=None, cost_usd=None,
            latency_s=time.perf_counter() - t0, status="error", error=str(e),
        ))
        raise

if __name__ == '__main__':
    llm = LLMClient()

    for i in range(2):                       # giả lập 2 request độc lập
        trace_id = str(uuid.uuid4())
        try:
            traced_call(llm, [{"role": "user", "content": f"câu hỏi {i} bước 1"}], trace_id, "step1")
            traced_call(llm, [{"role": "user", "content": f"câu hỏi {i} bước 2"}], trace_id, "step2")
        except Exception:
            pass  # đã log rồi, ở đây chỉ để demo không crash, request khác vẫn chạy tiếp

    # case lỗi cố ý, tách riêng để không làm hỏng vòng lặp trên
    try:
        traced_call(llm, [{"role": "user", "content": "x"}], str(uuid.uuid4()), "bad", max_tokens=-1)
    except Exception:
        pass