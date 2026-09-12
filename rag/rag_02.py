from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import re

DOCS_DIR = Path(__file__).parent / "docs"

def load_docs() -> list[dict]:
    """Đọc mọi file .md -> [{'source': 'idempotency.md', 'text': '...'}]"""
    out = []
    for p in sorted(DOCS_DIR.glob("*.md")):
        out.append({"source": p.name, "text": p.read_text(encoding="utf-8")})
    return out

# ---------- CÁCH 1: fixed-size, cắt thô theo ký tự ----------
def chunk_fixed(text: str, size: int = 400, overlap: int = 80) -> list[str]:
    # TODO: trượt cửa sổ [i, i+size], bước nhảy = size - overlap
    #       return list các lát text
    chunks = []
    for idx in range(0, len(text), size):
        start = max(0, idx - overlap)
        end = start + size
        chunks.append(text[start:end])
    return chunks

# ---------- CÁCH 2: gói theo đoạn văn, tôn trọng ranh giới ----------
def chunk_paragraphs(text, max_chars=400, overlap_paras=1):
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    heading, chunks, cur = "", [], []

    def flush():
        if cur:
            chunks.append((heading, "\n\n".join(cur)))

    for p in paras:
        if p.startswith("#"):
            flush()                     # chốt chunk với heading CŨ
            cur = []
            heading = p.lstrip("# ").strip()
            continue
        if cur and sum(len(x) for x in cur) + len(p) > max_chars:
            flush()
            cur = cur[-overlap_paras:] if overlap_paras else []
        cur.append(p)
    flush()
    return chunks

# ---------- gắn metadata ----------
def build_chunks(chunker):
    records = []
    for doc in load_docs():
        for i, (heading, body) in enumerate(chunker(doc["text"])):
            text = f"[{heading}] {body}" if heading else body
            records.append({
                "text": text, "source": doc["source"],
                "heading": heading, "chunk_index": i, "n_chars": len(text),
            })
    return records


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    # tách câu theo . ! ? — đơn giản, đủ dùng cho văn bản kỹ thuật (không có câu kiểu "TS. Nguyễn...")
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

# ---------- CÁCH 3: cửa sổ theo câu, tôn trọng ranh giới heading ----------
def chunk_sentences(text, window: int = 2, overlap: int = 1):
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    heading, body_paras, chunks = "", [], []
    step = max(window - overlap, 1)

    def flush():
        if not body_paras:
            return
        sentences = split_sentences(" ".join(body_paras))
        i = 0
        while i < len(sentences):
            group = sentences[i:i + window]
            chunks.append((heading, " ".join(group)))
            if i + window >= len(sentences):
                break
            i += step

    for p in paras:
        if p.startswith("#"):
            flush()
            body_paras = []
            heading = p.lstrip("# ").strip()
            continue
        body_paras.append(p)
    flush()
    return chunks

def demo_search():
    recs = build_chunks(chunk_paragraphs)
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    mat = model.encode([r["text"] for r in recs], normalize_embeddings=True)  # (n_chunk, 384)

    # queries = [
    #     "timeout của connection pool mặc định bao nhiêu",
    #     "làm sao 2 request thanh toán không tạo 2 đơn",
    #     "index không được database sử dụng khi nào",
    # ]
    # for q in queries:
    #     qv = model.encode(q, normalize_embeddings=True)
    #     scored = sorted(
    #         ((float(np.dot(qv, v)), r) for v, r in zip(mat, recs)),
    #         key=lambda x: x[0], reverse=True,
    #     )
    #     print(f"\n>>> {q}")
    #     for s, r in scored[:3]:
    #         print(f"  {s:.3f}  {r['source']:20} :: {r['heading']}")
    #         print(f"         {r['text'][:90]}...")

    q = "làm sao 2 request thanh toán không tạo 2 đơn"
    qv = model.encode(q, normalize_embeddings=True)
    print(f">>> tất cả chunk idempotency.md cho query này:")
    for v, r in zip(mat, recs):
        if r["source"] == "idempotency.md":
            print(f"  {float(np.dot(qv, v)):.3f}  {r['heading']}")

if __name__ == "__main__":
    demo_search()