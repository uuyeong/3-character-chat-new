import argparse
import pathlib
import re
import sys
from typing import List

# --- PDF 텍스트 추출기: pymupdf 우선, 실패하면 pdfminer ---

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        import fitz  # pymupdf
        doc = fitz.open(pdf_path)
        pages = []
        for p in doc:
            pages.append(p.get_text("text"))
        return "\n\n".join(pages)
    except Exception:
        # fallback
        try:
            from pdfminer.high_level import extract_text
            return extract_text(pdf_path)
        except Exception as e:
            raise RuntimeError(f"PDF 추출 실패: {pdf_path} ({e})")


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 머리말/바닥글, 페이지번호 흔적 약하게 정리(보수적으로)
    text = re.sub(r"\n\s*Page\s+\d+\s*\n", "\n\n", text, flags=re.I)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(\n) +", r"\1", text)
    return text.strip()


def chunk_paragraphs(text: str, max_chars: int = 900) -> List[str]:
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    out: List[str] = []
    for b in blocks:
        if len(b) <= max_chars:
            out.append(b)
        else:
            s = 0
            while s < len(b):
                e = min(s + max_chars, len(b))
                out.append(b[s:e].strip())
                s = e
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="PDF 폴더 경로")
    ap.add_argument("--dst", required=True, help="출력 텍스트 폴더 경로")
    ap.add_argument("--prefix", default="memories_all", help="출력 파일 접두어")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    dst = pathlib.Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(src.glob("**/*.pdf"))
    if not pdf_files:
        print(f"[정보] PDF 없음: {src}")
        sys.exit(0)

    for pdf in pdf_files:
        print(f"[처리] {pdf}")
        raw = extract_text_from_pdf(str(pdf))
        cleaned = clean_text(raw)
        chunks = chunk_paragraphs(cleaned, max_chars=900)
        # 파일명 기반으로 출력 파일 생성
        stem = pdf.stem.lower().replace(" ", "_")
        out_path = dst / f"{args.prefix}_{stem}.txt"
        out_text = "\n\n".join(chunks)
        out_path.write_text(out_text, encoding="utf-8")
        print(f"  → {out_path} ({len(chunks)} chunks)")

    print("[완료] 변환이 끝났습니다. 임베딩 재빌드를 원하면 chardb_embedding 삭제 후 재기동하세요.")


if __name__ == "__main__":
    main()
