# Ke hoach cac task tiep theo de hoan thanh Lab 24

File nay tong hop cac viec can lam tiep theo, theo dung thu tu nen thuc hien, dua tren yeu cau trong `LAB_TASKS.md` va trang thai file hien tai cua project.

## Trang thai hien tai

### Da co file can nop

- `src/m*.py`
- `src/pipeline.py`
- `src/phase_a_ragas.py`
- `src/phase_b_judge.py`
- `src/phase_c_guard.py`
- `reports/blueprint.md`
- `analysis/failure_clusters.md`
- `analysis/bias_report.md`

### Dang thieu hoac can tao

- `answers_50q.json`
- `reports/ragas_50q.json`
- `reports/judge_results.json`
- `reports/guard_results.json`

## Thu tu task can lam

## 1. Hoan tat moi truong chay

1. Khoi dong Qdrant:

   ```bash
   docker compose up -d
   ```

2. Cai dat dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Tai model SpaCy cho Presidio:

   ```bash
   python -m spacy download en_core_web_lg
   ```

4. Tao file `.env` tu file mau neu chua co:

   ```bash
   cp .env.example .env
   ```

5. Dien `OPENAI_API_KEY` vao `.env`.

## 2. Tao du lieu cau tra loi cho Phase A

1. Chay script tao `answers_50q.json`:

   ```bash
   python setup_answers.py
   ```

2. Kiem tra file da duoc tao:

   ```bash
   ls answers_50q.json
   ```

## 3. Hoan thanh va kiem tra Phase A: RAGAS Production Eval

1. Kiem tra code trong `src/phase_a_ragas.py`, dam bao da hoan thanh cac ham:

   - `group_by_distribution`
   - `run_ragas_50q`
   - `bottom_10`
   - `cluster_analysis`

2. Chay test rieng Phase A:

   ```bash
   pytest tests/test_phase_a.py -v
   ```

3. Chay script Phase A de tao report:

   ```bash
   python src/phase_a_ragas.py
   ```

4. Kiem tra file dau ra:

   ```bash
   ls reports/ragas_50q.json
   ```

5. Cap nhat nhan xet phan tich loi trong:

   ```text
   analysis/failure_clusters.md
   ```

## 4. Hoan thanh va kiem tra Phase B: LLM-as-Judge

1. Kiem tra code trong `src/phase_b_judge.py`, dam bao da hoan thanh cac ham:

   - `pairwise_judge`
   - `swap_and_average`
   - `cohen_kappa`
   - `bias_report`

2. Chay test rieng Phase B:

   ```bash
   pytest tests/test_phase_b.py -v
   ```

3. Chay script Phase B de tao report:

   ```bash
   python src/phase_b_judge.py
   ```

4. Kiem tra file dau ra:

   ```bash
   ls reports/judge_results.json
   ```

5. Cap nhat nhan xet phan tich bias trong:

   ```text
   analysis/bias_report.md
   ```

## 5. Hoan thanh va kiem tra Phase C: Guardrail Stack

1. Kiem tra code trong `src/phase_c_guard.py`, dam bao da hoan thanh cac ham:

   - `pii_scan`
   - `check_input_rail`
   - `run_adversarial_suite`
   - `check_output_rail`
   - `measure_p95_latency`

2. Kiem tra va neu can thi chinh sua guardrail flow trong:

   ```text
   guardrails/rails.co
   ```

3. Chay test rieng Phase C:

   ```bash
   pytest tests/test_phase_c.py -v
   ```

4. Chay script Phase C de tao report:

   ```bash
   python src/phase_c_guard.py
   ```

5. Kiem tra file dau ra:

   ```bash
   ls reports/guard_results.json
   ```

6. Cap nhat `reports/blueprint.md` bang cac so lieu thuc te:

   - P50 latency
   - P95 latency
   - P99 latency
   - Ket qua adversarial pass rate
   - Ket qua unit test
   - Ho ten va thong tin placeholder neu con

## 6. Chay kiem tra tong hop truoc khi nop

1. Chay toan bo test suite:

   ```bash
   pytest tests/ -v
   ```

2. Kiem tra con `# TODO` trong code Phase hay khong:

   ```bash
   grep -r "# TODO" src/phase_*.py
   ```

   Ket qua mong muon: khong co output.

3. Chay script check lab:

   ```bash
   python check_lab.py
   ```

   Ket qua mong muon: thong bao san sang nop bai.

## 7. Checklist file can co truoc khi nop

Truoc khi commit va nop bai, dam bao cac file sau ton tai:

- `src/m1_chunking.py`
- `src/m2_search.py`
- `src/m3_rerank.py`
- `src/m4_eval.py`
- `src/m5_enrichment.py`
- `src/pipeline.py`
- `src/phase_a_ragas.py`
- `src/phase_b_judge.py`
- `src/phase_c_guard.py`
- `answers_50q.json`
- `reports/ragas_50q.json`
- `reports/judge_results.json`
- `reports/guard_results.json`
- `reports/blueprint.md`
- `analysis/failure_clusters.md`
- `analysis/bias_report.md`

## 8. Thu tu uu tien neu bi loi

1. Neu `setup_answers.py` loi, kiem tra `.env`, Qdrant, API key va cac module Day 18 trong `src/`.
2. Neu Phase A loi, kiem tra `answers_50q.json` va ham `evaluate_ragas()` trong `src/m4_eval.py`.
3. Neu Phase B loi, kiem tra prompt judge, format JSON tra ve va file `human_labels_10q.json`.
4. Neu Phase C loi, kiem tra Presidio, SpaCy model, NeMo Guardrails va file `guardrails/rails.co`.
5. Neu `check_lab.py` loi, sua theo thong bao cua script roi chay lai.

