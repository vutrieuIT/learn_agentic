import os
from dotenv import load_dotenv
from groq import Groq
from enum import Enum
import json
from pydantic import BaseModel
from pydantic import ValidationError

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

ticket_content = 'xin chào'
ticket_content_account = 'tài khoản của tôi bị lỗi đăng nhập, vui long xem xét'
ticket_content_bill = 'thanh toán thành công, nhưng check hóa đơn thì không thấy'
ticket_content_confusses = 'sau khi đăng nhập thì app bị văng'

class Category(str, Enum):
    billing = "billing"; 
    technical = "technical"; 
    account = "account"; 
    other = "other"

class Priority(str, Enum):
    low = "low"; medium = "medium"; high = "high"

class Ticket(BaseModel):
    is_ticket: bool
    category: Category
    priority: Priority
    summary: str
    need_human: bool

def classify(ticket_text: str) -> Ticket:
    reps = client.chat.completions.create(
        model=Model.GPT_OSS_20B.value,
        messages=[
            {"role": Role.SYSTEM.value, "content": "Phân loại ticket hỗ trợ. Trả JSON theo schema."},
            {"role": Role.USER.value, "content": ticket_text},
        ],
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ticket", "schema": Ticket.model_json_schema()},  # <-- schema sinh từ class
        },
    )
    raw = reps.choices[0].message.content
    return Ticket.model_validate_json(raw)   # <-- parse + ép kiểu + raise nếu sai

messages = [
    {'role':Role.SYSTEM.value, 'content':'Trả về JSON. Các field: category, priority, summary, need_human.'},
    {'role':Role.USER.value, 'content':ticket_content}
]

tickets = {
    "account":  "tài khoản của tôi bị lỗi đăng nhập, vui lòng xem xét",
    "bill":     "thanh toán thành công, nhưng check hóa đơn thì không thấy",
    "crash":    "sau khi đăng nhập thì app bị văng",
    "hello":    "xin chào",
}

# print(json.dumps(Ticket.model_json_schema(), indent=2))
for name, text in tickets.items():
    t = classify(text)
    if not t.is_ticket:
        print(f"{name:8} -> skip")
    else:
        print(f"{name:8} -> {t}")

bad = '{"is_ticket": true, "category": "spam", "priority": "urgent", "summary": "x", "need_human": "maybe"}'

try:
    Ticket.model_validate_json(bad)
except ValidationError as e:
    print(e)