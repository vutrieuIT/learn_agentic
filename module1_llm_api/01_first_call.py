import os
from dotenv import load_dotenv
from groq import Groq
from enum import Enum

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

messages = [
    {'role':Role.SYSTEM.value, 'content':'Bạn là trợ lý trả lời ngắn gọn bằng tiếng Việt.'},
    {'role':Role.USER.value, 'content':'Giải thích REST API trong 2 câu.'}
]

reps = client.chat.completions.create(
    model=Model.GPT_OSS_20B.value,
    messages=messages,
    temperature=1.5,
    max_tokens=2000,
)

msg = reps.choices[0]
print('--- answer ---')
print(msg.message.content)

print('--- meta ---')
print('stop: ', msg.finish_reason)
print('model: ', reps.model)
print('usage:', reps.usage.prompt_tokens, '+', reps.usage.completion_tokens,
      '=', reps.usage.total_tokens, 'tokens')

