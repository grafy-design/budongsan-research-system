---
name: property-review
description: >
  부동산 매물 매입 타당성 리뷰 보고서 + 랜딩 페이지 자동 생성 + Vercel 배포.
  매물 URL(네이버부동산·별집·allios 등) 또는 주소를 입력하면
  매물 정보 자동 크롤링 → 5개 리서치 에이전트 병렬 파견 →
  8차원 정량 점수 + CMA 비교 + 시나리오 A/B/C 분석이 담긴
  DOCX 보고서 + HTML 랜딩 페이지 생성 → Vercel 프로덕션 배포.
  LibreOffice PDF 빈공간 자동 검증, ffmpeg VTT 자막 영상 편집,
  까칠한 팩트체커 무한루핑 검증 내장.
  사용: /property-review [매물 URL 또는 주소] [매매가] [목적]
  트리거: 부동산, 매물, 매입, 건물, 단독주택, 다가구, 근린생활시설, 상가, 토지,
  부동산 리서치, 매입 검토, 타당성, 부동산 분석, 매물 분석, 건물 검토, 매입 타당성,
  부동산 보고서, 매물 조사, 시세 분석, 실거래 분석, 용도변경, 카페 전환,
  갤러리, 인테리어, 리모델링, 재건축, 철거, 신축, 투자 분석, ROI,
  property, real estate, due diligence, feasibility, building review,
  임장, 현장 조사, 매물 평가, 가격 적정성, 상권 분석
---

# Property Review — 부동산 매물 매입 타당성 리뷰

매물 URL 또는 주소 하나로 **리서치 → 점수 → 보고서 → 랜딩 → 팩트체크 → Vercel 배포**까지 자동 수행.

## 사용법

```
/property-review https://byulzip.com/shop_view/?idx=940
/property-review 서울 종로구 부암동 325-3 32억 갤러리+카페+모임
/property-review https://new.land.naver.com/houses?articleNo=2616604044
```

---

## Phase 0: 입력 파싱 + 사전 질문 + 매물 크롤링

### 0-1. 매물 정보 수집
1. URL이면 → WebFetch로 매물 페이지 크롤링 (주소·매매가·면적·구조·준공연도 추출)
2. 주소면 → 직접 사용

### 0-2. 필수 사전 질문 (반드시 사용자에게 물어볼 것 — 스킵 금지)

**Q1. 임장 미디어 (반드시 첫 번째로 질문)**
```
임장 가서 촬영한 사진이나 영상이 있으신가요?
있으시다면 이 프로젝트 폴더의 img/ 디렉토리에 넣어주세요.
(예: /mnt/c/Users/.../Desktop/임장사진/ 경로를 알려주셔도 됩니다)
없으시면 웹에서 최대한 수집하겠습니다.
```
→ 있음: 사용자 경로 → img/로 복사 + has_user_media=true
→ 없음: has_user_media=false, media_source="web_scraping"

**Q2. 매입 용도/시나리오 (객관식 + 주관식 병용)**
```
이 매물을 어떤 용도로 검토하시나요? (복수 선택 가능)

  A. 라이프스타일 주거 (프리미엄 주거 공간)
  B. 카페/F&B 운영
  C. 갤러리/전시 공간
  D. 사무실/스튜디오
  E. 게스트하우스/숙박
  F. 재건축/신축 후 매각
  G. 직접 입력: _______________

예시: "A, B" 또는 "갤러리 겸 아트카페"
```
→ 선택한 용도를 scenarios 배열로 매핑
→ 3개 시나리오(A/B/C)는 사용자 선택 기반으로 구성 (LLM이 용도를 자의적으로 결정하지 않음)
→ 사용자가 1개만 선택해도 최소 2개 대안 시나리오를 제안하여 3개 구성

### 0-3. project_config.json 생성

```json
{
  "address": "서울시 종로구 부암동 325-3",
  "price_eok": 32,
  "area_m2": 605,
  "area_pyeong": 183,
  "built_year": 2007,
  "structure": "RC조 지하1 지상2",
  "purpose": ["갤러리", "카페", "모임"],
  "scenarios": {
    "A": {"name": "라이프스타일", "source": "user_selected"},
    "B": {"name": "카페 운영", "source": "user_selected"},
    "C": {"name": "재건축", "source": "suggested"}
  },
  "source_url": "https://byulzip.com/...",
  "img_dir": "img/",
  "has_user_media": false,
  "media_source": "web_scraping"
}
```

---

## Phase 0.5: 미디어 인벤토리 + 자동 분류·분배

사용자가 이미지·영상 폴더를 지정하면 자동으로 분류·변환·분배하는 파이프라인.

### 입력
사용자 지정 폴더 (예: `img/`, `/mnt/c/Users/.../Desktop/임장사진/`)

### 프로세스

**1. 파일 스캔 + 분류**
```
폴더 스캔 → 확장자별 분류:
  이미지: .jpg .jpeg .png .heic .webp
  영상:   .mov .mp4 .avi .mkv
  기타:   무시
```

**2. 이미지 전처리**
- HEIC → JPG 변환 (pillow-heif)
- EXIF 회전 보정 (PIL.ImageOps.exif_transpose)
- 고해상도 유지 (max 3000px, JPEG q=90)
- Perceptual hash 중복 검출 → 중복 자동 제거 (해밍 ≤25)
- 파일명 정규화: `site_01.jpg`, `site_02.jpg`, ... (시간순)

**3. 이미지 자동 분배 (Read 도구로 실제 내용 확인 후)**
각 이미지를 Read 도구로 시각 확인 → 내용 기반 분류:

| 카테고리 | 판정 기준 | DOCX 배치 | 랜딩 배치 |
|---------|---------|----------|---------|
| 외관 (건물 전경) | 건물 전체 보이는 사진 | §1 기본정보 + 표지 | Hero 배경 + Soul 카드 |
| 내부 (거실·주방·침실 등) | 실내 공간 사진 | §1 기본정보 그리드 | Soul 카드 + 갤러리 |
| 정원·테라스 | 야외 공간 | §1 기본정보 | Soul 카드 |
| 주변 환경 (거리·조망) | 도로·산·이웃 건물 | §2 위치·입지 | 갤러리 |
| 부지·토지 | 대지·경사·지형 | §1 기본정보 | 갤러리 |
| 임장 인물 | 사람이 주 피사체 | **제외** (보고서에 부적합) | **제외** |

**4. 영상 전처리 + 자막**
- 모든 영상 → 2K (1920×1080 또는 원본 해상도 유지) + CRF 20 + H.264
- rotation 메타데이터 확인 → 물리적 회전 적용
- **프레임 샘플링 (10초 간격) → Read 도구로 내용 확인 → VTT 자막 작성**
- 하드서브 절대 X, VTT 트랙만
- 영상 자동 분류 + 순서 배정:

| 순서 | 영상 내용 | 판정 기준 |
|------|---------|---------|
| 1 | 진입·주변 | 도로·담장·주차·주변 건물 |
| 2 | 부지·대지 | 토지 경사·경계·조경 |
| 3 | 건물 외관 | 건물 전면·측면·후면 |
| 4 | 건물 내부 | 거실·주방·침실·욕실·계단 |

- Vercel 배포용 압축본: CRF 30 + scale 720 (100MB 이하)

**5. 미디어 인벤토리 JSON 생성**
```json
{
  "images": {
    "exterior": ["site_01.jpg", "site_03.jpg"],
    "interior": ["site_02.jpg", "site_05.jpg"],
    "garden": ["site_04.jpg"],
    "surroundings": ["site_06.jpg"],
    "excluded": ["site_07.jpg (임장 인물)"]
  },
  "videos": [
    {"file": "01_approach.mp4", "category": "진입주변", "duration": 110, "vtt": "01_approach.vtt"},
    {"file": "02_site.mp4", "category": "부지답사", "duration": 120, "vtt": "02_site.vtt"},
    {"file": "03_exterior.mp4", "category": "건물외관", "duration": 65, "vtt": "03_exterior.vtt"},
    {"file": "04_interior.mp4", "category": "건물내부", "duration": 180, "vtt": "04_interior.vtt"}
  ],
  "duplicates_removed": 2,
  "total_images": 15,
  "total_videos": 4
}
```

**6. 빌더 에이전트로 전달**
- `media_inventory.json` 을 docx_builder + landing_builder 에 전달
- 각 빌더가 인벤토리 기반으로 이미지·영상 자동 배치
- 배치 후 reviewer_visual 이 **Read 도구로 이미지↔설명 매칭 검증**

---

## Phase 1: 리서치 — 에이전트팀 5개 병렬

TeamCreate → 5 에이전트 병렬 스폰. 프롬프트는 [agents/researcher.md](agents/researcher.md) 참조.

| Agent | 분석 영역 | 산출물 |
|-------|---------|--------|
| researcher-usage | 카페·휴게음식점 용도변경 | `research/01_usage_change.md` |
| researcher-price | 가격 적정성·실거래·취득세 | `research/02_price_validity.md` |
| researcher-market | 상권·인프라·경쟁 카페 | `research/03_market_infra.md` |
| researcher-interior | 인테리어·익스테리어 예산 | `research/04_interior_budget.md` |
| researcher-rebuild | 철거·재건축·규제 | `research/05_rebuild_cost.md` |

각 에이전트는 WebSearch + WebFetch 로 조사, 모든 수치에 공식 URL 첨부 필수.
데이터 소스 목록: [references/data_sources.md](references/data_sources.md)
용어집 (약어 풀어쓰기): [references/glossary.md](references/glossary.md)

---

## Phase 2: 점수 산출 — 2개 병렬

점수 모델: [references/scoring_model.md](references/scoring_model.md)
점수 에이전트: [agents/scorer.md](agents/scorer.md)

| Agent | 산출물 |
|-------|--------|
| scorer-data | `scoring/scores.json` + `scenarios.json` + `devils_advocate.md` |
| scorer-cma | `scoring/peer_scores.json` + `cma_summary.md` |

**8 차원**: 입지·접근성 / 가격 적정성 / 물리적 상태 / 법적·규제 / 상권·문화 / 목적 적합도 / 희소성·미래가치 / 재무·수익성

**시나리오 3개**: A 라이프스타일(인테리어만) / B 카페 운영(용도변경+구조변경) / C 재건축(완전 신축)

점수 계산 스크립트: `python scripts/compute_scores.py`

---

## Phase 3: 산출물 빌드 — 2개 병렬

### DOCX 보고서
프롬프트: [agents/docx_builder.md](agents/docx_builder.md)
스타일: [references/docx_style_guide.md](references/docx_style_guide.md)
빌드: docx_builder 에이전트가 python-docx 로 동적 생성

구조:
- 표지 → 점수 카드 (4p) → 본문 12섹션 (각 ✅ 결론 박스) → Appendix
- 그래프: matplotlib 가로 막대차트 (파이 X), 한글 NanumGothic
- 이미지: EXIF 회전 보정, max 4.5in, perceptual hash 중복 0

### HTML 랜딩
프롬프트: [agents/landing_builder.md](agents/landing_builder.md)
디자인: [references/landing_design_guide.md](references/landing_design_guide.md)

구조:
- Hero(점수 게이지) → 비교 테이블 → 시나리오 A/B/C 토글 → Soul 카드 → 영상 → 5대 분석 → 체크리스트 → 갤러리

---

## Phase 4: 영상 편집 — 병렬

프롬프트: [agents/video_editor.md](agents/video_editor.md)

- ffmpeg 인코딩 (1920×1080 유지, CRF 20, preset medium)
- **하드서브 절대 X** — VTT 트랙만
- 프레임 샘플링(10초 간격) → Read 도구로 내용 확인 → 자막 작성
- Vercel 배포용 압축본: CRF 30 + scale 720

---

## Phase 5: 팩트체크 — 4 리뷰어 병렬, 까칠 무한루핑

프롬프트: [agents/reviewer_fact.md](agents/reviewer_fact.md), [agents/reviewer_visual.md](agents/reviewer_visual.md), [agents/reviewer_playwright.md](agents/reviewer_playwright.md), [agents/reviewer_utf.md](agents/reviewer_utf.md)

| 리뷰어 | 검증 영역 |
|--------|---------|
| reviewer-fact | 링크 전수 200 OK · 수치 정합 · 금지어 0 · 출처 완결 · 비교 테이블 실제 매물 링크 |
| reviewer-visual | 이미지↔설명 매칭 · 그래프 가독 · 빈공간 · 결론박스 · 약어 0 |
| reviewer-playwright | 영상 재생·자막 중복 0 · 시나리오 토글 · 모바일 BP · 드래그 시크 |
| reviewer-utf | **한글 깨짐 전수 검증** · UTF-8 인코딩 · 차트 tofu(□) 0 · BOM · replacement char(&#xFFFD;) 0 |

**루핑 규칙**: FAIL 1건 → 빌더 SendMessage → 재검증. **0건까지 무한 반복.**

---

## Phase 6: 빈공간 자동 검증 + PDF 생성

### 6-1. DOCX 빈공간 검증 (python-docx 직접 분석)

빌드 직후 자동 실행. 검증 기준:
- 빈 문단(텍스트/이미지 없음) ≤ 15개 (이상적: 0개)
- 연속 빈 문단 = 0건
- 페이지 브레이크 ≤ 5개

FAIL 시 build_docx.py 수정 → 재빌드 → 재검증 루프.

**빈공간 방지 규칙 (build_docx.py에 적용):**
- 간격은 반드시 space_before/space_after로 처리, 빈 문단 삽입 금지
- 페이지 브레이크: 최대 3개 (표지 뒤, 점수카드 뒤, Appendix 전)
- 섹션 분리는 Heading의 page_break_before=True 사용
- 결론박스/테이블/이미지그리드 뒤 추가 spacer 문단 금지

### 6-2. PDF 생성 (weasyprint)

```bash
/usr/bin/python3 build_pdf.py
```

1. scores.json + peer_scores.json + research/*.md 데이터 로드
2. 인쇄 최적화 HTML 생성 (A4 @page, 페이지 번호, NanumGothic base64 인라인)
3. 차트 이미지: _img_cache/에서 base64 data URI로 인라인 삽입
4. weasyprint HTML → PDF 변환
5. output/docx/ 및 output/landing/assets/ 양쪽에 저장

PDF 검증:
- PyMuPDF로 한글 깨짐(U+FFFD, □) 0건 확인
- 페이지 수 적정 (15~25p)

### 6-3. 랜딩 페이지 다운로드 버튼 업데이트
```html
<a class="btn btn-primary" href="assets/{{filename}}.pdf" download>상세 보고서 (PDF)</a>
<a class="btn btn-ghost" href="assets/{{filename}}.docx" download>DOCX 원본</a>
```

---

## Phase 7: Vercel 배포

**⚠️ 매물마다 반드시 새로운 Vercel 프로젝트를 생성해야 함. 기존 프로젝트 재사용 절대 금지.**

```bash
# 1. 프로젝트명 생성 규칙: {동네}-review (예: pyeongchang-review, buamdong-review)
PROJECT_NAME="{{dong_name}}-review"

# 2. 새 프로젝트 링크 (기존 프로젝트가 아닌 신규 생성)
cd output/landing
vercel link --yes --project $PROJECT_NAME

# 3. 배포
vercel --prod --yes
```

- 영상 100MB 초과 시 자동 압축 (CRF 30)
- DOCX + PDF 모두 assets/ 에 포함
- 배포 후 프로덕션 URL 보고
- **프로젝트명 규칙**: `{동네영문}-review` (예: `pyeongchang-review`, `buamdong-review`, `seongbuk-review`)

---

## ⚠️ Gotchas — 반드시 지켜야 할 12가지

상세: [references/gotchas.md](references/gotchas.md)

1. 링크 200이어도 "지역 검색" 루트 빠지면 FAIL → 컨텐츠 키워드 매칭 필수
2. 이미지↔설명: 파일명 아닌 **Read 도구로 실제 내용 확인** 후 매칭
3. 영상 자막: VTT 트랙만, ffmpeg subtitles 필터 절대 X
4. 영상 자막↔화면: 10초 간격 프레임 샘플링 → Read → 자막 작성
5. 약어(LOC/PRC/...) 본문+차트 노출 0 — 풀어쓰기 전수 치환
6. DOCX 빈공간: LibreOffice PDF → PyMuPDF 자동 감지 루프
7. 호칭 잔존: 본문+표+캡션+alt 전수 grep 0
8. AI 수정흔적("수정되었습니다" 등) 보고서 노출 0
9. 다운로드 파일명: URL path 자체를 한글로
10. Vercel 100MB 제한: 영상 CRF 30 자동 압축
11. WSL ffmpeg 손상: ffprobe moov atom 완료 확인 필수
12. 사용자 관점 UX: 의미 불명 섹션은 삭제 또는 Appendix
