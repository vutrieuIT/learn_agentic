import os, random, time, logging

from dataclasses import dataclass, field

from dotenv import load_dotenv, find_dotenv
from groq import (Groq, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError,
                  BadRequestError, APIStatusError)

load_dotenv(find_dotenv(), override=True)
log = logging.getLogger("llm_client")

# --- CONFIG ---
DEFAULT_MODEL = "openai/gpt-oss-20b"
RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)

# --- PRICE USD / 1M TOKEN ---
PRICING = { # mock price
    "openai/gpt-oss-20b":  {"in": 0.1, "out": 0.2},
    "qwen/qwen3.8-27b":    {"in": 0.3, "out": 0.4},
}

def _cost(model: str, prompt_tok: int, completion_tok: int) -> float:
    p = PRICING.get(model)
    if not p:
        return 0.0
    return (prompt_tok * p["in"] + completion_tok * p["out"]) / 1_000_000


def _backoff(attempt: int) -> float:
    return min(2 ** attempt, 30) + random.uniform(0, 1)


def _retry_after(ex) -> float | None:
    resp = getattr(ex, "response", None)
    if resp is None:
        return None
    val = resp.headers.get("retry-after")
    return float(val) if val else None

@dataclass
class LLMResult:
    content: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_s: float
    model: str

@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

    def add(self, r: LLMResult) -> None:
        self.calls += 1
        self.prompt_tokens += r.prompt_tokens
        self.completion_tokens += r.completion_tokens
        c = _cost(r.model, r.prompt_tokens, r.completion_tokens)
        self.cost_usd += c
        return c

    def __str__(self) -> str:
        return (f"{self.calls} calls | in={self.prompt_tokens} out={self.completion_tokens} "
                f"| ${self.cost_usd:.4f}")

class LLMClient:
    def __init__(self, model: str = DEFAULT_MODEL, *, temperature: float = 0,
                 max_tokens: int = 512, max_attempts: int = 5, api_key: str | None = None):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_attempts = max_attempts
        self._client = Groq(api_key=api_key or os.environ["GROQ_API_KEY"])
        self.usage = Usage()

    def chat(self, messages: list[dict], *, model: str | None = None,
             temperature: float | None = None, max_tokens: int | None = None,
             **extra) -> LLMResult:
        model = model or self.model
        temperature = self.temperature if temperature is None else temperature
        max_tokens = self.max_tokens if max_tokens is None else max_tokens

        for attempt in range(1, self.max_attempts + 1):
            t0 = time.perf_counter()
            try:
                resp = self._client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature,
                    max_tokens=max_tokens, **extra,
                )
            except (BadRequestError, APIStatusError) as e:
                log.error("bad request, không retry: %s", e)
                raise
            except RETRYABLE as e:
                if attempt == self.max_attempts:
                    log.error("bỏ cuộc sau %d lần: %s", self.max_attempts, e)
                    raise
                wait = _retry_after(e) or _backoff(attempt)
                log.warning("%s -> chờ %.1fs [%d/%d]", type(e).__name__, wait, attempt, self.max_attempts)
                time.sleep(wait)
                continue

            latency = time.perf_counter() - t0
            choice = resp.choices[0]
            u = resp.usage

            if (choice.finish_reason == "length"):
                if (choice.message.content or "").strip():      # CÓ content -> bị cắt giữa câu
                    log.warning("output bị cắt giữa chừng (max_tokens=%d)", max_tokens)
                else:                                            # RỖNG -> reasoning ăn hết
                    log.warning("content rỗng — reasoning ăn hết %d token, tăng max_tokens", max_tokens)

            result = LLMResult(
                content=choice.message.content or "",
                finish_reason=choice.finish_reason,
                prompt_tokens=u.prompt_tokens,
                completion_tokens=u.completion_tokens,
                total_tokens=u.total_tokens,
                latency_s=latency,
                model=model,
            )
            call_cost = self.usage.add(result)
            log.info("%s | in=%d out=%d | %.2fs | $%.5f (session $%.4f)", 
                     model, u.prompt_tokens, u.completion_tokens, latency, call_cost, self.usage.cost_usd)
            return result

        raise RuntimeError("unreachable")

    def ask(self, prompt: str, *, system: str | None = None, **kw) -> str:
        """Shortcut hỏi 1-shot, trả về mỗi content."""
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
        return self.chat(msgs, **kw).content


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    llm = LLMClient()

    print(llm.ask("Một câu: idempotency key để làm gì?"))
    print(llm.ask("Liệt kê 15 database.", max_tokens=100, reasoning_effort="low"))

    print("\n--- tổng session ---")
    print(llm.usage)