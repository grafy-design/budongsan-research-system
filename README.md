# 부동산 매입 타당성 리서치 자동화 시스템

> 매물 URL 또는 주소 하나로 **리서치 → 점수 → DOCX/PDF 보고서 → 랜딩 페이지 → 팩트체크 → Vercel 배포**까지 자동 수행하는 Claude Code 스킬.

## 사용법

```bash
/property-review https://byulzip.com/shop_view/?idx=940
/property-review 서울 종로구 부암동 325-3 32억 갤러리+카페+모임
```

## 파이프라인

```
Phase 0   입력 파싱 + 매물 크롤링 + 사전 질문
Phase 0.5 미디어 인벤토리 (이미지/영상 분류·변환·분배)
Phase 1   리서치 — 5개 에이전트 병렬 (용도변경/가격/상권/인테리어/재건축)
Phase 2   점수 산출 — 8차원 × 3시나리오
Phase 3   산출물 빌드 — DOCX 보고서 + HTML 랜딩 페이지
Phase 4   영상 편집 — ffmpeg + VTT 자막
Phase 5   팩트체크 — 4 리뷰어 까칠 무한루핑
Phase 6   빈공간 자동 검증 + PDF 생성
Phase 7   Vercel 배포
```

## 디렉토리 구조

```
├── SKILL.md                    # 메인 스킬 프롬프트 (전체 파이프라인)
├── REVIEW.md                   # 리뷰 기준
├── agents/                     # 에이전트 프롬프트
│   ├── researcher.md           # 리서치 에이전트 (5개 병렬)
│   ├── scorer.md               # 점수 산출 에이전트
│   ├── docx_builder.md         # DOCX 보고서 빌더
│   ├── landing_builder.md      # HTML 랜딩 빌더
│   ├── video_editor.md         # 영상 편집 에이전트
│   ├── reviewer_fact.md        # 팩트체크 리뷰어 (R1)
│   ├── reviewer_visual.md      # 시각 검증 리뷰어 (R2)
│   ├── reviewer_playwright.md  # Playwright 브라우저 리뷰어 (R3)
│   └── reviewer_utf.md         # UTF-8/한글 깨짐 리뷰어 (R4)
├── references/                 # 스타일 가이드 + 데이터 소스
│   ├── landing_design_guide.md # 랜딩 디자인 시스템
│   ├── docx_style_guide.md     # DOCX 스타일 가이드
│   ├── scoring_model.md        # 8차원 점수 모델
│   ├── glossary.md             # 약어 풀어쓰기 용어집
│   ├── data_sources.md         # 데이터 소스 목록
│   ├── gotchas.md              # 12가지 필수 주의사항
│   └── samples/                # 코드 샘플 + JSON 스키마
├── scripts/                    # 유틸리티 스크립트
│   ├── compute_scores.py       # 점수 계산
│   ├── validate_docx_whitespace.py  # DOCX 빈공간 검증
│   ├── validate_images.py      # 이미지 검증
│   ├── validate_links.py       # 링크 검증
│   └── deploy_vercel.sh        # Vercel 배포
├── templates/                  # 템플릿
│   ├── project_config_template.json
│   └── peer_table_template.json
├── assets/fonts/               # 번들 폰트
│   └── NanumGothic.ttf
└── evals/                      # 평가 기준
    └── evals.json
```

## 핵심 특징

- **8차원 점수 모델**: 입지·접근성 / 가격 적정성 / 물리적 상태 / 법적·규제 / 상권·문화 / 목적 적합도 / 희소성·미래가치 / 재무·수익성
- **3 시나리오 분석**: 사용자 선택 기반 시나리오 구성 (라이프스타일 / 상업 / 재건축 등)
- **까칠한 팩트체크**: 4명의 리뷰어가 FAIL 0건까지 무한 반복 검증
- **Playwright 시각 검증**: 스크린샷 기반 명도 대비 검증 (Hero 3중 보호 패턴)
- **DOCX 빈공간 자동 최적화**: python-docx 분석 → spacing 조정 → 재검증 루프
- **PDF 생성**: weasyprint 기반 인쇄 최적화 PDF

## 기술 스택

- Claude Code (CLI)
- python-docx, matplotlib, weasyprint, PyMuPDF
- Playwright (브라우저 검증)
- ffmpeg (영상 인코딩 + VTT 자막)
- Vercel (배포)

## 라이선스

Private — GRAFY Design
