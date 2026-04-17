# REVIEW — property-review 스킬 구조·내용 검증

- **검증자**: skill-reviewer
- **일시**: 2026-04-16 (iter#3 최종)
- **대상**: `/home/grafy/.claude/skills/property-review/`
- **모드**: 까칠 무한루핑 (0건까지)
- **최종 상태**: ✅ PASS — 10항목 전수 PASS

---

## Iteration 로그

| iter | FAIL | 조치 |
|------|------|------|
| #1 | 6건 (항목4: 3건, 항목10: 3건) | Lead에게 보고 → 수정 요청 |
| #2 | 2건 (항목10-A: 가중치, 항목10-C: 등급) | Lead에게 재보고 → scorer.md 가중치+등급 수정 요청 |
| #3 | **0건** | **전 항목 PASS** |

---

## 체크리스트 10항목

### 1. SKILL.md 프론트매터 유효성 — ✅ PASS

| 항목 | 값 | 검증 |
|------|---|------|
| name | `property-review` | 18자, 소문자+하이픈, XML태그 X, "anthropic"/"claude" X |
| description | 부동산 매물 매입 타당성... (약 630자) | 비어있지 않음, 1024자 이내, XML태그 X, 3인칭 서술 |

---

### 2. SKILL.md 본문 500줄 이내 — ✅ PASS

- `wc -l SKILL.md` → **175줄** (500 미만)

---

### 3. Progressive Disclosure — ✅ PASS

SKILL.md에서 참조하는 14개 파일 확인. 4개 에이전트 파일이 references/ 파일을 상호 참조하나, 해당 references 파일은 SKILL.md에서도 직접 참조되므로 실질적 로딩 깊이는 1단계.

---

### 4. 모든 참조 파일 존재 — ✅ PASS (iter#1 FAIL → iter#3 PASS)

**수정 이력**:
- `scripts/build_report.py` 참조 → SKILL.md:98 + docx_builder.md:105에서 제거 (동적 생성 방식) ✅
- `agents/scorer.md` → SKILL.md:78에 링크 추가 ✅
- `references/glossary.md` → SKILL.md:71에 링크 추가 ✅

**현재 SKILL.md 참조 파일 전수 (14개)**:

| # | 참조 파일 | SKILL.md 위치 | 존재 |
|---|---------|-------------|------|
| 1 | agents/researcher.md | :59 | ✅ |
| 2 | references/data_sources.md | :70 | ✅ |
| 3 | references/glossary.md | :71 | ✅ |
| 4 | references/scoring_model.md | :77 | ✅ |
| 5 | agents/scorer.md | :78 | ✅ |
| 6 | agents/docx_builder.md | :96 | ✅ |
| 7 | references/docx_style_guide.md | :97 | ✅ |
| 8 | agents/landing_builder.md | :106 | ✅ |
| 9 | references/landing_design_guide.md | :107 | ✅ |
| 10 | agents/video_editor.md | :116 | ✅ |
| 11 | agents/reviewer_fact.md | :127 | ✅ |
| 12 | agents/reviewer_visual.md | :127 | ✅ |
| 13 | agents/reviewer_playwright.md | :127 | ✅ |
| 14 | references/gotchas.md | :162 | ✅ |

---

### 5. 디렉토리 구조 완결성 — ✅ PASS

```
property-review/
├── SKILL.md                          (1)
├── references/                       (6)
│   ├── data_sources.md
│   ├── docx_style_guide.md
│   ├── glossary.md
│   ├── gotchas.md
│   ├── landing_design_guide.md
│   └── scoring_model.md
├── agents/                           (8)
│   ├── docx_builder.md
│   ├── landing_builder.md
│   ├── researcher.md
│   ├── reviewer_fact.md
│   ├── reviewer_playwright.md
│   ├── reviewer_visual.md
│   ├── scorer.md
│   └── video_editor.md
├── scripts/                          (5)
│   ├── compute_scores.py
│   ├── deploy_vercel.sh
│   ├── validate_docx_whitespace.py
│   ├── validate_images.py
│   └── validate_links.py
├── templates/                        (2)
│   ├── peer_table_template.json
│   └── project_config_template.json
├── assets/fonts/                     (1)
│   └── NanumGothic.ttf
└── evals/                            (1)
    └── evals.json
```

**총 24개 파일** (22+ 요구 충족)

---

### 6. Gotchas 12건 반영 — ✅ PASS

| # | gotchas.md | SKILL.md ⚠️ 섹션 | 일치 |
|---|-----------|-----------------|------|
| 1 | 링크 깨짐 반복 | 링크 200이어도 컨텐츠 키워드 매칭 | ✅ |
| 2 | 이미지↔설명 불일치 | Read 도구로 실제 내용 확인 | ✅ |
| 3 | 영상 자막 중복 | VTT 트랙만, ffmpeg subtitles X | ✅ |
| 4 | 영상 자막↔화면 불일치 | 10초 간격 프레임 샘플링 | ✅ |
| 5 | 약어 본문 노출 | 풀어쓰기 전수 치환 | ✅ |
| 6 | DOCX 빈공간 | LibreOffice PDF 자동 감지 루프 | ✅ |
| 7 | 호칭 잔존 | 전수 grep 0 | ✅ |
| 8 | 수정흔적 문구 | 보고서 노출 0 | ✅ |
| 9 | 다운로드 파일명 | URL path 한글 | ✅ |
| 10 | Vercel 100MB | CRF 30 자동 압축 | ✅ |
| 11 | WSL ffmpeg 손상 | ffprobe moov atom 확인 | ✅ |
| 12 | 메타 섹션 의미 불명 | 삭제 또는 Appendix | ✅ |

---

### 7. 스크립트 실행 가능 — ✅ PASS

| 스크립트 | --help 또는 -n | 실행 권한 |
|---------|---------------|---------|
| compute_scores.py | `python3 --help` OK | -rwxr-xr-x ✅ |
| validate_docx_whitespace.py | `python3 --help` OK | -rwxr-xr-x ✅ |
| validate_images.py | `python3 --help` OK | -rwxr-xr-x ✅ |
| validate_links.py | `python3 --help` OK | -rwxr-xr-x ✅ |
| deploy_vercel.sh | `bash -n` OK | -rwxr-xr-x ✅ |

---

### 8. 금지어 전수 grep — ✅ PASS

| 금지어 | 결과 | 비고 |
|--------|------|------|
| "부암동 325-3" | 4건 | SKILL.md 사용 예시(2), researcher.md 변수 예시(1), evals.json(1=제외). 모두 예시/플레이스홀더 맥락 |
| "v1.5"/"v2"/"v3" | 7건 | 모두 금지어 규칙 정의 또는 gotchas 역사 기술 맥락 |
| "회장" | 2건 | 금지어 규칙 정의 맥락만 |
| "대표" (호칭) | 11건 | 전부 "대표 이미지", "대표 출처" 등 부사적 용법. 호칭 사용 0 |

---

### 9. 에이전트 프롬프트 품질 — ✅ PASS

#### {{placeholder}} 변수화: 8개 전수 ✅
#### 루핑 규칙: 리뷰어 3개 전수 명시 ✅
#### 까칠 톤 키워드: "FAIL", "무한 반복", "0건까지" 전수 존재 ✅

---

### 10. 점수 모델 일관성 — ✅ PASS (iter#1 FAIL → iter#3 PASS)

#### 10-A: 시나리오 가중치 — scoring_model.md vs scorer.md ✅

32셀 전수 대조 일치 (기본 8 + A 8 + B 8 + C 8).

| 차원 | 기본 | A | B | C |
|------|:---:|:---:|:---:|:---:|
| 입지·접근성 | 15=15 ✅ | 13=13 ✅ | 18=18 ✅ | 18=18 ✅ |
| 가격 적정성 | 20=20 ✅ | 18=18 ✅ | 18=18 ✅ | 22=22 ✅ |
| 물리적 상태 | 10=10 ✅ | 14=14 ✅ | 8=8 ✅ | 4=4 ✅ |
| 법적·규제 | 15=15 ✅ | 8=8 ✅ | 22=22 ✅ | 26=26 ✅ |
| 상권·문화 | 10=10 ✅ | 8=8 ✅ | 14=14 ✅ | 12=12 ✅ |
| 목적 적합도 | 15=15 ✅ | 20=20 ✅ | 12=12 ✅ | 8=8 ✅ |
| 희소성·미래가치 | 10=10 ✅ | 14=14 ✅ | 6=6 ✅ | 4=4 ✅ |
| 재무·수익성 | 5=5 ✅ | 5=5 ✅ | 12=12 ✅ | 6=6 ✅ |

#### 10-B: 차원명 — scoring_model.md vs compute_scores.py ✅

| 약어 | scoring_model.md | compute_scores.py | 일치 |
|------|-----------------|-------------------|------|
| LOC | 입지·접근성 | 입지·접근성 | ✅ |
| PRC | 가격 적정성 | 가격 적정성 | ✅ |
| PHY | 물리적 상태 | 물리적 상태 | ✅ |
| REG | 법적·규제 | 법적·규제 | ✅ |
| MKT | 상권·문화 인프라 | 상권·문화 인프라 | ✅ |
| FIT | 목적 적합도 | 목적 적합도 | ✅ |
| SCR | 희소성·미래가치 | 희소성·미래가치 | ✅ |
| FIN | 재무·수익성 | 재무·수익성 | ✅ |

#### 10-C: 등급 체계 — 3개 소스 일치 ✅

| 점수 범위 | scoring_model.md | compute_scores.py | scorer.md | 일치 |
|----------|-----------------|-------------------|-----------|------|
| 90~100 | A+ | A+ | A+ | ✅ |
| 80~89 | A | A | A | ✅ |
| 70~79 | B+ | B+ | B+ | ✅ |
| 60~69 | B | B | B | ✅ |
| 50~59 | C | C | C | ✅ |
| 0~49 | **D** | **D** | **D** | ✅ |

---

## 최종 판정

| # | 항목 | 결과 |
|---|------|------|
| 1 | 프론트매터 유효성 | ✅ PASS |
| 2 | 500줄 이내 | ✅ PASS |
| 3 | Progressive Disclosure | ✅ PASS |
| 4 | 참조 파일 존재 | ✅ PASS |
| 5 | 디렉토리 구조 | ✅ PASS |
| 6 | Gotchas 12건 | ✅ PASS |
| 7 | 스크립트 실행 | ✅ PASS |
| 8 | 금지어 grep | ✅ PASS |
| 9 | 에이전트 프롬프트 | ✅ PASS |
| 10 | 점수 모델 일관성 | ✅ PASS |

## ✅ PASS: 10/10 — FAIL 0건
