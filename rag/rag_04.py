import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).resolve().parent.parent))  # để import shared/
from shared.llm_client import LLMClient
from rag_03 import get_conn, hybrid_search

SYSTEM_PROMPT = """Bạn là trợ lý trả lời câu hỏi CHỈ dựa vào các đoạn tài liệu (CONTEXT) được cung cấp.
Quy tắc:
- Nếu context không chứa đủ thông tin để trả lời, nói rõ "Không tìm thấy thông tin trong tài liệu" — KHÔNG bịa.
- Khi trả lời, ghi rõ trả lời dựa trên đoạn nào bằng cách trích [nguồn: <source>].
- Trả lời ngắn gọn, đúng trọng tâm câu hỏi.
"""

THRESH = 0.5

def build_context(chunks: list[dict]) -> str:
    # đánh số + gắn nguồn để model có thể trích dẫn lại
    parts = [
        f"[{i}] (nguồn: {c['source']} :: {c['heading']})\n{c['text']}"
        for i, c in enumerate(chunks, start=1)
    ]
    return "\n\n".join(parts)

def answer(query: str, conn, model, llm: LLMClient, top_k: int = 5) -> str:
    chunks = hybrid_search(conn, query, model, top_k=top_k)
    # chunks = [c for c in chunks if c['score'] > THRESH]
    # if not chunks:
    #     return "Không tìm thấy thông tin trong tài liệu."
    for c in chunks:
        print(c["source"], "::", c["heading"], ' - ', c['score'])
        print(c["text"][:200])
        print("---")
    context = build_context(chunks)
    user_prompt = f"CONTEXT:\n{context}\n\nCÂU HỎI: {query}"
    return llm.ask(user_prompt, system=SYSTEM_PROMPT)

if __name__ == "__main__":
    conn = get_conn()
    embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    llm = LLMClient()

    q = "làm sao 2 request thanh toán không tạo 2 đơn"
    print(answer(q, conn, embed_model, llm))
    print("\n---\n")
    print(llm.usage)