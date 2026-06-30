# Kế Hoạch Thực Hiện Lab 24: Production Eval + Guardrail Stack

Tài liệu này tổng hợp toàn bộ các bước và nhiệm vụ cần thực hiện theo thứ tự trình tự thời gian để hoàn thành bài lab đánh giá (evaluation) và bảo vệ (guardrail) cho hệ thống RAG.

---

## 🛠️ Phase 0: Thiết Lập & Chuẩn Bị (15 phút - Trước khi tính giờ)

Trước khi thực hiện các task code chính, hãy hoàn thành các bước thiết lập môi trường sau:

- [x] **Bước 1: Sao chép mã nguồn Day 18**
  - Copy toàn bộ các file `m*.py` từ thư mục source Day 18 của bạn vào `src/`.
  - Copy file `pipeline.py` từ Day 18 vào `src/`.
  - *Lưu ý:* Module [m4_eval.py](file:///d:/Day24-Track3-Eval-Guard/src/m4_eval.py) của bạn cần phải được triển khai hoàn chỉnh hàm `evaluate_ragas()` vì nó sẽ được sử dụng trong Phase A.
  
- [ ] **Bước 2: Khởi động cơ sở dữ liệu Vector (Qdrant)**
  - Chạy lệnh sau để khởi động container Qdrant ở chế độ nền:
    ```bash
    docker compose up -d
    ```

- [ ] **Bước 3: Cài đặt thư viện & Mô hình ngôn ngữ**
  - Cài đặt các thư viện cần thiết trong [requirements.txt](file:///d:/Day24-Track3-Eval-Guard/requirements.txt):
    ```bash
    pip install -r requirements.txt
    ```
  - Tải xuống mô hình ngôn ngữ SpaCy (dành cho Presidio PII Detection):
    ```bash
    python -m spacy download en_core_web_lg
    ```

- [ ] **Bước 4: Cấu hình biến môi trường**
  - Sao chép file cấu hình ví dụ:
    ```bash
    cp .env.example .env
    ```
  - Mở file `.env` mới tạo và điền giá trị `OPENAI_API_KEY` của bạn.

- [ ] **Bước 5: Tạo dữ liệu câu trả lời (answers_50q.json)**
  - Chạy script [setup_answers.py](file:///d:/Day24-Track3-Eval-Guard/setup_answers.py) để chạy pipeline RAG trên 50 câu hỏi test set, sinh ra file `answers_50q.json`. Quá trình này mất khoảng 5-10 phút.
    ```bash
    python setup_answers.py
    ```

---

## 📊 Phase A: RAGAS Production Eval (30 phút)

Mục tiêu là chạy RAGAS evaluation trên bộ dữ liệu 50 câu hỏi với 3 distributions để phát hiện điểm yếu của hệ thống.

- **File cần thực hiện:** [phase_a_ragas.py](file:///d:/Day24-Track3-Eval-Guard/src/phase_a_ragas.py)
- **Kiểm thử tự động:** `pytest tests/test_phase_a.py -v`

### Các Task cần làm:
- [ ] **Task 1: Nhóm câu hỏi theo phân phối (`group_by_distribution`)**
  - Phân nhóm 50 câu hỏi từ test set thành 3 nhóm: `factual` (20 câu), `multi_hop` (20 câu), và `adversarial` (10 câu).
- [ ] **Task 2: Chạy RAGAS Evaluation (`run_ragas_50q`)**
  - Gọi hàm `evaluate_ragas()` từ module `src/m4_eval.py` của bạn để chấm điểm 4 metrics (faithfulness, answer_relevancy, context_precision, context_recall) cho 50 câu trả lời.
  - Ánh xạ kết quả trả về thành danh sách các đối tượng `RagasResult`.
- [ ] **Task 3: Tìm 10 câu tệ nhất (`bottom_10`)**
  - Sắp xếp kết quả theo điểm trung bình (`avg_score`) tăng dần và lấy 10 câu hỏi có điểm số thấp nhất.
  - Sử dụng cây chẩn đoán `DIAGNOSTIC_TREE` để đưa ra chuẩn đoán lỗi (`diagnosis`) và gợi ý sửa đổi (`suggested_fix`).
- [ ] **Task 4: Phân tích cụm lỗi (`cluster_analysis`)**
  - Lập ma trận thống kê số lượng lỗi nặng nhất (`worst_metric`) trên từng phân phối (`distribution`).
  - Xác định phân phối bị lỗi nhiều nhất và chỉ số metric yếu nhất của toàn bộ hệ thống để sinh ra đoạn insight nhận xét.

### Thực thi & Viết Báo Cáo:
- [ ] Chạy file để tạo ra file báo cáo tự động:
  ```bash
  python src/phase_a_ragas.py
  ```
  *(Đầu ra yêu cầu: tạo ra file `reports/ragas_50q.json`)*
- [ ] Viết nhận xét phân tích lỗi vào file [failure_clusters.md](file:///d:/Day24-Track3-Eval-Guard/analysis/failure_clusters.md).

---

## ⚖️ Phase B: LLM-as-Judge (30 phút)

Mục tiêu là xây dựng và đánh giá cơ chế dùng LLM làm giám khảo (LLM-as-Judge) để so sánh các cặp câu trả lời và phân tích độ lệch (bias) của mô hình.

- **File cần thực hiện:** [phase_b_judge.py](file:///d:/Day24-Track3-Eval-Guard/src/phase_b_judge.py)
- **Kiểm thử tự động:** `pytest tests/test_phase_b.py -v`

### Các Task cần làm:
- [ ] **Task 5: Triển khai Pairwise Judge (`pairwise_judge`)**
  - Viết prompt và gọi LLM đánh giá cặp câu trả lời (A và B) theo 3 tiêu chí: *Accuracy* (Độ chính xác), *Completeness* (Độ đầy đủ), và *Conciseness* (Độ súc tích).
  - Trả về JSON chứa `winner` ("A", "B", hoặc "tie"), `reasoning`, và điểm số chi tiết cho từng câu trả lời.
- [ ] **Task 6: Giảm thiểu Position Bias bằng Swap-and-Average (`swap_and_average`)**
  - Chạy hàm `pairwise_judge` 2 lần: lần 1 theo thứ tự `(A, B)` và lần 2 đổi chỗ thứ tự truyền vào thành `(B, A)`.
  - Quy đổi kết quả của lượt 2 về không gian gốc và đối chiếu tính nhất quán. Kết quả chung cuộc chỉ thắng khi cả 2 lượt cùng chọn một câu trả lời, nếu không sẽ coi là hòa (`tie`).
- [ ] **Task 7: Đo mức độ đồng thuận Cohen's Kappa (`cohen_kappa`)**
  - Tính chỉ số Cohen's $\kappa$ giữa nhãn của LLM Judge (đã binarize) và 10 nhãn dán bởi con người (`human_labels_10q.json`).
- [ ] **Task 8: Báo cáo định lượng Bias (`bias_report`)**
  - Tính tỷ lệ Position Bias (số lượng trường hợp hoán đổi vị trí làm thay đổi kết quả).
  - Tính tỷ lệ Verbosity Bias (tần suất LLM chọn câu trả lời dài hơn làm câu trả lời chiến thắng).

### Thực thi & Viết Báo Cáo:
- [ ] Chạy file để sinh ra báo cáo:
  ```bash
  python src/phase_b_judge.py
  ```
  *(Đầu ra yêu cầu: tạo ra file `reports/judge_results.json`)*
- [ ] Viết nhận xét phân tích bias vào file [bias_report.md](file:///d:/Day24-Track3-Eval-Guard/analysis/bias_report.md).

---

## 🛡️ Phase C: NeMo Guardrails (30 phút)

Mục tiêu là lắp ráp hệ thống phòng thủ đa tầng (PII Scanner -> Input Guard -> RAG -> Output Guard) và kiểm thử hiệu năng latency của stack này.

- **File cần thực hiện:** [phase_c_guard.py](file:///d:/Day24-Track3-Eval-Guard/src/phase_c_guard.py)
- **Kiểm thử tự động:** `pytest tests/test_phase_c.py -v`

### Các Task cần làm:
- [ ] **Task 9a: Triển khai Quét thông tin cá nhân PII (`pii_scan`)**
  - Sử dụng Microsoft Presidio để quét và nhận diện các thông tin nhạy cảm bao gồm: Email, số điện thoại Việt Nam (`VN_PHONE`), và số CCCD/CMND Việt Nam (`VN_CCCD`).
  - Thực hiện ẩn danh hóa các thông tin này bằng cách thay thế chúng với nhãn thực thể tương ứng (ví dụ: `<VN_PHONE>`).
- [ ] **Task 9b: Triển khai Input Guardrail (`check_input_rail`)**
  - Gửi truy vấn của người dùng qua NeMo Guardrails để kiểm tra xem nội dung có nằm ngoài chủ đề cho phép (off-topic), tấn công jailbreak hoặc chèn mã độc (prompt injection) hay không.
- [ ] **Task 10: Chạy bộ kiểm thử tấn công (`run_adversarial_suite`)**
  - Chạy danh sách 20 câu hỏi tấn công giả lập từ [adversarial_set_20.json](file:///d:/Day24-Track3-Eval-Guard/adversarial_set_20.json) qua hai lớp bảo vệ Presidio và NeMo Input Rail.
  - Yêu cầu: Đạt tỷ lệ phòng thủ chính xác (Pass rate) $\ge 15/20$ (đạt $75\%$). Để nâng cao lên $18/20$ ($90\%$) nhằm ăn điểm bonus, bạn có thể chỉnh sửa và mở rộng Colang flows trong file [guardrails/rails.co](file:///d:/Day24-Track3-Eval-Guard/guardrails/rails.co).
- [ ] **Task 11: Triển khai Output Guardrail (`check_output_rail`)**
  - Kiểm tra câu trả lời sinh ra từ mô hình RAG trước khi phản hồi người dùng thông qua lớp NeMo Output Rail để phát hiện các thông tin nhạy cảm hoặc không an toàn.
- [ ] **Task 12: Đo lường thời gian phản hồi thực tế (`measure_p95_latency`)**
  - Thực hiện đo chỉ số Latency phân vị P50, P95, và P99 riêng biệt cho từng lớp: Presidio PII, NeMo Guardrails và tổng thời gian gộp.
  - Kiểm tra xem giá trị P95 tổng có đáp ứng ngân sách Latency tối đa (`LATENCY_BUDGET_P95_MS = 500ms`) hay không.

### Báo cáo & Điền Blueprint:
- [ ] Chạy file để kiểm thử và xuất kết quả:
  ```bash
  python src/phase_c_guard.py
  ```
  *(Đầu ra yêu cầu: tạo ra file `reports/guard_results.json`)*
- [ ] **Task 13: Cập nhật tài liệu CI/CD Blueprint**
  - Mở file [blueprint.md](file:///d:/Day24-Track3-Eval-Guard/reports/blueprint.md).
  - Điền các thông số Latency thực tế đo được từ Task 12 và kết quả test của bạn vào các mục tương ứng (xóa các placeholder `___ms`, `[Họ Tên]`, v.v.).

---

## 🏁 Bước Cuối Cùng: Kiểm Tra & Nộp Bài

Hãy chạy các bước xác minh sau trước khi nộp bài để đảm bảo không bị trừ điểm đáng tiếc:

- [ ] **Kiểm tra unit tests**
  - Chạy toàn bộ test suite và đảm bảo không có test nào bị fail:
    ```bash
    pytest tests/ -v
    ```
- [ ] **Kiểm tra TODO**
  - Đảm bảo đã xóa sạch hoặc hoàn thiện tất cả các comment `# TODO` trong các file code:
    ```bash
    grep -r "# TODO" src/phase_*.py
    ```
    *(Kết quả đầu ra phải rỗng)*
- [ ] **Chạy script kiểm tra chất lượng tự động**
  - Chạy script kiểm tra tổng thể được thiết kế sẵn:
    ```bash
    python check_lab.py
    ```
    *(Đảm bảo đạt trạng thái: `✓ Sẵn sàng nộp bài!`)*
- [ ] **Đẩy mã nguồn lên GitHub**
  - Đảm bảo tất cả các file sau nằm trong commit của bạn:
    - [x] Các module `src/m*.py` và `src/pipeline.py` (copy từ Day 18).
    - [x] Code hoàn thiện `src/phase_a_ragas.py`, `src/phase_b_judge.py`, và `src/phase_c_guard.py`.
    - [x] Các báo cáo tự động: `reports/ragas_50q.json`, `reports/judge_results.json`, và `reports/guard_results.json`.
    - [x] File cập nhật thủ công: `reports/blueprint.md`.
    - [x] Các tài liệu phân tích: `analysis/failure_clusters.md` và `analysis/bias_report.md`.
