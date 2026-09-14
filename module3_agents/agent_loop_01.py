import json
import sys
from pathlib import Path 
sys.path.append(str(Path(__file__).resolve().parent.parent))
from shared.llm_client import LLMClient

def get_distance(city_a: str, city_b: str) -> dict:
    fake = {("Hà Nội", "Đà Nẵng"): 760, ("Hà Nội", "Sài Gòn"): 1700}
    km = fake.get((city_a, city_b)) or fake.get((city_b, city_a)) or 500
    return {"distance_km": km}

def get_fuel_price() -> dict:
    return {"price_per_liter_vnd": 23000}

def calc_cost(distance_km: float, price_per_liter: float, consumption_per_100km: float) -> dict:
    liters = distance_km * consumption_per_100km / 100
    return {"total_vnd": round(liters * price_per_liter)}

TOOLS_IMPL = {"get_distance": get_distance, "get_fuel_price": get_fuel_price, "calc_cost": calc_cost}

TOOLS_SPEC = [
    {"type": "function", "function": {
        "name": "get_distance",
        "description": "Lấy khoảng cách (km) giữa 2 thành phố.",
        "parameters": {"type": "object",
            "properties": {"city_a": {"type": "string"}, "city_b": {"type": "string"}},
            "required": ["city_a", "city_b"]},
    }},
    {"type": "function", "function": {
        "name": "get_fuel_price",
        "description": "Lấy giá xăng hiện tại (VND/lít).",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "calc_cost",
        "description": "Tính tổng tiền xăng = quãng đường * mức tiêu thụ / 100 * giá xăng.",
        "parameters": {"type": "object",
            "properties": {
                "distance_km": {"type": "number"},
                "price_per_liter": {"type": "number"},
                "consumption_per_100km": {"type": "number", "description": "lít xăng / 100km, ví dụ 7"},
            },
            "required": ["distance_km", "price_per_liter", "consumption_per_100km"]},
    }},
]

class Agent:
    def __init__(self, llm: LLMClient, tools_spec: list[dict], tools_impl: dict,
                 system: str, max_steps: int = 6):
        self.llm = llm
        self.tools_spec = tools_spec
        self.tools_impl = tools_impl
        self.system = system
        self.max_steps = max_steps

    def run(self, user_msg: str) -> str:
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": user_msg},
        ]
        for step in range(self.max_steps):
            result = self.llm.chat(messages, tools=self.tools_spec, tool_choice="auto")
            # phải tự dựng lại message assistant đúng shape để append (giống bài streaming module 1)
            assistant_msg = {"role": "assistant", "content": result.content or None}
            if result.tool_calls:
                assistant_msg["tool_calls"] = [tc.model_dump() for tc in result.tool_calls]
            messages.append(assistant_msg)

            if not result.tool_calls:
                return result.content

            for call in result.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                    if name not in self.tools_impl:
                        raise ValueError(f"Tool '{name}' không tồn tại.")
                    out = self.tools_impl[name](**args)
                except Exception as e:
                    out = {"error": str(e)}
                print(f"  [step {step}] {name}({call.function.arguments}) -> {out}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                  "content": json.dumps(out, ensure_ascii=False)})

        result = self.llm.chat(messages)
        return f"[CẢNH BÁO: hết {self.max_steps} bước, câu trả lời có thể chưa đầy đủ]\n{result.content}"


if __name__ == "__main__":
    llm = LLMClient()
    agent = Agent(
        llm, TOOLS_SPEC, TOOLS_IMPL,
        # system="Bạn là trợ lý tính chi phí chuyến đi. ",
        system="Bạn là trợ lý tính chi phí chuyến đi. Dùng tool để lấy số liệu thật, đừng tự bịa.",
        max_steps=2,
    )
    answer = agent.run("Tôi đi từ Hà Nội đến Đà Nẵng bằng xe máy tiêu thụ 3 lít/100km, tốn bao nhiêu tiền xăng?")
    print("\n--- trả lời ---")
    print(answer)
    print(llm.usage)