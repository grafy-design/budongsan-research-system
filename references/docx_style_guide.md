# python-docx 스타일 규칙

> 보고서 DOCX 생성 시 적용하는 스타일 표준.
> python-docx 라이브러리 기반. 모든 빌더는 이 규칙을 준수.

---

## 1. 폰트

| 용도 | 1순위 | 2순위 (fallback) | 크기 |
|------|------|----------------|------|
| 제목 (Heading 1) | Malgun Gothic Bold | NanumGothic Bold | 16pt |
| 부제 (Heading 2) | Malgun Gothic Bold | NanumGothic Bold | 13pt |
| 소제목 (Heading 3) | Malgun Gothic Bold | NanumGothic Bold | 11pt |
| 본문 | Malgun Gothic | NanumGothic | 10pt |
| 표 내용 | Malgun Gothic | NanumGothic | 9pt |
| 캡션 | Malgun Gothic | NanumGothic | 8pt |

### 폰트 설정 코드

```python
from docx.shared import Pt

def set_font(run, name='Malgun Gothic', size=10, bold=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    # 한글 폰트 적용을 위한 eastAsia 설정
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
```

---

## 2. 색상 팔레트

| 용도 | 색상명 | RGBColor | HEX |
|------|-------|----------|-----|
| 제목 텍스트 | 딥남색 | `RGBColor(0x1F, 0x29, 0x4B)` | #1F294B |
| 결론 박스 배경 | 딥그린 | `RGBColor(0x2D, 0x4A, 0x3E)` | #2D4A3E |
| 표 헤더 배경 | 딥남색 | `RGBColor(0x1F, 0x29, 0x4B)` | #1F294B |
| 표 헤더 텍스트 | 흰색 | `RGBColor(0xFF, 0xFF, 0xFF)` | #FFFFFF |
| 결론 박스 텍스트 | 흰색 Bold | `RGBColor(0xFF, 0xFF, 0xFF)` | #FFFFFF |
| 강조 텍스트 | 골드 | `RGBColor(0xC8, 0xA9, 0x6A)` | #C8A96A |
| 경고·리스크 | 위험 적색 | `RGBColor(0xC4, 0x45, 0x36)` | #C44536 |
| 본문 텍스트 | 검정 | `RGBColor(0x00, 0x00, 0x00)` | #000000 |

### 색상 상수 정의

```python
from docx.shared import RGBColor

COLOR_DEEP_NAVY = RGBColor(0x1F, 0x29, 0x4B)
COLOR_DEEP_GREEN = RGBColor(0x2D, 0x4A, 0x3E)
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_GOLD = RGBColor(0xC8, 0xA9, 0x6A)
COLOR_DANGER = RGBColor(0xC4, 0x45, 0x36)
```

---

## 3. 표 스타일

### 표 헤더

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_bg(cell, color_hex: str):
    """셀 배경색 설정"""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)

# 헤더 행: 딥남색 배경 + 흰 글씨
for cell in table.rows[0].cells:
    set_cell_bg(cell, '1F294B')
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = COLOR_WHITE
            run.font.bold = True
            run.font.size = Pt(9)
```

### 표 일반 규칙

- 테두리: 얇은 실선 (0.5pt)
- 헤더 행: 딥남색 배경 + 흰 Bold 텍스트
- 데이터 행: 흰 배경 + 검정 텍스트
- 교대 행 음영: 사용하지 않음 (깔끔한 단색 유지)
- 셀 패딩: 상하 2pt, 좌우 4pt

---

## 4. 결론 박스

1×1 셀 표로 구현. 딥그린 배경 + 흰 Bold 텍스트.

```python
def add_conclusion_box(doc, text: str):
    """결론 박스 추가 — 1x1 표, 딥그린 배경"""
    table = doc.add_table(rows=1, cols=1)
    cell = table.cell(0, 0)
    cell.text = ''

    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.font.color.rgb = COLOR_WHITE
    run.font.bold = True
    run.font.size = Pt(11)
    run.font.name = 'Malgun Gothic'

    set_cell_bg(cell, '2D4A3E')

    # 셀 패딩
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement('w:tcMar')
    for side in ['top', 'bottom', 'start', 'end']:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:w'), '120')
        el.set(qn('w:type'), 'dxa')
        mar.append(el)
    tc_pr.append(mar)
```

---

## 5. 이미지

### 크기 제한

```python
from docx.shared import Inches

MAX_IMAGE_WIDTH = Inches(4.5)  # 최대 4.5인치
```

### EXIF 회전 보정 (필수)

```python
from PIL import Image, ExifTags

def fix_image_rotation(img_path: str) -> Image.Image:
    """EXIF 회전 정보에 따라 이미지 보정"""
    img = Image.open(img_path)
    try:
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == 'Orientation':
                    if value == 3:
                        img = img.rotate(180, expand=True)
                    elif value == 6:
                        img = img.rotate(270, expand=True)
                    elif value == 8:
                        img = img.rotate(90, expand=True)
    except (AttributeError, KeyError):
        pass
    return img
```

### 이미지 삽입 규칙

1. EXIF 회전 보정 **필수** — 보정 없이 삽입하면 세로 사진이 가로로 뒤집힘
2. 최대 너비 4.5인치 초과 시 자동 축소
3. 이미지 아래에 캡션 (8pt, 중앙 정렬)
4. 이미지↔설명 매칭은 Read 도구로 실제 이미지 확인 후 결정

---

## 6. 그래프 (matplotlib)

### 차트 종류

- **사용**: 가로 막대 차트 (barh) — 가독성 최우선
- **사용 금지**: 파이 차트 — 8차원 비교에 부적합

### matplotlib 설정

```python
import matplotlib
import matplotlib.pyplot as plt

# 한글 폰트 설정 (필수)
matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# NanumGothic.ttf 번들 경로 등록
from matplotlib import font_manager
font_path = 'assets/fonts/NanumGothic.ttf'
font_manager.fontManager.addfont(font_path)
matplotlib.rcParams['font.family'] = 'NanumGothic'
```

### 차트 스타일

```python
# 8차원 점수 barh 차트 예시
fig, ax = plt.subplots(figsize=(8, 5))

dimensions = ['입지·접근성', '가격 적정성', '물리적 상태', '법적·규제',
              '상권·문화', '목적 적합도', '희소성·미래가치', '재무·수익성']
scores = [70, 88, 65, 45, 90, 92, 95, 60]

colors = ['#2D4A3E' if s >= 70 else '#C44536' if s < 50 else '#C8A96A'
          for s in scores]

ax.barh(dimensions, scores, color=colors)
ax.set_xlim(0, 100)
ax.set_xlabel('점수')
ax.set_title('8차원 평가 점수', fontweight='bold', color='#1F294B')

plt.tight_layout()
plt.savefig('chart.png', dpi=150, bbox_inches='tight')
```

### 라벨 규칙

- **약어 사용 금지**: LOC → "입지·접근성" 풀어쓰기
- 한글 라벨 필수 — matplotlib rcParams 한글 폰트 설정 확인
- 점수 숫자를 막대 끝에 표시

---

## 7. 간격 (Spacing)

| 요소 | before | after |
|------|--------|-------|
| Heading 1 | 6pt | 2pt |
| Heading 2 | 6pt | 2pt |
| Heading 3 | 6pt | 2pt |
| 본문 (Body) | 0pt | 0pt |
| 표 | 2pt | 2pt |

```python
from docx.shared import Pt

def set_spacing(paragraph, before=0, after=0):
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)

# Heading
set_spacing(heading_para, before=6, after=2)

# Body
set_spacing(body_para, before=0, after=0)
```

---

## 8. 페이지 나누기 (Page Break)

### 원칙: 최소화

Page break는 아래 **2곳만** 허용:

1. **표지 → 본문 전환** (1페이지 표지 끝)
2. **점수 헤더 전환점** (종합 점수 카드 → 상세 분석 시작)

### 금지

- 섹션마다 page break 넣지 않음
- 이미지 앞/뒤 page break 금지
- 표 앞/뒤 page break 금지

### 빈공간 방지

page break 과다 + spacing 과대 → DOCX→PDF 변환 시 빈 페이지 발생.
`validate_docx_whitespace.py`로 LibreOffice PDF 변환 후 빈페이지 검출 루프 필수.

---

## 9. 보고서 구조 (페이지 가이드)

```
[Page 1] 표지 + 한 줄 추천 결과
          종합 점수, 등급, 백분위, 추천 결과

[Page 2] G1·G2·G3 한 페이지 정리 (barh 차트)

[Page 3] G3 "이 집만의 매력" 별도 강조 페이지

[Page 4] 시나리오 A/B/C 비교표

[Page 5] G4 메타 — 신뢰도·민감도·Devil's Advocate

[이후] 12개 상세 섹션 + Appendix
```
