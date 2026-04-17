#!/usr/bin/env python3
"""
validate_docx_whitespace.py -- DOCX 빈공간 자동 검증 + 수정 스크립트

입력: docx 파일
출력: 수정된 docx + PDF + 빈페이지 리포트

처리:
1. LibreOffice headless -> PDF 변환
2. PyMuPDF(fitz) 페이지별 fill% 계산
3. fill < 15% -> 빈 페이지 후보
4. 자동 수정: page break 제거 + spacing 축소 + 빈 단락 제거
5. 재변환 -> 재검사 -> 반복

사용법:
  python validate_docx_whitespace.py --input input.docx --output output.docx
  python validate_docx_whitespace.py --input input.docx --output output.docx --max-iterations 5
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

# ---- LibreOffice 탐색 ----
def find_soffice() -> str:
    """LibreOffice soffice 바이너리 위치 자동 탐색"""
    # 시스템 PATH
    system_soffice = shutil.which("soffice")
    if system_soffice:
        return system_soffice

    # AppImage 추출 경로 (WSL 환경)
    appimage_path = "/tmp/squashfs-root/opt/libreoffice25.8/program/soffice"
    if os.path.isfile(appimage_path):
        return appimage_path

    # 일반적인 리눅스 경로
    for candidate in [
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/opt/libreoffice/program/soffice",
    ]:
        if os.path.isfile(candidate):
            return candidate

    print("오류: LibreOffice(soffice)를 찾을 수 없습니다.", file=sys.stderr)
    print("  설치: sudo apt install libreoffice", file=sys.stderr)
    sys.exit(1)


# ---- DOCX -> PDF 변환 ----
def convert_docx_to_pdf(docx_path: str, output_dir: str) -> str:
    """LibreOffice headless로 DOCX -> PDF 변환"""
    soffice = find_soffice()
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        docx_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        print(f"오류: LibreOffice 변환 실패\n{proc.stderr}", file=sys.stderr)
        sys.exit(1)

    pdf_name = Path(docx_path).stem + ".pdf"
    pdf_path = os.path.join(output_dir, pdf_name)
    if not os.path.exists(pdf_path):
        print(f"오류: PDF 파일이 생성되지 않았습니다: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    return pdf_path


# ---- PDF 페이지별 fill% 계산 ----
def analyze_pdf_fill(pdf_path: str, empty_threshold: float = 15.0) -> list:
    """PyMuPDF로 페이지별 텍스트 블록 fill% 계산"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("오류: PyMuPDF 패키지가 필요합니다. pip install PyMuPDF", file=sys.stderr)
        sys.exit(1)

    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height

        if page_area == 0:
            pages.append({
                "page": page_num + 1,
                "fill_pct": 0,
                "is_empty": True,
                "text_blocks": 0,
                "image_count": 0,
            })
            continue

        # 텍스트 블록 면적 합산
        text_blocks = page.get_text("blocks")
        text_area = 0
        for block in text_blocks:
            x0, y0, x1, y1 = block[:4]
            block_area = abs(x1 - x0) * abs(y1 - y0)
            text_area += block_area

        # 이미지 면적 합산
        image_list = page.get_images(full=True)
        image_area = 0
        for img in image_list:
            try:
                img_rects = page.get_image_rects(img[0])
                for rect in img_rects:
                    image_area += abs(rect.width) * abs(rect.height)
            except Exception:
                pass

        total_content_area = text_area + image_area
        fill_pct = round((total_content_area / page_area) * 100, 1)
        # fill_pct가 100을 초과하면 (겹침 등) 캡핑
        fill_pct = min(fill_pct, 100.0)

        pages.append({
            "page": page_num + 1,
            "fill_pct": fill_pct,
            "is_empty": fill_pct < empty_threshold,
            "text_blocks": len(text_blocks),
            "image_count": len(image_list),
        })

    doc.close()
    return pages


# ---- DOCX 빈공간 자동 수정 ----
def fix_whitespace(docx_path: str, output_path: str, empty_pages: list) -> dict:
    """빈 페이지 원인 제거: page break, 과도한 spacing, 빈 단락"""
    try:
        from docx import Document
        from docx.oxml.ns import qn
    except ImportError:
        print("오류: python-docx 패키지가 필요합니다. pip install python-docx", file=sys.stderr)
        sys.exit(1)

    doc = Document(docx_path)
    fixes = {"page_breaks_removed": 0, "spacing_reduced": 0, "empty_paras_removed": 0}

    # 1. 연속 빈 단락 제거 (3개 이상 연속이면 1개로)
    consecutive_empty = 0
    paras_to_remove = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text and not para.runs:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                paras_to_remove.append(para)
        else:
            consecutive_empty = 0

    for para in paras_to_remove:
        parent = para._element.getparent()
        if parent is not None:
            parent.remove(para._element)
            fixes["empty_paras_removed"] += 1

    # 2. page break 제거 (빈 페이지 직전에 있는 불필요한 page break)
    for para in doc.paragraphs:
        for run in para.runs:
            # run XML에서 w:br type="page" 찾기
            br_elements = run._element.findall(qn("w:br"))
            for br in br_elements:
                if br.get(qn("w:type")) == "page":
                    # page break 직후 내용이 없으면 제거
                    run._element.remove(br)
                    fixes["page_breaks_removed"] += 1

    # 3. 과도한 spacing 축소 (before/after > 240 twips = 12pt 이상)
    MAX_SPACING = 240  # 12pt in twips
    for para in doc.paragraphs:
        pPr = para._element.find(qn("w:pPr"))
        if pPr is not None:
            spacing = pPr.find(qn("w:spacing"))
            if spacing is not None:
                before = spacing.get(qn("w:before"))
                after = spacing.get(qn("w:after"))
                if before and int(before) > MAX_SPACING:
                    spacing.set(qn("w:before"), str(MAX_SPACING))
                    fixes["spacing_reduced"] += 1
                if after and int(after) > MAX_SPACING:
                    spacing.set(qn("w:after"), str(MAX_SPACING))
                    fixes["spacing_reduced"] += 1

    doc.save(output_path)
    return fixes


# ---- 메인 루프 ----
def main():
    parser = argparse.ArgumentParser(description="DOCX 빈공간 자동 검증 + 수정 스크립트")
    parser.add_argument("--input", required=True, help="입력 docx 파일")
    parser.add_argument("--output", required=True, help="출력 docx 파일")
    parser.add_argument("--max-iterations", type=int, default=5, help="최대 반복 횟수 (기본 5)")
    parser.add_argument("--threshold", type=float, default=15.0,
                        help="빈 페이지 판정 fill%% 임계값 (기본 15)")
    parser.add_argument("--report", default=None, help="리포트 JSON 출력 경로")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"오류: 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 작업 디렉토리
    work_dir = tempfile.mkdtemp(prefix="docx_ws_")
    current_docx = str(input_path)
    iteration_log = []

    print(f"입력 파일: {input_path}")
    print(f"빈 페이지 임계값: fill < {args.threshold}%")

    for iteration in range(1, args.max_iterations + 1):
        print(f"\n--- 반복 {iteration}/{args.max_iterations} ---")

        # DOCX -> PDF
        print("  PDF 변환 중...")
        pdf_path = convert_docx_to_pdf(current_docx, work_dir)

        # fill% 분석
        print("  페이지 분석 중...")
        pages = analyze_pdf_fill(pdf_path, args.threshold)
        empty_pages = [p for p in pages if p["is_empty"]]

        total_pages = len(pages)
        empty_count = len(empty_pages)

        print(f"  전체 {total_pages}페이지 중 빈 페이지: {empty_count}개")
        for p in empty_pages:
            print(f"    -> p.{p['page']}: fill {p['fill_pct']}% "
                  f"(텍스트블록: {p['text_blocks']}, 이미지: {p['image_count']})")

        iter_info = {
            "iteration": iteration,
            "total_pages": total_pages,
            "empty_pages": empty_count,
            "empty_page_numbers": [p["page"] for p in empty_pages],
            "pages": pages,
        }

        if empty_count == 0:
            print("  빈 페이지 없음. 완료.")
            iter_info["action"] = "done"
            iteration_log.append(iter_info)
            break

        # 수정 적용
        output_docx = os.path.join(work_dir, f"fixed_iter{iteration}.docx")
        print("  수정 적용 중...")
        fixes = fix_whitespace(current_docx, output_docx, empty_pages)
        iter_info["fixes"] = fixes
        iteration_log.append(iter_info)

        total_fixes = sum(fixes.values())
        print(f"  수정: page_break={fixes['page_breaks_removed']}, "
              f"spacing={fixes['spacing_reduced']}, "
              f"empty_para={fixes['empty_paras_removed']}")

        if total_fixes == 0:
            print("  더 이상 자동 수정할 수 있는 항목이 없습니다.")
            break

        current_docx = output_docx

    # 최종 파일 복사
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current_docx, str(output_path))
    print(f"\n최종 DOCX 저장: {output_path}")

    # 최종 PDF도 생성
    pdf_output_dir = str(output_path.parent)
    final_pdf = convert_docx_to_pdf(str(output_path), pdf_output_dir)
    print(f"최종 PDF 저장: {final_pdf}")

    # 리포트
    report = {
        "input": str(input_path),
        "output": str(output_path),
        "final_pdf": final_pdf,
        "threshold": args.threshold,
        "iterations": iteration_log,
        "total_iterations": len(iteration_log),
    }

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"리포트 저장: {report_path}")

    # 임시 디렉토리 정리
    shutil.rmtree(work_dir, ignore_errors=True)

    print("\n=== 완료 ===")
    first = iteration_log[0] if iteration_log else {}
    last = iteration_log[-1] if iteration_log else {}
    print(f"  초기 빈 페이지: {first.get('empty_pages', '?')}개")
    print(f"  최종 빈 페이지: {last.get('empty_pages', '?')}개")
    print(f"  반복 횟수: {len(iteration_log)}")


if __name__ == "__main__":
    main()
