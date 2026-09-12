import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from rag_02 import build_chunks, chunk_paragraphs

DSN = "postgresql://rag_user:rag_pwd@localhost:5432/rag"

def get_conn():
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)   # dạy psycopg cách encode/decode numpy array <-> vector
    return conn

def create_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            heading TEXT,
            chunk_index INT NOT NULL,
            text TEXT NOT NULL,
            embedding VECTOR(384) NOT NULL
        )
    """)

def create_index(conn):
    conn.execute("""
        CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
        ON chunks USING hnsw (embedding vector_cosine_ops)
    """)

def ingest(conn):
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    recs = build_chunks(chunk_paragraphs)
    vecs = model.encode([r["text"] for r in recs], normalize_embeddings=True)

    with conn.cursor() as cur:
        for r, v in zip(recs, vecs):
            cur.execute(
                """INSERT INTO chunks (source, heading, chunk_index, text, embedding)
                   VALUES (%s, %s, %s, %s, %s)""",
                (r["source"], r["heading"], r["chunk_index"], r["text"], v),
            )
    print(f"Đã insert {len(recs)} chunks")

def search(conn, query: str, model, top_k: int = 3):
    qv = model.encode(query, normalize_embeddings=True)
    rows = conn.execute(
        """
        SELECT source, heading, text, embedding <=> %s AS distance
        FROM chunks
        ORDER BY distance
        LIMIT %s
        """,
        (qv, top_k),
    ).fetchall()
    for source, heading, text, distance in rows:
        similarity = 1 - distance
        print(f"{similarity:.3f}  {source:20} :: {heading}")

def vector_search_ranked(conn, qv, top_k=20):
    rows = conn.execute(
        """SELECT id, source, heading, text
           FROM chunks ORDER BY embedding <=> %s LIMIT %s""",
        (qv, top_k),
    ).fetchall()
    return [r[0] for r in rows], {r[0]: r for r in rows}  # ids theo thứ tự rank, map tra info

def to_or_tsquery(conn, text):
    lexemes = conn.execute(
        "SELECT tsvector_to_array(to_tsvector('simple', %s))", (text,)
    ).fetchone()[0]
    return " | ".join(lexemes) if lexemes else None

def keyword_search_ranked(conn, query, top_k=20):
    or_query = to_or_tsquery(conn, query)
    if or_query is None:
        return [], {}
    rows = conn.execute(
        """SELECT id, source, heading, text
           FROM chunks
           WHERE to_tsvector('simple', text) @@ to_tsquery('simple', %s)
           ORDER BY ts_rank(to_tsvector('simple', text), to_tsquery('simple', %s)) DESC
           LIMIT %s""",
        (or_query, or_query, top_k),
    ).fetchall()
    return [r[0] for r in rows], {r[0]: r for r in rows}

def hybrid_search(conn, query, model, top_k=5, k_rrf=60):
    qv = model.encode(query, normalize_embeddings=True)
    vec_ids, vec_info = vector_search_ranked(conn, qv)
    kw_ids, kw_info = keyword_search_ranked(conn, query)

    scores = {}
    for rank, doc_id in enumerate(vec_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k_rrf + rank)
    for rank, doc_id in enumerate(kw_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k_rrf + rank)

    info = {**vec_info, **kw_info}
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
    # for doc_id, s in ranked:
    #     _, source, heading, text = info[doc_id]
    #     print(f"{s:.4f}  {source:20} :: {heading}")
    return [
        {"id": doc_id, "score": s, "source": info[doc_id][1],
         "heading": info[doc_id][2], "text": info[doc_id][3]}
        for doc_id, s in ranked
    ]

if __name__ == "__main__":
    conn = get_conn()
    create_schema(conn)
    # ingest(conn)   # chỉ chạy 1 lần, comment lại tránh insert trùng
    create_index(conn)
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print('ngữ nghĩa')
    for r in hybrid_search(conn, "làm sao 2 request thanh toán không tạo 2 đơn", model):
        print(f"{r['score']:.4f}  {r['source']:20} :: {r['heading']}")
    print('keyword')
    for r in hybrid_search(conn, "idempotency key retry POST", model):
        print(f"{r['score']:.4f}  {r['source']:20} :: {r['heading']}")