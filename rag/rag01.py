import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# --- kho "tài liệu" giả để thử ---
docs = [
    "Idempotency key giúp request gửi lại nhiều lần chỉ được xử lý một lần.",
    "Connection pool tái sử dụng kết nối database để tránh chi phí mở kết nối mới.",
    "Index B-tree tăng tốc truy vấn WHERE và ORDER BY trên cột được đánh index.",
    "HTTP cache dùng header ETag và Cache-Control để client khỏi tải lại dữ liệu.",
    "Message queue tách producer khỏi consumer, giúp hệ thống chịu tải đột biến.",
    "Con mèo của tôi thích nằm ngủ trên bàn phím vào buổi sáng.",   # nhiễu, khác chủ đề
]

docs_vecs = model.encode(docs, normalize_embeddings=True)

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def search(query: str, top_k: int = 3):
    q = model.encode(query)
    scores = [(cosine(q, v), d) for v, d in zip(docs_vecs, docs)]
    scores.sort(reverse=True)
    for s, d in scores[:top_k]:
        print(f'{s:.3f} {d}')

if __name__ == "__main__":
    print("shape:", docs_vecs.shape)
    for query in [
        "Làm sao để 2 lần bấm nút thanh toán không tạo 2 đơn hàng?",
        "Cách làm truy vấn SQL nhanh hơn",
        "tránh mở kết nối DB liên tục",
    ]:
        print(f"\n>>> {query}")
        search(query)