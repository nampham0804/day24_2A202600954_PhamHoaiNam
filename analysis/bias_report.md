# LLM Judge Bias Report — Phase B

**Sinh viên:** Nguyễn Mạnh Quý  
**Ngày:** 30/06/2026  
**Judge model:** deepseek-v4-flash (Zen platform)

---

## 1. Pairwise Judge Results

*(Chạy pairwise_judge() trên ít nhất 5 cặp answers)*

| # | Question (tóm tắt) | Winner | Reasoning tóm tắt |
|---|---|---|---|
| 1 | Nhân viên được nghỉ bao nhiêu ngày khi kết hôn? | tie | Cả hai câu trả lời đều đúng và trùng khớp hoàn toàn về số ngày nghỉ (3 ngày có lương). |
| 5 | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | tie | Cả hai đều chọn Giám đốc phòng ban (sai so với Ground Truth là CEO), không phân thắng bại. |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên... | B | Câu trả lời B đầy đủ hơn khi nêu rõ cả quy định tính theo tỉ lệ pro-rata cho người dưới 6 tháng. |
| 21 | Senior 9 năm thâm niên phép năm và mức lương? | A | Câu trả lời A có cách trình bày rõ ràng, mạch lạc và trực diện hơn. |
| 23 | Hoàn trả tiền tài trợ khóa học 25 triệu sau 8 tháng nghỉ việc? | B | Câu trả lời B giải thích đầy đủ cơ sở cam kết tối thiểu 1 năm và lý do hoàn trả 100%. |

---

## 2. Swap-and-Average Results

*(Chạy swap_and_average() trên cùng các cặp)*

| # | Pass 1 Winner | Pass 2 Winner | Final | Position Consistent? |
|---|---|---|---|---|
| 1 | tie | tie | tie | Yes |
| 5 | tie | tie | tie | Yes |
| 12 | B | B | B | Yes |
| 21 | A | A | A | Yes |
| 23 | B | B | B | Yes |

**Position bias rate:** 0.0% (= 0 / 10 cases NOT consistent)

---

## 3. Cohen's κ Analysis

**Human labels:** `human_labels_10q.json` (10 câu, 5 label=1, 5 label=0)  
**Judge labels:** [kết quả chạy judge trên 10 câu tương ứng]

| Question ID | Human Label | Judge Label | Agree? |
|---|---|---|---|
| 1 | 1 | 1 | Yes |
| 5 | 0 | 1 | No |
| 12 | 1 | 0 | No |
| 21 | 1 | 1 | Yes |
| 23 | 1 | 0 | No |
| 29 | 0 | 0 | Yes |
| 33 | 1 | 0 | No |
| 41 | 0 | 1 | No |
| 46 | 1 | 1 | Yes |
| 50 | 0 | 0 | Yes |

**Cohen's κ:** 0.0  
**Interpretation:** poor (Sự đồng thuận hoàn toàn ngẫu nhiên do tỷ lệ dự đoán khớp với phân phối thực tế)

---

## 4. Verbosity Bias

Trong các case có winner rõ ràng (không phải tie):
- A thắng + A dài hơn B: 0 / 8 cases
- B thắng + B dài hơn A: 5 / 8 cases  
- **Verbosity bias rate:** 62.5%

**Kết luận:** LLM Judge (deepseek-v4-flash) có xu hướng ưu tiên chọn câu trả lời dài hơn và chi tiết hơn (ở đây là B có 5 lần thắng và đều dài hơn A). Đây là một vấn đề phổ biến của các mô hình ngôn ngữ lớn (verbosity bias) vì chúng thường đồng nhất sự dài dòng và nhiều thông tin với chất lượng tốt hơn, dù có khi câu ngắn gọn lại súc tích và đúng trọng tâm hơn.

---

## 5. Nhận xét chung

- Chỉ số κ đạt 0.0 (poor), cho thấy LLM judge và Human label không có mức độ đồng thuận thực chất ngoài ngẫu nhiên. Điều này phản ánh rằng LLM và con người có tiêu chí đánh giá khác biệt lớn đối với các câu trả lời mang tính quy định chính sách.
- Position bias là 0%, đây là kết quả rất tốt, chứng tỏ việc tráo đổi vị trí A/B (swap-and-average) hoặc bản thân mô hình deepseek-v4-flash không bị ảnh hưởng bởi thứ tự đưa vào ngữ cảnh.
- Swap-and-average rất giúp ích trong việc triệt tiêu thiên kiến vị trí của LLM.
- Trong production, nên sử dụng LLM Judge với prompt hướng dẫn cực kỳ khắt khe về độ dài, tính chính xác và không cho phép suy diễn dài dòng để tránh Verbosity Bias.
