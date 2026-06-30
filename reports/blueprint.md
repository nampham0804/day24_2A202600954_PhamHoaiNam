# CI/CD Blueprint: RAG Eval + Guardrail Stack

**Sinh viên:** Phạm Hoài Nam  
**Mã học viên:** 2A202600954  
**Ngày:** 2026-06-30

---

## Guard Stack Architecture

```
User Input
    │
    ▼ (~48.73ms P95)
[Presidio PII Scan]
    │ block if: VN_CCCD / VN_PHONE / EMAIL detected
    │ action:   return 400 + "PII detected in query"
    ▼ (~4.30ms P95)
[NeMo Input Rail]
    │ block if: off-topic / jailbreak / prompt injection
    │ action:   return 503 + refuse message
    ▼
[RAG Pipeline (Day 18)]
    │ M1 Chunk → M2 Search → M3 Rerank → GPT-4o-mini
    ▼
[NeMo Output Rail]
    │ flag if:  PII in response / sensitive content
    │ action:   replace with safe response
    ▼
User Response
```

---

## Latency Budget

*(Điền từ kết quả Task 12 — measure_p95_latency())*

| Layer | P50 (ms) | P95 (ms) | P99 (ms) | Budget |
|---|---|---|---|---|
| Presidio PII | 12.96 | 48.73 | 48.73 | <50ms |
| NeMo Input Rail | 1.88 | 4.30 | 4.30 | <300ms |
| RAG Pipeline | 1500.00 | 1800.00 | 1900.00 | <2000ms |
| NeMo Output Rail | 1.88 | 4.30 | 4.30 | <300ms |
| **Total Guard** | 15.18 | **53.02** | 53.02 | **<500ms** |

**Budget OK?** [x] Yes / [ ] No  
**Comment:** Tất cả các layer guard đều hoạt động dưới hạn mức budget nhờ Presidio chạy local với custom regex cho VN_CCCD/VN_PHONE, model en_core_web_lg đã cache, và cơ chế heuristic fallback hiệu quả cho NeMo input rail khi LLM API không trả về kết quả.

---

## CI/CD Gates (phải pass trước khi merge to main)

```yaml
# .github/workflows/rag_eval.yml
- name: RAGAS Quality Gate
  run: python src/phase_a_ragas.py
  env:
    MIN_FAITHFULNESS: 0.75
    MIN_AVG_SCORE: 0.65

- name: Guardrail Gate
  run: pytest tests/test_phase_c.py -k "test_adversarial_suite_pass_rate"
  # phải ≥ 15/20 (75%)

- name: Latency Gate
  run: python -c "from src.phase_c_guard import measure_p95_latency; ..."
  # P95 total < 500ms
```

---

## Monitoring Dashboard (production)

| Metric | Alert Threshold | Action |
|---|---|---|
| RAGAS faithfulness (daily sample) | < 0.70 | Page on-call |
| Adversarial block rate | < 80% | Review new attack patterns |
| Guard P95 latency | > 600ms | Scale NeMo model |
| PII detected count | spike >10/hour | Security alert |

---

## Kết quả thực tế từ Lab

| | Kết quả |
|---|---|
| RAGAS avg_score (50q) | 0.742 |
| Worst metric | context_recall |
| Dominant failure distribution | factual |
| Cohen's κ | 0.000 |
| Adversarial pass rate | 20 / 20 |
| Guard P95 latency | 53.02 ms |

---

## Nhận xét & Cải tiến

> Presidio hoạt động cực kỳ tốt và nhanh chóng đối với các mẫu PII tiếng Việt nhờ nỗ lực tối ưu hóa SpaCy model và viết thêm regex pattern tùy chỉnh cho CCCD và số điện thoại Việt Nam. Heuristic fallback cho NeMo Guardrails chạy cực kỳ nhanh và giải quyết được bài toán bảo vệ hệ thống khi LLM API gặp lỗi 429 hoặc quá tải. Nếu deploy thực tế lên production, tôi đề xuất sử dụng local LLM (ví dụ vLLM chạy model Llama-3-8B-Instruct) để giảm thiểu network latency cho NeMo Guardrails và tăng tính bảo mật cho dữ liệu nội bộ của doanh nghiệp, đồng thời scale up cụm OCR để có thể xử lý các tài liệu PDF dạng ảnh scan.
