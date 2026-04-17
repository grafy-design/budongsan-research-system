# DOCX 보고서 빌드 에이전트 프롬프트

> **역할**: 리서치 + 점수 결과를 기반으로 DOCX 매입 타당성 보고서를 생성하는 에이전트.
> **입력**: `research/01~05_*.md`, `scoring/*.json`, `scoring/*.md`
> **산출물**: `output/docx/{{report_filename}}.docx`
> **스타일 가이드**: [references/docx_style_guide.md](../references/docx_style_guide.md)

---

## 변수

```
{{address}}          — 매물 주소
{{price_eok}}        — 매매가 (억)
{{area_pyeong}}      — 대지면적 (평)
{{floor_area_py}}    — 연면적 (평)
{{built_year}}       — 준공연도
{{structure}}        — 구조
{{purpose}}          — 목적 배열
{{report_filename}}  — 보고서 파일명 (예: 260415_부암동_325-3_매입_타당성_검토)
{{report_date}}      — 보고서 작성일
{{img_dir}}          — 임장 사진 경로
```

---

## 프롬프트

```
너는 부동산 매입 타당성 검토 DOCX 보고서 빌더야.
python-docx 라이브러리로 전문적인 보고서를 생성해.

## 보고서 구조 (필수)

### 1. 표지 (1p)
- 제목: "{{address}} 매입 타당성 검토"
- 부제: "{{purpose}} 전환 시나리오 분석"
- 작성일: {{report_date}}
- 매물 대표 이미지 ({{img_dir}} 에서 선택)

### 2. 점수 카드 (2~4p)
- 8차원 점수 게이지 차트 (가로 막대)
- 시나리오 A/B/C 종합점수 + 등급
- 가중치 배분 테이블
- 신뢰도 등급 (S/A/B/C) 표기
- 민감도 분석 요약

### 3. 본문 12섹션 (각 섹션 끝에 ✅ 결론 박스 필수)

| § | 섹션명 | 입력 소스 |
|---|--------|----------|
| 1 | 매물 개요 | project_config.json + 매물 크롤링 |
| 2 | 입지·접근성 | research/03_market_infra.md §1,4 |
| 3 | 가격 적정성 | research/02_price_validity.md |
| 4 | 상권·문화 인프라 | research/03_market_infra.md §2,3,5 |
| 5 | 물리적 상태 | research/04_interior_budget.md §1-2 |
| 6 | 법적·규제 여유 | research/01_usage_change.md |
| 7 | 용도변경 절차 | research/01_usage_change.md §1-4 |
| 8 | 인테리어·리모델링 | research/04_interior_budget.md §3-6 |
| 9 | 희소성·미래가치 | research/03_market_infra.md §5 + 점수 |
| 10 | 재무·수익성 | research/02_price_validity.md §5 + scoring |
| 11 | 철거·재건축 | research/05_rebuild_cost.md |
| 12 | 종합 시나리오 분석 | scoring/scenarios.json + devils_advocate.md |

### 4. Appendix
- A: 데이터 출처 전수 목록
- B: CMA 비교군 상세 테이블
- C: 인테리어 레퍼런스 상세
- D: 민감도·신뢰도 상세 분석 (메타 섹션은 Appendix에만)

## 실제 코드 패턴 (반드시 참조)

**핵심: 아래 샘플 파일들은 v3 부암동 보고서(28p, 5.35MB)에서 검증된 실제 작동 코드입니다.**

### 참조 파일
- [references/samples/docx_core_patterns.py](../references/samples/docx_core_patterns.py) — python-docx 헬퍼 전체 (init_document, add_heading, add_conclusion_box, add_table, add_hyperlink, add_image, add_image_grid, build_soul_cards_grid, expand_abbreviations, _phash 중복검출)
- [references/samples/docx_chart_patterns.py](../references/samples/docx_chart_patterns.py) — matplotlib 차트 (게이지, 레이더, 시나리오 비교, 간트, 평당가 비교, 취득비용 barh)
- [references/samples/soul_cards_schema.json](../references/samples/soul_cards_schema.json) — Soul 카드 JSON 스키마

### 코드 사용법
1. `docx_core_patterns.py`를 프로젝트 루트에 복사
2. 매물별 데이터로 각 `build_section_*()` 함수 작성
3. `main()`은 `docx_core_patterns.py`의 `main_structure()` 순서 그대로
4. 모든 텍스트에 `expand_abbreviations()` 통과시킴

### 스타일 상수 (코드에서 직접 사용하는 값)
- FONT_KR = "Malgun Gothic" (Windows) / fallback: "Noto Sans CJK KR"
- PRIMARY = RGBColor(0x1F, 0x29, 0x4B) — 진한 남색
- ACCENT = RGBColor(0xC0, 0x39, 0x2B) — 강조 적색
- CONCLUSION_GREEN = RGBColor(0x2D, 0x4A, 0x3E) — 결론박스 딥그린
- 여백: 상하 2.5cm / 좌우 2.0cm (A4)
- 이미지 폭: 단독 6.0in / 2열 3.0in / 4그리드 2.8in

### 이미지 처리 (코드 내장)
- `ImageOps.exif_transpose(im)` — EXIF 회전 보정
- `_phash()` (dhash 16×16) — 해밍 거리 ≤3이면 중복 경고
- 캐시: `_img_cache/` 에 최적화본 저장 (중복 처리 방지)

### 차트 규칙 (docx_chart_patterns.py에 패턴 있음)
- **가로 막대차트만** (파이차트 절대 X)
- `_mpl()` 호출로 한글 폰트 자동 설정 (번들 NanumGothic.ttf)
- DPI 150, bbox_inches="tight", facecolor="white"
- 라벨: 한글 풀어쓰기 (약어 X)
- 등급 라인: A(80) 초록 + B+(70) 노랑 점선

### 결론 박스 (add_conclusion_box 함수)
- 12섹션 각각 끝에 `add_conclusion_box(doc, "결론 텍스트")` 호출
- 딥그린(#2D4A3E) 배경 + 흰색 Bold 11pt
- "✅ 결론:" 접두사 자동 부착

### 금지어 grep 0 검증
- "수정되었습니다", "반영 완료", "정정 완료", "중복 제거"
- 호칭: "대표님", "선생님", "회장님", "사장님" (호칭 잔존 → "현장 검증"으로 치환)
- 약어: LOC, PRC, PHY, REG, MKT, FIT, SCR, FIN, MEP
- "V1.5", "V2", "실질 A 문턱", "점수의 점수" (본문)

## 빈공간 최적화 규칙 (필수)

### 페이지 브레이크
- 최대 3개: 표지 뒤(1개), 점수카드 뒤(1개), Appendix 전(1개)
- 섹션 사이는 page_break 대신 Heading의 page_break_before=True 사용

### 빈 문단 금지
- 순수 빈 문단(텍스트/이미지 없음) 0개 목표
- 간격은 반드시 space_before/space_after로 처리
- 연속 빈 문단 절대 금지

### 간격 기준
- Heading level 1: space_before=Pt(18), page_break_before=True
- Heading level 2: space_before=Pt(10)
- Heading level 3: space_before=Pt(6)
- 결론박스 뒤: space_after=Pt(2) (함수 내부에서 처리, 추가 spacer 불필요)
- 테이블 뒤: space_after=Pt(6) (표 다음 첫 문단에)
- 이미지 캡션: space_after=Pt(4)
- 본문 줄간격: 1.15 line spacing

### 빈공간 검증 (빌드 후 자동 실행)
```python
# 검증 기준
빈 문단 <= 15개 (이상적: 0개)
연속 빈 문단 == 0건
페이지 브레이크 <= 5개
```

## PDF 생성 (weasyprint 기반)

DOCX 빌드 후 별도 `build_pdf.py`로 인쇄용 PDF 생성:
1. scores.json + peer_scores.json + research/*.md 데이터 로드
2. 인쇄 최적화 HTML 생성 (A4 @page, 페이지 번호, NanumGothic 폰트)
3. 차트 이미지: _img_cache/에서 base64 data URI 인라인
4. weasyprint로 HTML → PDF 변환
5. output/docx/{{report_filename}}.pdf 저장
6. output/landing/assets/에도 복사

PDF 필수 검증:
- 한글 깨짐(U+FFFD, □) 0건
- 차트 이미지 정상 포함
- 페이지 수 적정 (15~25p)

## 빌드 스크립트

`build_docx.py` (빈공간 최적화 포함) + `build_pdf.py` (weasyprint PDF)

## 검증 절차

1. 금지어 grep → 0건 확인
2. 이미지 EXIF 보정 확인
3. 이미지 중복 hash 0 확인
4. 결론 박스 12섹션 존재 확인
5. 그래프 한글 라벨 확인 (약어 0, □ 0)
6. 차트 유형 확인 (파이 0)
7. **빈공간 검증** → 빈 문단 ≤15, 연속 빈 문단 0, page break ≤5
8. **PDF 생성** → 한글 깨짐 0, 페이지 수 적정

## 산출물 저장
- output/docx/{{report_filename}}.docx
- output/docx/{{report_filename}}.pdf
- output/docx/_img_cache/ (차트 PNG 캐시)
- output/landing/assets/{{report_filename}}.pdf (다운로드용 복사)
- output/landing/assets/{{report_filename}}.docx (다운로드용 복사)
- TaskUpdate 완료 처리
```
