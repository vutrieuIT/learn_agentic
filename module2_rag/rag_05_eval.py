from rag_03 import get_conn, vector_search_ranked, keyword_search_ranked, hybrid_search
from sentence_transformers import SentenceTransformer

EVAL_SET = [
    {"query": "Postgres mặc định cho phép tối đa bao nhiêu kết nối?", "expected_source": "connection_pool.md"},
    {"query": "công thức tính số kết nối pool nên đặt bao nhiêu", "expected_source": "connection_pool.md"},
    {"query": "log báo lỗi timeout khi lấy connection từ pool nghĩa là gì", "expected_source": "connection_pool.md"},

    {"query": "tại sao WHERE lower(email) = ... không dùng được index", "expected_source": "db_index.md"},
    {"query": "index nhiều cột thì nên đặt cột nào trước", "expected_source": "db_index.md"},
    {"query": "tạo index có nhược điểm gì", "expected_source": "db_index.md"},

    {"query": "header nào cho phép CDN cache response", "expected_source": "http_caching.md"},
    {"query": "làm sao biết nội dung chưa đổi mà không cần tải lại toàn bộ", "expected_source": "http_caching.md"},
    {"query": "cách xử lý cache invalidation khi đổi nội dung file tĩnh", "expected_source": "http_caching.md"},

    # cố tình chứa từ "idempotency" nhưng đáp án đúng KHÔNG PHẢI idempotency.md -- bẫy nhầm topic
    {"query": "vì sao message có thể bị xử lý hai lần trong hệ thống dùng queue", "expected_source": "message_queue.md"},
    {"query": "message lỗi liên tục thì xử lý thế nào để không chặn hàng đợi", "expected_source": "message_queue.md"},
    {"query": "kafka đảm bảo thứ tự message như thế nào", "expected_source": "message_queue.md"},

    {"query": "thuật toán giới hạn request cho phép burst ngắn là gì", "expected_source": "rate_limiting.md"},
    {"query": "nên rate limit theo IP hay theo user id", "expected_source": "rate_limiting.md"},
    {"query": "nhiều instance ứng dụng thì bộ đếm rate limit nên đặt ở đâu", "expected_source": "rate_limiting.md"},

    {"query": "làm sao 2 request thanh toán không tạo 2 đơn", "expected_source": "idempotency.md"},
    {"query": "idempotency key nên lưu trong bao lâu", "expected_source": "idempotency.md"},
    {"query": "dùng hash nội dung request làm idempotency key có được không", "expected_source": "idempotency.md"},
]

def evaluate(conn, model, retriever, k=5, verbose=True):
    """retriever(conn, query, model, top_k) -> list[dict] có key 'source', đã xếp theo rank."""
    hits, reciprocal_ranks = 0, []
    for item in EVAL_SET:
        results = retriever(conn, item["query"], model, top_k=max(k, 10))
        sources = [r["source"] for r in results]
        rank = next((i for i, s in enumerate(sources, start=1) if s == item["expected_source"]), None)
        hit = rank is not None and rank <= k
        hits += hit
        reciprocal_ranks.append(1 / rank if rank else 0)
        if verbose:
            mark = "OK  " if hit else "FAIL"
            print(f"[{mark}] rank={str(rank):4}  {item['query'][:55]:55} expect={item['expected_source']}")

    n = len(EVAL_SET)
    print(f"\nHit@{k}: {hits}/{n} = {hits/n:.1%}   MRR: {sum(reciprocal_ranks)/n:.3f}")

def vector_retriever(conn, query, model, top_k=10):
    qv = model.encode(query, normalize_embeddings=True)
    ids, info = vector_search_ranked(conn, qv, top_k=top_k)
    return [{"source": info[i][1]} for i in ids]

def keyword_retriever(conn, query, model, top_k=10):
    ids, info = keyword_search_ranked(conn, query, top_k=top_k)
    return [{"source": info[i][1]} for i in ids]

if __name__ == "__main__":
    conn = get_conn()
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    print("=== vector-only ===")
    evaluate(conn, model, vector_retriever)
    print("\n=== keyword-only ===")
    evaluate(conn, model, keyword_retriever)
    print("\n=== hybrid ===")
    evaluate(conn, model, lambda c, q, m, top_k: hybrid_search(c, q, m, top_k=top_k))