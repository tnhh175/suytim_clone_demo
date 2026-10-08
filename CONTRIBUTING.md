# Hướng Dẫn Nộp Bài (dành cho sinh viên)

## 0. Quy ước đặt tên thư mục nộp bài

```
submissions/<case_study_slug>_<ma_nhom>/
```

- `case_study_slug` — đúng slug case study trong
  [ngân hàng case study](https://fossbk-spec.github.io/ktpmud-book/do_an_mon_hoc)
  (`may_day`, `suy_tim`, `alzheimer`, hoặc `dreye`).
- `ma_nhom` — mã nhóm giảng viên cấp (vd `nhom01`) — **không dùng họ tên
  thật hay MSSV** trong tên thư mục (xem Mục 3 về quyền riêng tư).

Ví dụ: `submissions/suy_tim_nhom07/`.

**Quan trọng:** 1 Pull Request chỉ được đụng tới ĐÚNG 1 thư mục
`submissions/<case_study_slug>_<ma_nhom>/` của nhóm bạn. CI sẽ tự động
FAIL nếu PR chứa thay đổi ở bất kỳ đường dẫn nào khác (kể cả sửa file gốc
của repo này) — đây là cơ chế bắt buộc để nộp bài của nhóm A không bao giờ
vô tình ghi đè hay xung đột với nhóm B.

## 1. Các bước nộp bài

1. **Fork** repo này về tài khoản GitHub cá nhân (hoặc dùng chung 1 fork
   cho cả nhóm — 1 thành viên đại diện fork, thêm thành viên còn lại làm
   collaborator trên fork đó).
2. **Tạo branch riêng** từ `main`, đặt tên `submit/<case_study_slug>-<ma_nhom>`:
   ```
   git checkout -b submit/suy_tim-nhom07
   ```
3. **Copy thư mục mẫu:**
   ```
   cp -r submissions/_TEMPLATE submissions/suy_tim_nhom07
   ```
4. **Điền `submission.json`** (xem schema Mục 2) và các file trong `report/`
   (SRS, C4 Model, Test Report...), `src/`, `slides/`.
5. **Chạy kiểm tra cục bộ trước khi nộp** (bắt buộc — CI sẽ chạy lại đúng
   script này, nộp trước khi tự kiểm tra chỉ tốn thời gian chờ CI fail):
   ```
   python scripts/validate_submission.py submissions/suy_tim_nhom07
   ```
6. **Commit + push** lên fork của bạn, rồi **mở Pull Request** vào
   `main` của `fossbk-spec/ktpmud-project`.
7. Chờ CI chạy xanh (✅) — nếu đỏ (❌), đọc log lỗi, sửa, push tiếp lên
   cùng branch (PR tự cập nhật, không cần mở PR mới).
8. Giảng viên/TA review nội dung và merge. Sau khi merge, bài nộp của nhóm
   bạn chính thức nằm trong lịch sử `main` — **không sửa được nữa qua PR
   thường** (mọi cập nhật sau merge coi như nộp lại, cần trao đổi trực tiếp
   với giảng viên).

## 2. Schema `submission.json`

```json
{
  "case_study_slug": "suy_tim",
  "case_study_id": "CS-2",
  "group_code": "nhom07",
  "members": ["MSSV1", "MSSV2", "MSSV3", "MSSV4"],
  "scenario": "khong_ap_dung",
  "submitted_at": "2026-12-15"
}
```

Trường bắt buộc: `case_study_slug`, `case_study_id`, `group_code`,
`members`. `members` dùng **MSSV**, không dùng họ tên đầy đủ (xem Mục 3).

`scenario` chỉ có ý nghĩa với CS-1 (Dr May Day) — điền `mayday_sim` (kịch
bản mô phỏng độc lập) hoặc `mayday_tichhop` (kịch bản tích hợp thật). Với
CS-2/CS-3 điền `khong_ap_dung`.

## 3. Quy tắc bắt buộc về quyền riêng tư (CI sẽ chặn nếu vi phạm)

1. **Không đưa dữ liệu bệnh nhân thật** vào bất kỳ đâu trong PR — toàn bộ
   3 case study đều bắt buộc dùng dữ liệu synthetic/mô phỏng theo nguyên
   tắc Zero PII/PHI của khung chung. Vi phạm: 0 điểm toàn phần theo Rubric.
2. **Không commit khóa API, token, mật khẩu, file `.env`.**
3. **Không dùng họ tên thật đầy đủ** của thành viên trong code/README/tên
   file — dùng MSSV. Tránh rủi ro khi repo này công khai vĩnh viễn trên
   GitHub.
4. **Không commit file dữ liệu lớn** (>10MB) — dùng link Google
   Drive/HuggingFace/Kaggle trong `README.md` thay vì đẩy thẳng vào Git.
5. `scripts/validate_submission.py` chạy vài kiểm tra mẫu hình cơ bản
   (regex cho khóa API dạng phổ biến, file `.env`, MSSV/tên trong
   `submission.json` không phải placeholder) — đây là **lưới an toàn cuối**,
   không thay thế trách nhiệm tự rà soát của nhóm trước khi nộp.

## 4. Câu hỏi thường gặp

**Nhóm em có thể sửa bài sau khi đã merge không?**
Không tự sửa qua PR thường (branch protection chặn ghi đè thư mục nhóm
khác nhưng cũng chặn cả việc bạn tự ý sửa thư mục của chính mình sau khi
đã merge, để giữ tính toàn vẹn lịch sử nộp bài) — trao đổi trực tiếp với
giảng viên nếu cần nộp bổ sung/nộp lại.

**2 nhóm có thể chọn cùng 1 case study không?**
Có — mỗi nhóm vẫn có thư mục riêng (`ma_nhom` khác nhau), không xung đột.

**Nhóm chọn CS-2/CS-3 (dùng chung kiến trúc 4-module) có cần nộp riêng
từng module không?**
Không — nộp toàn bộ sản phẩm (mã nguồn + báo cáo + slide) của nhóm vào
đúng 1 thư mục `submissions/<case_study_slug>_<ma_nhom>/`.

**Sao không cho push thẳng vào `main`?**
Vì `main` được bảo vệ (branch protection) — chỉ nhận thay đổi qua PR đã
qua CI xanh, tránh 1 nhóm vô tình (hoặc cố ý) ghi đè bài của nhóm khác.
