import sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.llm_client import LLMClient

# --- CASE 1: có kết quả rõ ràng
CLASSIFY_CASES = [
    {"input":"server sập, không truy cập được production", "expected":"urgent"},
    {"input":"xin hỏi cách đổi mật khẩu", "expected":"normal"},
    {"input":"App load chậm hơn bình thường một chút", "expected":"normal"}
]

def classify_priority(llm: LLMClient, message: str):
    prompt = f'phân loại mức ưu tiên ticket sau là "urgent"  hoặc "normal", chỉ trả lời đúng 1 từ.\n ticket:{message}'
    return llm.ask(prompt=prompt).strip().lower()

def run_assertion_eval(llm : LLMClient) -> float:
    correct = 0
    for case in CLASSIFY_CASES:
        pred = classify_priority(llm, case['input'])
        ok = case['expected'] == pred
        correct += ok
        print(f"[{'OK' if ok else 'FAIL'}] {case['input'][:35]!r} expected={case['expected']} got={pred}")
    acc = correct / len(CLASSIFY_CASES)
    print(f"Assertion accuracy: {acc:.2%}")
    return acc

# CASE 2: llm - as - judge

SUMMARY_CASES = [
    {
        "input": """connection pool là tập hợp các kết nối database được giữ sẵn và tái sử dụng
        thay vì mở/đóng kết nối mới cho mỗi request, giúp giảm overhead handshake TCP+auth"""
    }
]

JUDGE_PROMPT = """
bạn là giám khảo chấm bản tóm tắt.
văn bản gốc:
{source}

bản tóm tắt cần chấm:
{summary}

chấm theo 2 tiêu chí, thang 1 - 5 điểm / tiêu chí:
- faithfulness: tóm tắt có bịa thông tin không có trong văn bản không (5 điểm = không bịa gì)
- relevance: tóm tắt có giữ đúng ý chính không (5 điểm = đầy đủ ý chính)

chỉ trả JSON, KHÔNG thêm chữ nào khác: {{"faithfulness": <int>, "relevance": <int>, "reason": "<ngắn gọn>"}}
"""

def judge_summary(llm :LLMClient, source: str, summary: str) -> dict:
    raw = llm.ask(JUDGE_PROMPT.format(source=source, summary=summary))
    return json.loads(raw)

def run_llm_judge_eval(llm: LLMClient):
    for case in SUMMARY_CASES:
        summary = llm.ask(f"tóm tắt trong 1 câu: {case['input']}")
        score = judge_summary(llm, case["input"], summary)
        print(f"summary={summary!r}")
        print(f"score={score}")

def run_llm_judge_sanity_check(llm: LLMClient):
    source = SUMMARY_CASES[0]["input"]
    bad_summary = (
        "Connection pool giúp giảm chi phí bằng cách nén dữ liệu và mã hoá AES-256, "
        "được Google phát minh năm 2015."
    )  # bịa hoàn toàn, không có trong source
    score = judge_summary(llm, source, bad_summary)
    print(f"[sanity check] bad_summary score={score}")
    assert score["faithfulness"] <= 2, (
        f"Judge KHÔNG bắt được tóm tắt bịa — faithfulness={score['faithfulness']}, judge không đáng tin"
    )

if __name__ == "__main__":
    llm = LLMClient()
    acc = run_assertion_eval(llm)
    # dòng này biến eval thành regression test: sai ngưỡng thì script FAIL, không âm thầm trôi qua
    assert acc >= 0.8, f"Regression: accuracy {acc:.2%} dưới ngưỡng 80%"

    run_llm_judge_eval(llm)
    run_llm_judge_sanity_check(llm)
