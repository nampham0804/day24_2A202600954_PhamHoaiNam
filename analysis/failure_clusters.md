# Failure Cluster Analysis — Phase A

**Sinh viên:** Nguyễn Mạnh Quý  
**Ngày:** 30/06/2026

---

## 1. Aggregate RAGAS Scores theo Distribution

| Metric | factual | multi_hop | adversarial |
|---|---|---|---|
| faithfulness | 0.795 | 0.721 | 0.692 |
| answer_relevancy | 0.738 | 0.755 | 0.724 |
| context_precision | 0.719 | 0.751 | 0.817 |
| context_recall | 0.689 | 0.759 | 0.756 |
| **avg_score** | 0.735 | 0.746 | 0.747 |

---

## 2. Bottom 10 Questions

| Rank | Distribution | Question | avg_score | worst_metric |
|---|---|---|---|---|
| 1 | factual | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu? | 0.5865 | faithfulness |
| 2 | multi_hop | Nhân viên được tài trợ khóa học 25 triệu, nghỉ việc sau 8 tháng hoàn thành khóa học. Phải hoàn trả bao nhiêu? | 0.6095 | answer_relevancy |
| 3 | factual | Nhân viên được nghỉ bao nhiêu ngày khi kết hôn? | 0.6458 | answer_relevancy |
| 4 | factual | Phụ cấp ăn trưa hàng tháng là bao nhiêu? | 0.6470 | answer_relevancy |
| 5 | factual | VPN có bắt buộc không khi làm việc từ xa (WFH)? | 0.6585 | answer_relevancy |
| 6 | multi_hop | Nhân viên mới đang trong tháng thứ 3 thử việc có BẮT BUỘC tham dự buổi đào tạo nội bộ của phòng ban không? Tại sao? | 0.6593 | faithfulness |
| 7 | multi_hop | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | 0.6628 | context_precision |
| 8 | adversarial | Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không? | 0.6672 | faithfulness |
| 9 | multi_hop | Nhân viên thử việc tháng thứ 3 phát hiện vi phạm bảo mật. Họ nên và không nên làm gì theo chính sách? | 0.6720 | context_recall |
| 10 | factual | Mentor và buddy của nhân viên mới có thể là cùng một người không? Quản lý trực tiếp có thể làm mentor không? | 0.6773 | faithfulness |

---

## 3. Failure Cluster Matrix

*(Mỗi ô = số câu có worst_metric = row, thuộc distribution = col)*

| worst_metric | factual | multi_hop | adversarial | Total |
|---|---|---|---|---|
| faithfulness | 3 | 4 | 4 | 11 |
| answer_relevancy | 5 | 6 | 3 | 14 |
| context_precision | 5 | 5 | 0 | 10 |
| context_recall | 7 | 5 | 3 | 15 |

---

## 4. Dominant Failure Analysis

**Dominant distribution:** factual  
**Dominant metric:** context_recall  

**Lý do phân tích:**
Distribution `factual` có số lượng thất bại (worst metric) nhiều nhất, chủ yếu nằm ở khía cạnh `context_recall`. Nguyên nhân là do cấu trúc tài liệu HR Policy tiếng Việt chứa nhiều cụm từ viết tắt hoặc cách diễn đạt đa dạng mà bộ RAG thuần vector (Semantic Search) chưa thể tối ưu hóa độ bao phủ của truy vấn. Khi người dùng hỏi các câu hỏi thực tế ngắn gọn, độ tương đồng ngữ nghĩa đôi khi bị phân tán vào các phân đoạn không liên quan, dẫn đến việc bỏ sót các chunk chứa thông tin chính xác. Điều này khiến cho LLM thiếu đi các dữ kiện đầu vào đúng đắn để trả lời.

---

## 5. Suggested Fixes

| Metric yếu | Root cause | Suggested fix |
|---|---|---|
| faithfulness | LLM hallucinating | Tinh chỉnh hệ thống prompt hệ thống để yêu cầu LLM trích dẫn trực tiếp nguồn ngữ cảnh và chỉ đưa ra câu trả lời khi có dữ kiện rõ ràng, nếu không phải nói rõ là không có thông tin. |
| context_recall | Missing relevant chunks | Bổ sung cơ chế Hybrid Search kết hợp BM25 (keyword search) và Dense Vector (semantic search), đồng thời tăng kích thước chunk size hoặc overlap để bảo toàn ngữ cảnh. |
| context_precision | Too many irrelevant chunks | Tích hợp bộ tái xếp hạng (Reranker) như Cohere hoặc BAAI/bge-rerancer sau bước Retrieval để sắp xếp lại độ ưu tiên và lọc bớt các chunk rác trước khi truyền vào LLM. |
| answer_relevancy | Answer doesn't match question | Cải thiện Prompt Engineering, đưa ra các ví dụ cụ thể (few-shot prompting) và hướng dẫn LLM phân tích từ khóa câu hỏi kỹ lò hơn trước khi đưa ra cấu trúc câu trả lời. |

---

## 6. Nhận xét về Adversarial Distribution

Điểm trung bình của bộ câu hỏi `adversarial` (0.747) thực tế khá tương đồng với `factual` (0.735) và `multi_hop` (0.746). Tuy nhiên, độ tin cậy thực tế ở khía cạnh `faithfulness` của adversarial lại ở mức thấp nhất (0.692). RAG pipeline vẫn bị "nhầm" bởi các cạm bẫy mâu thuẫn phiên bản (chính sách v2023 vs v2024) do hệ thống truy vấn lôi kéo cả 2 loại tài liệu cũ và mới vào ngữ cảnh mà LLM không phân biệt được thời gian hiệu lực. Ví dụ như câu hỏi số 48 về bảo hiểm PVI cho nhân viên thử việc rơi vào bottom 10 do LLM không phân biệt được quy định phủ định từ tài liệu.
