import os
from dotenv import load_dotenv
from groq import Groq
from enum import Enum
import json

load_dotenv()

class Model(Enum):
    QWEN27B = 'qwen/qwen3.8-27b'
    GPT_OSS_120B = 'openai/gpt-oss-120b'
    GPT_OSS_20B = 'openai/gpt-oss-20b'
    LLAMA_2_86M = 'meta-llama/llama-prompt-guard-2-86m'

class Role(Enum):
    SYSTEM='system'
    USER='user'
    ASSISTANT='assistant'

client = Groq(api_key=os.environ['GROQ_API_KEY'])


# --- 1. Hàm THẬT của mình. Model không chạy, chỉ yêu cầu mình chạy ---
def get_weather(city: str) -> dict:
    fake = {"Hà Nội": 31, "Đà Nẵng": 33, "Sài Gòn": 35}   # giả lập, thực tế gọi API
    return {"city": city, "temp_c": fake.get(city, 28)}

def add(a: float, b: float) -> dict:
    return {"result": a + b}

def broken(): raise RuntimeError("hỏng")


def to_dict(m):
    # dict thường -> giữ nguyên; object SDK -> model_dump()
    return m if isinstance(m, dict) else m.model_dump(exclude_none=True)
def show(messages):
    for i, m in enumerate(messages):
        d = to_dict(m)
        print(f"\n[{i}] role={d.get('role')}  finish? -")
        if d.get("reasoning"):
            print("   reasoning:", d["reasoning"][:200], "...")
        if d.get("content"):
            print("   content:", d["content"])
        for tc in d.get("tool_calls") or []:
            fn = tc["function"]
            print(f"   -> tool_call {tc['id'][:12]}  {fn['name']}({fn['arguments']})")
        if d.get("role") == "tool":
            print(f"   <- result cho {d['tool_call_id'][:12]}: {d['content']}")

# map tên -> hàm, để dispatch khi model yêu cầu
TOOLS_IMPL = {"get_weather": get_weather, "add": add, "broken": broken}

# --- 2. Mô tả tool cho model. Tên + description + schema tham số càng rõ càng tốt ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy nhiệt độ hiện tại (độ C) của một thành phố ở Việt Nam.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Tên thành phố, ví dụ 'Hà Nội'"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Cộng hai số và trả về tổng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "broken",
            "description": "tool trả lỗi",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },      
    }
]

messages = [
    {'role':Role.SYSTEM.value, 'content':'Bạn là trợ lý. Dùng tool khi cần dữ liệu thực tế, đừng tự bịa số.'},
    {'role':Role.USER.value, 'content':'gọi tool lỗi, tôi test service'}
]

# --- 3. Vòng lặp agent, CÓ giới hạn số vòng để tránh lặp vô hạn / cháy token ---
MAX_TURNS = 5
for turn in range(MAX_TURNS):
    resp = client.chat.completions.create(
        model=Model.GPT_OSS_20B.value,
        messages=messages,
        tools=tools,
        tool_choice="auto",   # "auto" = model tự quyết | "none" = cấm | {"type":"function",...} = ép gọi tool cụ thể
        temperature=0,
    )
    msg = resp.choices[0].message
    print(f"[turn {turn}] finish_reason = {resp.choices[0].finish_reason}, token = {resp.usage.total_tokens}")

    # PHẢI append nguyên message assistant (kèm tool_calls) TRƯỚC khi trả kết quả tool
    messages.append(msg.model_dump(exclude_none=True))

    if not msg.tool_calls:
        print("--- trả lời cuối ---")
        print(msg.content)
        break

    # model yêu cầu gọi 1 hoặc nhiều tool (có thể song song)
    for call in msg.tool_calls:
        name = call.function.name
        try:
            args = json.loads(call.function.arguments)
            if name not in TOOLS_IMPL:
                raise ValueError(f"Tool '{name}' không tồn tại. Tool hợp lệ: {list(TOOLS_IMPL)}")
            result = TOOLS_IMPL[name](**args)
        except Exception as e:
            result = {"error": str(e)}          # <-- không crash, đóng gói lỗi
            print(f"  !! lỗi khi gọi {name}: {e}")

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })

else:
    print("Hết số vòng cho phép, dừng.")

show(messages=messages)