#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_submission.py — Kiểm tra 1 thư mục nộp bài (submissions/<slug>/)
hoặc toàn bộ diff của 1 Pull Request.

Áp dụng nguyên tắc "1 nhóm = 1 file/thư mục cách ly" đã dùng xuyên suốt hệ
sinh thái HMYT/KTPMUD: mỗi nhóm chỉ được sửa đúng 1 thư mục của mình, có
schema bắt buộc, và bị chặn nếu chứa mẫu hình dữ liệu nhạy cảm.

Hai chế độ sử dụng:

  1) Kiểm tra 1 thư mục nộp bài cụ thể (dùng khi sinh viên tự kiểm tra
     trước khi nộp):
       python scripts/validate_submission.py submissions/suy_tim_nhom07

  2) Kiểm tra toàn bộ file thay đổi trong 1 PR (dùng trong CI —
     .github/workflows/validate-submission.yml gọi chế độ này):
       python scripts/validate_submission.py --pr-files changed_files.txt

Thoát mã 0 nếu PASS, khác 0 nếu FAIL (để CI tự động chặn merge).
"""

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SUBMISSIONS_DIR = ROOT / "submissions"
TEMPLATE_NAME = "_TEMPLATE"

REQUIRED_SUBMISSION_FIELDS = ["case_study_slug", "case_study_id", "group_code", "members"]
VALID_CASE_STUDY_SLUGS = {"may_day", "suy_tim", "alzheimer", "dreye"}
MAX_FILE_SIZE_MB = 10

# Regex mẫu hình phổ biến của khóa API/secret — lưới an toàn cuối, không
# thay thế việc nhóm tự rà soát trước khi nộp.
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                      # AWS access key
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),                    # OpenAI/Anthropic-style key
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),                 # Google API key
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),                    # GitHub PAT
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]

PLACEHOLDER_VALUES = {
    "REPLACE_VOI_SLUG_CASE_STUDY_may_day_suy_tim_hoac_alzheimer",
    "REPLACE_VOI_MA_CS_VD_CS-2",
    "REPLACE_VOI_MA_NHOM_VD_nhom07",
    "MSSV1",
    "MSSV2",
    "MSSV3",
    "YYYY-MM-DD",
}


def scan_secrets(file_path: Path) -> list[str]:
    if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".pkl", ".h5", ".pt"}:
        return []
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    findings = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"nghi vấn secret khớp mẫu {pattern.pattern!r}")
    return findings


def validate_folder(folder: Path) -> list[str]:
    errors: list[str] = []

    if folder.name == TEMPLATE_NAME:
        errors.append(f"'{folder.name}' là thư mục mẫu — không được nộp trực tiếp, hãy copy sang thư mục mới.")
        return errors

    if not re.match(r"^[a-z0-9_]+_[a-z0-9]+$", folder.name):
        errors.append(
            f"Tên thư mục '{folder.name}' không đúng quy ước '<case_study_slug>_<ma_nhom>' "
            f"(chỉ chữ thường/số/gạch dưới)."
        )

    manifest_path = folder / "submission.json"
    if not manifest_path.exists():
        errors.append("Thiếu file 'submission.json' bắt buộc.")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"'submission.json' lỗi cú pháp JSON: {e}")
            manifest = {}

        for field in REQUIRED_SUBMISSION_FIELDS:
            if not manifest.get(field):
                errors.append(f"'submission.json' thiếu trường bắt buộc '{field}'.")

        for field, value in manifest.items():
            values = value if isinstance(value, list) else [value]
            for v in values:
                if isinstance(v, str) and v.strip() in PLACEHOLDER_VALUES:
                    errors.append(
                        f"'submission.json' trường '{field}' vẫn còn giá trị mẫu ('{v}') — cần điền thật."
                    )

        slug = manifest.get("case_study_slug")
        if slug and slug not in VALID_CASE_STUDY_SLUGS:
            errors.append(
                f"'submission.json' trường 'case_study_slug' = '{slug}' không hợp lệ — "
                f"phải là 1 trong {sorted(VALID_CASE_STUDY_SLUGS)}."
            )

    readme_path = folder / "README.md"
    if not readme_path.exists():
        errors.append("Thiếu file 'README.md' tóm tắt bài làm.")

    # Quét toàn bộ file trong thư mục: kích thước + mẫu hình secret
    for f in folder.rglob("*"):
        if not f.is_file() or f.name == ".gitkeep":
            continue
        size_mb = f.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            errors.append(
                f"File '{f.relative_to(folder)}' nặng {size_mb:.1f}MB (>{MAX_FILE_SIZE_MB}MB) — "
                f"dùng link Google Drive/Kaggle/HuggingFace trong README thay vì commit trực tiếp."
            )
        if f.name in {".env", ".env.local"}:
            errors.append(f"File '{f.relative_to(folder)}' — không được commit file .env.")
        for finding in scan_secrets(f):
            errors.append(f"File '{f.relative_to(folder)}': {finding}.")

    return errors


def validate_pr_files(changed_files: list[str]) -> list[str]:
    """Kiểm tra 1 PR chỉ đụng tới ĐÚNG 1 thư mục submissions/<slug>/ —
    cách ly bắt buộc để nhóm A không thể vô tình/cố ý sửa bài nhóm B hoặc
    các file gốc của repo."""
    errors: list[str] = []
    touched_submission_dirs: set[str] = set()

    for raw_path in changed_files:
        path = raw_path.strip().replace("\\", "/")
        if not path:
            continue
        parts = Path(path).parts
        if len(parts) < 2 or parts[0] != "submissions":
            errors.append(
                f"PR sửa file ngoài 'submissions/': '{path}' — PR nộp bài chỉ được thay đổi "
                f"file trong đúng 1 thư mục submissions/<case-study>_<mã-nhóm>/ của nhóm bạn."
            )
            continue
        touched_submission_dirs.add(parts[1])

    if len(touched_submission_dirs) > 1:
        errors.append(
            f"PR đụng tới NHIỀU thư mục nộp bài cùng lúc: {sorted(touched_submission_dirs)} — "
            f"1 PR chỉ được nộp cho đúng 1 nhóm/1 thư mục."
        )

    if TEMPLATE_NAME in touched_submission_dirs:
        errors.append(f"PR sửa trực tiếp thư mục mẫu '{TEMPLATE_NAME}/' — không được sửa, hãy copy sang thư mục riêng.")

    for slug in touched_submission_dirs:
        folder = SUBMISSIONS_DIR / slug
        if folder.exists():
            errors.extend(validate_folder(folder))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", help="Đường dẫn thư mục nộp bài để kiểm tra cục bộ")
    parser.add_argument("--pr-files", help="File text liệt kê các đường dẫn đã thay đổi trong PR (1 dòng/file)")
    args = parser.parse_args()

    if args.pr_files:
        changed_files = Path(args.pr_files).read_text(encoding="utf-8").splitlines()
        errors = validate_pr_files(changed_files)
    elif args.folder:
        errors = validate_folder(Path(args.folder))
    else:
        parser.print_help()
        return 2

    if errors:
        print("[FAILED] Nộp bài KHÔNG hợp lệ:")
        for e in errors:
            print(f"  ❌ {e}")
        return 1

    print("[PASSED] Nộp bài hợp lệ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
