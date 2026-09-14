import sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.llm_client import LLMClient
from agent_loop_01 import Agent

def get_price(kind: str) -> dict:
    if kind not in ("fuel", "toll"):
        raise ValueError(f"kind phải là 'fuel' hoặc 'toll', nhận được '{kind}'")
    return {"price": {"fuel": 23000, "toll": 50000}[kind]}

def estimate(x: float, y: float, z: float) -> dict:
    # trùng chức năng với "calc_cost" ở bước 1 nhưng tên tham số vô nghĩa
    return {"total": x * y * z / 100}

TOOLS_IMPL_BAD = {"get_price": get_price, "estimate": estimate}

TOOLS_SPEC_BAD = [
    {"type": "function", "function": {
        "name": "get_price",
        "description": "Lấy giá.",   # <-- mơ hồ, không nói giá gì, đơn vị gì
        "parameters": {"type": "object",
            "properties": {"kind": {"type": "string","enum": ["fuel", "toll"], 
                                    "description": "'fuel' = giá xăng, 'toll' = phí cầu đường"}},   # <-- không enum, không ví dụ giá trị hợp lệ
            "required": ["kind"]},
    }},
    {"type": "function", "function": {
        "name": "estimate",
        "description": "Ước tính.",  # <-- không nói ước tính cái gì, công thức nào
        "parameters": {"type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
            "required": ["x", "y", "z"]},   # <-- x,y,z không gợi ý km/giá/tiêu thụ là cái nào
    }},
]

if __name__ == '__main__':
    llm = LLMClient()
    system="""Bạn là trợ lý tính chi phí chuyến đi.
QUY TẮC BẮT BUỘC:
- CHỈ dùng số liệu lấy được từ tool. TUYỆT ĐỐI không tự đoán/nhớ số liệu (khoảng cách, giá cả...).
- Nếu KHÔNG có tool để lấy 1 thông tin cần thiết, phải nói rõ: "Tôi không có công cụ để lấy <thông tin đó>, vui lòng cung cấp." KHÔNG được tự điền số.
- LUÔN dùng tool `estimate`/`calc_cost` để tính toán, không tự nhẩm bằng tay."""
    agent = Agent(llm, TOOLS_SPEC_BAD, TOOLS_IMPL_BAD,
        system=system,
        max_steps=6,
    )

    answer = agent.run("Tôi đi từ Hà Nội đến Đà Nẵng bằng xe máy tiêu thụ 3 lít/100km, tốn bao nhiêu tiền xăng?")
    print("\n--- trả lời ---")
    print(answer)
    print(llm.usage)