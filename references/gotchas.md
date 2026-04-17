# Gotchas — 실제 발생 실수 + 해결법

> 부암동 프로젝트(v1.0→v3) 전 과정에서 **실제 반복 발생한 실수** 12건.
> Anthropic 스킬 베스트 프랙티스: "Gotchas 섹션이 정확도를 가장 많이 올림."
> 각 항목마다 증상·원인·해결법·검증 방법을 구체적으로 기술.

---

## 1. 링크 깨짐 반복

### 증상
보고서·랜딩에 삽입된 매물 URL 클릭 시 "지역 검색 결과" 페이지로 이동하거나 404 발생.

### 원인
`curl`로 HTTP 200을 받아 "유효"로 판정했으나, 실제로는 매물 사이트가 없는 매물 ID를 지역 검색 루트로 리다이렉트함. 3xx가 아닌 200으로 응답하기 때문에 상태 코드만으로는 판별 불가.

### 해결법

```python
# validate_links.py — 컨텐츠 검증 추가
def validate_property_url(url: str) -> bool:
    resp = requests.get(url, timeout=10, allow_redirects=True)
    if resp.status_code != 200:
        return False
    content = resp.text
    # 매물 페이지 필수 키워드 매칭
    required_keywords = ['매매가', '전용면적', '대지면적']
    optional_keywords = ['평', '억', '만', '㎡', '층']
    has_required = any(kw in content for kw in required_keywords)
    has_optional = sum(1 for kw in optional_keywords if kw in content) >= 2
    return has_required or has_optional
```

### 검증 방법
- `python validate_links.py` 실행 → 모든 URL에 대해 `PASS/FAIL` 출력
- FAIL 건이 0이 될 때까지 URL 수정 후 재검증
- 최종 URL을 브라우저에서 수동 확인 1회

---

## 2. 이미지↔설명 불일치

### 증상
"정원 전경" 캡션 아래에 실내 사진이 표시되거나, "거실" 캡션 아래에 욕실 사진이 나옴.

### 원인
파일명(`garden_01.jpg`, `living_02.jpg`)만 보고 매칭. 실제 이미지 내용을 확인하지 않음. 매물 사이트에서 크롤링한 파일명이 실제 내용과 무관한 경우 빈번.

### 해결법
1. Read 도구로 이미지 직접 시각 확인 후 매칭
2. `validate_images.py`로 perceptual hash 기반 중복 감지

```python
# validate_images.py — 이미지 확인 워크플로
# 1. 모든 이미지를 Read 도구로 직접 확인
# 2. 이미지 내용과 캡션 매칭 검증
# 3. perceptual hash로 중복 이미지 감지

from PIL import Image
import imagehash

def find_duplicates(image_paths: list) -> list:
    hashes = {}
    duplicates = []
    for path in image_paths:
        h = imagehash.phash(Image.open(path))
        for existing_path, existing_hash in hashes.items():
            if h - existing_hash < 5:  # 유사도 임계값
                duplicates.append((path, existing_path))
        hashes[path] = h
    return duplicates
```

### 검증 방법
- 빌드 후 모든 이미지를 Read 도구로 순회하며 캡션과 대조
- 중복 이미지 0건 확인

---

## 3. 영상 자막 중복 (하드서브 + VTT)

### 증상
영상 재생 시 자막이 2줄씩 겹쳐 보임. 하나는 영상에 구워진 하드서브, 하나는 VTT 소프트서브.

### 원인
ffmpeg 인코딩 시 `subtitles` 필터(하드서브)를 적용한 상태에서, HTML `<track>` 태그로 VTT 자막도 동시에 로드.

### 해결법
**VTT 트랙만 사용. ffmpeg subtitles 필터 절대 포함 금지.**

```bash
# 올바른 인코딩 (자막 필터 없음)
ffmpeg -i input.mp4 \
  -vf "scale=-2:720" \
  -c:v libx264 -crf 30 -preset slow \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4

# 절대 사용 금지:
# -vf "subtitles=subtitle.srt"
# -vf "ass=subtitle.ass"
```

```html
<!-- HTML에서 VTT 트랙만 사용 -->
<video controls preload="metadata">
  <source src="video.mp4" type="video/mp4">
  <track kind="subtitles" src="video.vtt" srclang="ko" label="한국어" default>
</video>
```

### 검증 방법
- Playwright로 영상 재생 → 스크린샷 → 자막 1줄만 표시되는지 확인
- ffmpeg 명령어에 `subtitles` / `ass` 필터 grep → 0건

---

## 4. 영상 자막↔화면 불일치

### 증상
VTT 자막이 "주방을 보시면..."이라 말하는 시점에 실제 화면은 거실을 비추고 있음.

### 원인
프레임 샘플링 없이 추정으로 자막 타임코드를 작성. 영상 실제 내용과 동기화하지 않음.

### 해결법

```bash
# 10초 간격 프레임 추출
ffmpeg -i input.mp4 -vf "fps=1/10" -q:v 2 frames/frame_%04d.jpg
```

1. 10초 간격 프레임 추출
2. Read 도구로 각 프레임 시각 확인
3. 프레임 내용 기반으로 자막 타임코드 작성
4. 재확인 후 VTT 파일 최종 확정

### 검증 방법
- 랜덤 5개 타임코드 시점의 프레임을 추출하여 자막 내용 대조
- Playwright 영상 재생으로 최종 확인

---

## 5. 약어 본문 노출 (LOC/PRC/...)

### 증상
보고서 본문에 "LOC 점수: 70" 형태로 약어가 그대로 남아 있음. 차트 PNG 라벨에도 "LOC", "PRC" 약어 노출.

### 원인
치환 로직이 본문 텍스트만 대상. 표 셀, 캡션, alt 텍스트, matplotlib 라벨에는 적용되지 않음.

### 해결법

```python
# 전수 치환 대상
targets = [
    '본문 텍스트',
    '표 셀 내용',
    '이미지 캡션',
    '이미지 alt 텍스트',
    'matplotlib 라벨 (xticks, yticks, legend, title)',
    '빌드 스크립트 내 하드코딩된 문자열',
]

# glossary.md 의 치환 규칙 적용
import re
REPLACEMENTS = {
    'LOC': '입지·접근성', 'PRC': '가격 적정성',
    'PHY': '물리적 상태', 'REG': '법적·규제',
    'MKT': '상권·문화', 'FIT': '목적 적합도',
    'SCR': '희소성·미래가치', 'FIN': '재무·수익성',
}

def expand_all(text: str) -> str:
    for abbr, full in REPLACEMENTS.items():
        text = re.sub(rf'\b{abbr}\b', full, text)
    return text
```

### 검증 방법

```bash
# 산출물 전수 grep
grep -rn '\bLOC\b\|\bPRC\b\|\bPHY\b\|\bREG\b\|\bMKT\b\|\bFIT\b\|\bSCR\b\|\bFIN\b' output/
# 결과: 0건이어야 함
```

---

## 6. DOCX 빈공간

### 증상
DOCX를 PDF로 변환하면 텍스트가 10% 미만인 거의 빈 페이지가 발생.

### 원인
1. page break 과다 (섹션마다 삽입)
2. spacing 과대 (heading before 12pt 등)
3. 이미지 크기 과대 (6인치 이상)

### 해결법

```python
# validate_docx_whitespace.py 핵심 루프
import subprocess
import fitz  # PyMuPDF

def check_blank_pages(docx_path: str) -> list:
    # 1. LibreOffice → PDF 변환
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'pdf', docx_path
    ], check=True)
    pdf_path = docx_path.replace('.docx', '.pdf')

    # 2. PyMuPDF로 페이지별 텍스트 블록 면적 계산
    doc = fitz.open(pdf_path)
    blank_pages = []
    for i, page in enumerate(doc):
        blocks = page.get_text("blocks")
        text_area = sum(
            (b[2]-b[0]) * (b[3]-b[1]) for b in blocks if b[6] == 0
        )
        page_area = page.rect.width * page.rect.height
        fill_ratio = text_area / page_area if page_area > 0 else 0
        if fill_ratio < 0.15:
            blank_pages.append(i + 1)
    return blank_pages

# 3. 빈 페이지 발견 → 수정 → 재검사 루프
while True:
    blanks = check_blank_pages('report.docx')
    if not blanks:
        break
    # page break 제거 + spacing 축소 후 재빌드
    fix_spacing_and_breaks('report.docx', blanks)
```

### 검증 방법
- `validate_docx_whitespace.py` 실행 → 빈 페이지 0건 확인
- 수동으로 PDF 열어 전체 페이지 썸네일 확인

---

## 7. 호칭 잔존

### 증상
보고서에 "대표님", "선생님" 등 호칭이 남아 있음.

### 원인
본문 텍스트만 치환하고, 표 셀·캡션·alt 텍스트에는 치환을 적용하지 않음.

### 해결법
본문 + 표 + 캡션 + alt + 빌드 스크립트까지 전수 grep 후 치환.

```bash
grep -rn '대표님\|선생님\|사장님\|님께서' output/
# 결과: 0건이어야 함
```

### 검증 방법
- 산출물 전체에 대해 호칭 키워드 grep → 0건

---

## 8. 수정흔적 문구

### 증상
보고서에 "수정되었습니다", "반영하였습니다", "업데이트했습니다" 등 AI 자기보고 문구가 남아 있음.

### 원인
수정 작업 시 AI가 자동 생성한 보고 문구가 산출물에 잔존.

### 해결법

```python
FORBIDDEN_PHRASES = [
    '수정되었습니다', '반영하였습니다', '업데이트했습니다',
    '수정 완료', '반영 완료', '변경되었습니다',
    '수정했습니다', '고쳤습니다', '업데이트 완료',
    '이전 버전', '기존 버전', '변경 사항',
]
```

```bash
grep -rn '수정되었습니다\|반영하였습니다\|업데이트했습니다\|수정 완료\|반영 완료' output/
# 결과: 0건이어야 함
```

### 검증 방법
- 금지어 리스트 전수 grep → 0건

---

## 9. 다운로드 파일명

### 증상
랜딩에서 보고서 다운로드 시 파일명이 `report_v3_final.docx` 같은 영문 내부명으로 저장되거나, `download` 속성과 실제 파일명이 불일치.

### 원인
`<a>` 태그의 `href` 경로와 `download` 속성의 파일명이 다르게 설정됨.

### 해결법
파일명 자체를 한글로 저장하고, `download` 속성 없이 직접 서빙.

```html
<!-- 올바른 방법 -->
<a href="assets/부암동_325-3_매입검토_보고서.pdf">PDF 다운로드</a>
<a href="assets/부암동_325-3_매입검토_보고서.docx">DOCX 다운로드</a>

<!-- 잘못된 방법 -->
<a href="assets/report.pdf" download="부암동_보고서.pdf">다운로드</a>
```

### 검증 방법
- 브라우저에서 다운로드 클릭 → 파일명 확인
- `href` 경로의 실제 파일 존재 여부 확인

---

## 10. Vercel 100MB 제한

### 증상
`vercel --prod` 배포 시 "File size exceeds 100MB limit" 에러.

### 원인
임장 영상 원본(1~3GB)을 압축 없이 그대로 배포 시도.

### 해결법

```bash
# CRF 30 + scale 720 압축
ffmpeg -i input.mp4 \
  -vf "scale=-2:720" \
  -c:v libx264 -crf 30 -preset slow \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4

# 파일 크기 확인
ls -lh output.mp4
# 100MB 미만인지 확인
```

### 검증 방법

```bash
# 배포 전 크기 확인
find output/landing/ -size +100M -type f
# 결과: 0건이어야 함
```

---

## 11. WSL 셧다운으로 ffmpeg 손상

### 증상
ffmpeg 인코딩 중 WSL이 셧다운되어 출력 파일의 moov atom이 미완성. 영상이 재생되지 않거나, 시크(seek)가 불가능.

### 원인
`movflags +faststart` 옵션은 인코딩 완료 후 moov atom을 파일 앞으로 이동시키는데, 이 과정에서 WSL 셧다운이 발생하면 atom 이동이 중단됨.

### 해결법

```bash
# nohup으로 실행
nohup ffmpeg -i input.mp4 -vf "scale=-2:720" \
  -c:v libx264 -crf 30 -preset slow \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4 > ffmpeg.log 2>&1 &

# 완료 확인
wait $!
```

### 검증 방법

```bash
# moov atom 존재 확인
ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1 output.mp4
# 정상: format_name=mov,mp4,m4a,3gp,3g2,mj2

# 시크 가능 확인
ffprobe -v error -show_entries format_tags=major_brand -of default=noprint_wrappers=1 output.mp4
```

---

## 12. 메타 섹션 의미 불명

### 증상
보고서의 "점수의 점수", "민감도 분석" 같은 메타 섹션이 사용자(의뢰인)에게 의미 전달 실패. "이게 뭔가요?" 피드백.

### 원인
내부 분석 용어를 그대로 사용자 대면 보고서에 노출. 사용자 관점의 UX 리뷰 누락.

### 해결법
1. **의미 불명 섹션**: 본문에서 삭제하고 Appendix로 이동
2. **남기는 경우**: 사용자 친화적 제목으로 변경
   - "점수의 점수" → "이 분석의 신뢰도"
   - "민감도 분석" → "어떤 조건이 바뀌면 결과가 달라지나?"
   - "Devil's Advocate" → "이 매물을 사면 안 되는 이유"
3. **결론 박스 (두괄식)**: 각 섹션 최상단에 "한 줄 결론" 박스 배치

### 검증 방법
- 사용자 관점 UX 리뷰어(reviewer-visual)가 "의미 불명 섹션 0건" 확인
- 비전문가에게 보고서를 보여주고 "이해 안 되는 부분" 피드백 수집
