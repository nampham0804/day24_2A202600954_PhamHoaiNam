from __future__ import annotations

"""Phase B: LLM-as-Judge — pairwise, swap-and-average, Cohen κ, bias analysis."""

import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY, JUDGE_MODEL, HUMAN_LABELS_PATH


@dataclass
class JudgeResult:
    question: str
    answer_a: str
    answer_b: str
    winner_pass1: str       # "A" | "B" | "tie"  (original order)
    winner_pass2: str       # "A" | "B" | "tie"  (after swap, ALREADY converted back)
    final_winner: str       # consensus after swap-and-average
    reasoning_pass1: str
    reasoning_pass2: str
    position_consistent: bool  # True if both passes agree on same answer
    scores_pass1: dict = field(default_factory=dict)  # {"A": float, "B": float}
    scores_pass2: dict = field(default_factory=dict)


# ─── Task 5: Pairwise Judge ───────────────────────────────────────────────────

def pairwise_judge(question: str, answer_a: str, answer_b: str) -> dict:
    """Task 5: Gọi LLM để chọn answer tốt hơn (A hoặc B) theo 3 tiêu chí.

    Tiêu chí đánh giá:
        - Độ chính xác (accuracy): có khớp với thực tế chính sách không?
        - Độ đầy đủ (completeness): có trả lời đủ câu hỏi không?
        - Tính súc tích (conciseness): có thừa / thiếu thông tin không?

    Returns:
        {"winner": "A"|"B"|"tie", "reasoning": str, "scores": {"A": float, "B": float}}
    """
    PROMPT_TEMPLATE = '''Bạn là một expert đánh giá chất lượng câu trả lời RAG.

    Câu hỏi: {question}

    Answer A:
    {answer_a}

    Answer B:
    {answer_b}

    Đánh giá dựa trên 3 tiêu chí: độ chính xác, đầy đủ, súc tích.
    Trả lời JSON (chỉ JSON, không text khác):
    {{"winner": "A" hoặc "B" hoặc "tie", "reasoning": "giải thích ngắn gọn", "scores": {{"A": 0.0-1.0, "B": 0.0-1.0}}}}
    '''

    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": "Bạn là expert đánh giá RAG. Chỉ trả lời JSON."},
                {"role": "user",   "content": PROMPT_TEMPLATE.format(
                    question=question, answer_a=answer_a, answer_b=answer_b)},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠️  LLM Judge call failed: {e}. Falling back to heuristic baseline.")
        # Simple word overlap heuristic
        q_words = set(question.lower().split())
        a_words = set(answer_a.lower().split())
        b_words = set(answer_b.lower().split())
        
        overlap_a = len(q_words.intersection(a_words))
        overlap_b = len(q_words.intersection(b_words))
        
        score_a = min(1.0, overlap_a / max(1, len(q_words)))
        score_b = min(1.0, overlap_b / max(1, len(q_words)))
        
        if score_a > score_b:
            winner = "A"
        elif score_b > score_a:
            winner = "B"
        else:
            winner = "tie"
            
        return {
            "winner": winner,
            "reasoning": f"Fallback heuristic comparison (A match: {overlap_a}, B match: {overlap_b}) due to API failure: {e}",
            "scores": {"A": round(score_a, 2), "B": round(score_b, 2)}
        }


# ─── Task 6: Swap-and-Average ─────────────────────────────────────────────────

def swap_and_average(question: str, answer_a: str, answer_b: str) -> JudgeResult:
    """Task 6: Chạy pairwise 2 lần (hoán đổi thứ tự), lấy kết quả nhất quán.

    Lý do: LLM thường có position bias (ưu tiên answer xuất hiện trước).
    Bằng cách swap, ta phát hiện và giảm bias này.

    Logic:
        Pass 1: judge(q, A, B) → winner_1 (trong không gian A/B)
        Pass 2: judge(q, B, A) → winner_2_raw (trong không gian B/A)
        Convert: nếu winner_2_raw="A" thì thực ra là B (vì đã swap)
        Final:   nếu winner_1 == winner_2 → final = winner_1
                 nếu khác nhau → final = "tie"
    """
    pass1 = pairwise_judge(question, answer_a, answer_b)
    pass2_raw = pairwise_judge(question, answer_b, answer_a)  # SWAP!

    # Convert pass2 back to original A/B space
    swap_map = {"A": "B", "B": "A", "tie": "tie"}
    winner_pass2 = swap_map[pass2_raw["winner"]]

    # Average: consensus only if both agree
    if pass1["winner"] == winner_pass2:
        final = pass1["winner"]
    else:
        final = "tie"  # disagreement = inconclusive

    position_consistent = (pass1["winner"] == winner_pass2)

    return JudgeResult(
        question=question, answer_a=answer_a, answer_b=answer_b,
        winner_pass1=pass1["winner"], winner_pass2=winner_pass2,
        final_winner=final,
        reasoning_pass1=pass1["reasoning"], reasoning_pass2=pass2_raw["reasoning"],
        position_consistent=position_consistent,
        scores_pass1=pass1["scores"],
        scores_pass2={"A": pass2_raw["scores"]["B"], "B": pass2_raw["scores"]["A"]},
    )


# ─── Task 7: Cohen's κ ────────────────────────────────────────────────────────

def cohen_kappa(judge_labels: list[int], human_labels: list[int]) -> float:
    """Task 7: Tính Cohen's κ giữa LLM judge và human labels.

    Args:
        judge_labels:  nhãn từ LLM judge (0 = bad answer, 1 = good answer)
        human_labels:  nhãn từ human_labels_10q.json

    Returns:
        κ ∈ [-1, 1]
        Thang đo Landis-Koch: <0=poor, 0-0.2=slight, 0.2-0.4=fair,
                               0.4-0.6=moderate, 0.6-0.8=substantial, 0.8-1=almost perfect
    """
    if len(judge_labels) != len(human_labels):
        raise ValueError("Input arrays must have same length.")
    
    n = len(judge_labels)
    if n == 0:
        return 0.0
        
    # Observed agreement
    agreements = sum(1 for a, b in zip(judge_labels, human_labels) if a == b)
    Po = agreements / n
    
    # Expected agreement
    classes = set(judge_labels).union(set(human_labels))
    from collections import Counter
    count1 = Counter(judge_labels)
    count2 = Counter(human_labels)
    
    Pe = 0.0
    for c in classes:
        p1 = count1[c] / n
        p2 = count2[c] / n
        Pe += p1 * p2
        
    import math
    # Handle division by zero (Pe == 1.0)
    if math.isclose(Pe, 1.0, abs_tol=1e-12):
        return 1.0 if Po == 1.0 else 0.0
        
    return (Po - Pe) / (1.0 - Pe)


# ─── Task 8: Bias Report ──────────────────────────────────────────────────────

def bias_report(judge_results: list[JudgeResult]) -> dict:
    """Task 8: Đo lường position bias và verbosity bias.

    Position bias: LLM chọn answer theo vị trí (A hay B) thay vì chất lượng.
        → Đo bằng % cases where position_consistent = False

    Verbosity bias: LLM ưu tiên answer dài hơn dù không chính xác hơn.
        → Đo bằng: trong các case A thắng, A có dài hơn B không? Tương tự cho B.

    Returns:
        {
          "total_judged": int,
          "position_bias_rate": float,        # 0-1, cao = bias nhiều
          "position_bias_count": int,
          "verbosity_bias": float,            # 0-1, > 0.6 = đáng lo ngại
          "verbosity_details": {
            "a_wins_a_longer": int,           # A thắng VÀ A dài hơn
            "b_wins_b_longer": int,           # B thắng VÀ B dài hơn
            "total_decisive": int,            # tổng case có winner rõ ràng
          },
          "interpretation": str,
        }
    """
    total = len(judge_results)
    if total == 0:
        return {
            "total_judged": 0,
            "position_bias_rate": 0.0,
            "position_bias_count": 0,
            "verbosity_bias": 0.0,
            "verbosity_details": {
                "a_wins_a_longer": 0,
                "b_wins_b_longer": 0,
                "total_decisive": 0
            },
            "interpretation": "No results"
        }

    position_bias_count = sum(1 for r in judge_results if not r.position_consistent)
    position_bias_rate  = position_bias_count / total

    a_wins_a_longer = sum(
        1 for r in judge_results
        if r.final_winner == "A" and len(r.answer_a) > len(r.answer_b)
    )
    b_wins_b_longer = sum(
        1 for r in judge_results
        if r.final_winner == "B" and len(r.answer_b) > len(r.answer_a)
    )
    decisive = sum(1 for r in judge_results if r.final_winner in ("A", "B"))
    verbosity_bias = (a_wins_a_longer + b_wins_b_longer) / decisive if decisive > 0 else 0.0

    interpretation = ("Position bias cao — nên dùng swap-and-average."
                      if position_bias_rate > 0.3 else "Position bias thấp — judge ổn định.")
    return {
        "total_judged": total,
        "position_bias_rate": round(position_bias_rate, 3),
        "position_bias_count": position_bias_count,
        "verbosity_bias": round(verbosity_bias, 3),
        "verbosity_details": {
            "a_wins_a_longer": a_wins_a_longer,
            "b_wins_b_longer": b_wins_b_longer,
            "total_decisive": decisive
        },
        "interpretation": interpretation,
    }



# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # --- Demo pairwise + swap ---
    q   = "Nhân viên được nghỉ bao nhiêu ngày phép năm?"
    a_a = "Nhân viên được nghỉ 15 ngày phép năm theo chính sách v2024 hiện hành."
    a_b = "Theo quy định, nhân viên có 12 ngày phép hàng năm."

    print("Running swap-and-average judge demo...")
    demo_res = swap_and_average(q, a_a, a_b)
    print(f"  Pass 1 winner: {demo_res.winner_pass1}")
    print(f"  Pass 2 winner: {demo_res.winner_pass2}")
    print(f"  Final:         {demo_res.final_winner}")
    print(f"  Position consistent: {demo_res.position_consistent}")

    # --- Cohen's κ vs human labels ---
    with open(HUMAN_LABELS_PATH, encoding="utf-8") as f:
        human_data = json.load(f)
    human_labels = [item["human_label"] for item in human_data]
    print(f"\nHuman labels loaded: {len(human_labels)} questions")

    with open("test_set_50q.json", encoding="utf-8") as f:
        test_set = json.load(f)
    gt_map = {item["id"]: item["ground_truth"] for item in test_set}

    judge_results_list = []
    judge_labels = []

    print("\nEvaluating 10 questions from human labels...")
    for item in human_data:
        qid = item["question_id"]
        q = item["question"]
        model_ans = item["model_answer"]
        gt = gt_map.get(qid, "")

        # Compare model_answer (as A) and ground_truth (as B)
        res = swap_and_average(q, model_ans, gt)
        judge_results_list.append(res)

        # Classify as good answer (1) if model_answer won/tied or scored high
        is_good = 0
        if res.final_winner == "A" or res.final_winner == "tie":
            is_good = 1
        else:
            score_a = res.scores_pass1.get("A", 0.0)
            if score_a >= 0.7:
                is_good = 1
        judge_labels.append(is_good)
        print(f"  Q{qid}: human={item['human_label']}, judge={is_good} (winner={res.final_winner})")

    kappa = cohen_kappa(judge_labels, human_labels)
    print(f"\nCohen's κ (actual): {kappa:.3f}")

    # --- Bias report ---
    bias = bias_report(judge_results_list)
    print(f"Bias report: {bias}")

    # --- Save report ---
    report_data = {
        "cohen_kappa": round(kappa, 3),
        "bias": bias,
        "results": [
            {
                "question_id": item["question_id"],
                "question": r.question,
                "model_answer": r.answer_a,
                "ground_truth": r.answer_b,
                "winner_pass1": r.winner_pass1,
                "winner_pass2": r.winner_pass2,
                "final_winner": r.final_winner,
                "position_consistent": r.position_consistent,
                "scores_pass1": r.scores_pass1,
                "scores_pass2": r.scores_pass2,
                "judge_label": judge_labels[idx],
                "human_label": item["human_label"]
            }
            for idx, (item, r) in enumerate(zip(human_data, judge_results_list))
        ]
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/judge_results.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print("\n✓ Phase B report saved → reports/judge_results.json")
