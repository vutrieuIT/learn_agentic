import os, json
from dotenv import load_dotenv
from groq import Groq
from enum import Enum

load_dotenv()

class Model(Enum):
    GPT_OSS_20B = 'openai/gpt-oss-20b'

client = Groq(api_key=os.environ['GROQ_API_KEY'])

def get_weather(city: str) -> dict:
    fake = {"Hà Nội": 31, "Đà Nẵng": 33, "Sài Gòn": 35}
    return {"city": city, "temp_c": fake.get(city, 28)}

TOOLS_IMPL = {"get_weather": get_weather}
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Lấy nhiệt độ hiện tại (độ C) của một thành phố ở Việt Nam.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}]


def stream_one_turn(messages):
    """1 lượt gọi model, stream. In text/reasoning khi nó chảy về.
    Trả về (assistant_msg_dict, finish_reason)."""
    stream = client.chat.completions.create(
        model=Model.GPT_OSS_20B.value,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0,
        stream=True,
        extra_body={"stream_options": {"include_usage": True}},
    )

    content_parts = []
    tc_buf = {}          # index -> {"id", "name", "args"}
    finish = None

    for chunk in stream:
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        finish = choice.finish_reason or finish
        delta = choice.delta

        if getattr(delta, "reasoning", None):
            print(f"\033[90m{delta.reasoning}\033[0m", end="", flush=True)
        if delta.content:
            print(delta.content, end="", flush=True)
            content_parts.append(delta.content)

        for tc in (delta.tool_calls or []):
            slot = tc_buf.setdefault(tc.index, {"id": None, "name": None, "args": ""})
            if tc.id:
                slot["id"] = tc.id
            if tc.function and tc.function.name:
                slot["name"] = tc.function.name
            if tc.function and tc.function.arguments:
                slot["args"] += tc.function.arguments        # <-- NỐI

    # dựng lại message assistant đúng shape API cần cho lượt sau
    msg = {"role": "assistant", "content": "".join(content_parts) or None}
    if tc_buf:
        msg["tool_calls"] = [
            {"id": s["id"], "type": "function",
             "function": {"name": s["name"], "arguments": s["args"]}}
            for _, s in sorted(tc_buf.items())
        ]
    return msg, finish


messages = [
    {"role": "system", "content": "Bạn là trợ lý. Dùng tool khi cần dữ liệu thực tế."},
    {"role": "user", "content": "Hà Nội với Sài Gòn chỗ nào nóng hơn, chênh mấy độ?"},
]

MAX_TURNS = 5
for turn in range(MAX_TURNS):
    print(f"\n===== turn {turn} =====")
    assistant_msg, finish = stream_one_turn(messages)
    messages.append(assistant_msg)

    if not assistant_msg.get("tool_calls"):
        print(f"\n[finish: {finish}] -> xong")
        break

    for call in assistant_msg["tool_calls"]:
        name = call["function"]["name"]
        raw_args = call["function"]["arguments"]
        try:
            args = json.loads(raw_args)          # giờ mới parse — vì đã nối đủ
            result = TOOLS_IMPL[name](**args)
        except Exception as e:
            result = {"error": str(e)}
        print(f"\n  -> {name}({raw_args}) = {result}")
        messages.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": json.dumps(result, ensure_ascii=False),
        })
else:
    print("Hết số vòng.")