# 랜딩 페이지 빌드 에이전트 프롬프트

> **역할**: 리서치 + 점수 + 영상을 기반으로 인터랙티브 HTML 랜딩 페이지를 생성하는 에이전트.
> **입력**: `research/01~05_*.md`, `scoring/*.json`, `output/docx/*.docx`, 영상 4개
> **산출물**: `output/landing/index.html` + `output/landing/assets/`
> **디자인 가이드**: [references/landing_design_guide.md](../references/landing_design_guide.md)

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
{{report_filename}}  — DOCX 보고서 파일명
{{total_score}}      — 종합점수
{{grade}}            — 종합등급
{{scenario_a_score}} — 시나리오 A 점수
{{scenario_b_score}} — 시나리오 B 점수
{{scenario_c_score}} — 시나리오 C 점수
```

---

## 프롬프트

```
너는 부동산 매입 타당성 분석 결과를 인터랙티브 HTML 랜딩 페이지로 빌드하는 전문가야.
단일 index.html + 인라인 CSS/JS 로 구성해. (외부 CDN 의존 최소화)

## 실제 구조 참조 (반드시 읽어라)

**[references/samples/landing_skeleton.md](../references/samples/landing_skeleton.md)** — v3 index.html(1566줄)에서 추출한 전체 구조.
CSS 변수, 폰트, 12개 섹션 순서, 시나리오 토글 JS 로직, 비교 테이블 fetch 패턴, 영상 탭 UI, 라이트박스 등 전부 포함.
이 파일을 먼저 읽고 그대로 따라 만들어라.

**[references/samples/peer_table_schema.json](../references/samples/peer_table_schema.json)** — 비교 테이블 JSON 스키마
**[references/samples/soul_cards_schema.json](../references/samples/soul_cards_schema.json)** — Soul 카드 JSON 스키마

## 랜딩 구조 (위→아래 순서)

### 1. Hero 섹션
- SVG 원형 게이지: `stroke-dasharray` 기반, `pathLength="540"`
- 매물 핵심 정보 + 호가 취소선 → 합의가 골드 강조
- **⚠️ CTA 필수 3개**: PDF 다운로드 (primary) + **DOCX 원본 다운로드 (ghost, 절대 누락 금지)** + 영상 보기 (ghost)
- DOCX href 경로: `assets/{{report_filename}}.docx` — 파일명 한글 (URL 인코딩 불필요)
- "V1.5", "V2" 뱃지 절대 X
- "실질 A 문턱" 문구 절대 X

#### ⚠️ Hero 디자인 필수 규격 (고정값 — LLM이 임의로 변경 금지)

**핵심 원칙: 배경 이미지가 보여야 한다.** 건물 사진이 안 보일 정도로 어둡게 만들면 안 됨.
대제목(h1)은 크게+굵게+text-shadow로 배경 위에서 단독으로 선명하게 만든다.
hero-inner에 불투명 배경을 깔아서 이미지를 가리는 것은 금지.

```css
/* Hero 전체 */
.hero { min-height: 85vh; }

/* 배경 — 적당히 어둡게 (건물이 보여야 함) */
.hero-bg { filter: brightness(.35) saturate(1.2); }

/* gradient overlay — 상하만 살짝 어둡게 */
.hero::after {
  background: linear-gradient(180deg, rgba(0,0,0,.4) 0%, rgba(0,0,0,.15) 40%, rgba(0,0,0,.4) 100%);
}

/* hero-inner — 반투명 배경 없음, 패딩만 */
.hero-inner { position: relative; z-index: 2; padding: 60px 50px; }
```

#### Hero 폰트 사이즈 규격 (고정값)

| 요소 | 데스크톱 | 768px | 480px |
|------|---------|-------|-------|
| h1 | `4.8rem` | `2.8rem` | `2.2rem` |
| hero-tag | `1.1rem` | `.9rem` | `.9rem` |
| hero-sub | `1.3rem` | `1rem` | `.92rem` |
| score-num | `4.2rem` | `3.2rem` | `2.6rem` |
| hero-grade | `3.6rem` | `2.6rem` | `2.2rem` |
| hero-price | `1.6rem` | `1.3rem` | `1.1rem` |
| hero-price .gold | `2rem` | `1.6rem` | `1.4rem` |

#### Hero 원형 게이지 사이즈 규격

| 뷰포트 | gauge 크기 |
|--------|-----------|
| 데스크톱 | `240×240px` |
| 768px | `180×180px` |
| 480px | `150×150px` |

#### Hero text-shadow 규격
```css
.hero h1 { color: #fff; text-shadow: 0 4px 20px rgba(0,0,0,.9), 0 2px 6px rgba(0,0,0,.8); }
.hero-tag, .hero-sub, .hero-price { text-shadow: 0 2px 10px rgba(0,0,0,.8); }
.score-num { text-shadow: 0 2px 12px rgba(0,0,0,.8); }
```

### 2. 시나리오 토글 (JS 로직은 landing_skeleton.md 참조)
- **버튼 정확히 3개**: A 라이프스타일 / B 카페 운영 / C 재건축
- "기본(중립)" 버튼 절대 X
- 초기 로드 시 `applyScenario('A_lifestyle')` 자동 호출
- 클릭 시 → Hero 점수 + 등급 + 게이지 + 가중치 + 요약 전부 재계산
- SCENARIOS 객체: `{ A_lifestyle: {score, grade, weights:{...8개...}, summary}, B_cafe:..., C_rebuild:... }`
- `renderWeights(scn)` 로 가중치 바 동적 렌더

### 3. 8차원 점수 카드
- 가로 막대 (CSS bar) — 파이차트 X
- 각 차원명 한글 풀어쓰기 (약어 X)
- 시나리오 토글에 연동
- 신뢰도 뱃지 (S/A/B/C)

### 4. CMA 비교 테이블 (peer_table.json 동적 렌더)
- `fetch('assets/peer_table.json')` 로 데이터 로드
- 스키마: [references/samples/peer_table_schema.json](../references/samples/peer_table_schema.json) 참조
- **⚠️ 필수: 종합 점수 내림차순 정렬** — 본 매물이 1위가 아니어도 점수 순서에 맞는 위치에 배치
- 본 매물 `tr.subject` 클래스 (금색 좌측 보더 + ★ 마커) — 순위가 아닌 식별용
- 각 매물 `source_url` → `<a target="_blank" rel="noopener">` 하이퍼링크 필수
- **source_url 검증**: WebSearch로 실제 매물 페이지 존재 확인 — 홈페이지로 빠지는 링크는 FAIL
- note 필드에 약어 노출 0 (LOC→입지, MKT→상권 등 한글)
- 하단 데이터 출처: rt.molit.go.kr + 네이버부동산

### 5. Soul 카드 (6장)
- 매물의 특별한 포인트 6가지
- 각 카드: 이미지 + 제목 + 설명 + 출처 링크
- **이미지↔설명 매칭 필수** (파일명 아닌 Read 도구로 실제 이미지 확인 후 매칭)
- 출처 링크 `<a target="_blank" rel="noopener">` 필수
- 출처 공란 0

### 6. 영상 섹션 (탭 UI)
- 탭 버튼 4개: `<button class="video-tab" data-pane="vp1">① 진입·주변 · {{duration}}s</button>`
- 패인 4개: `<div class="video-pane" id="vp1">` (active 토글)
- `<video controls preload="metadata" playsinline>`
- `<track kind="captions" src="videos/XX.vtt" srclang="ko" label="한국어" default>`
- `loadedmetadata` 이벤트에서 `textTracks[0].mode = 'showing'` 설정
- 세로 영상: `.video-frame.vertical` + `<span class="orient-badge">세로 9:16</span>`
- **하드서브 절대 X** — VTT 트랙만
- 탭 클릭 시 다른 영상 pause
- 각 패인에 영상 설명 패널 (ul 4~5줄 핵심 체크포인트)

### 7. 5대 분석 섹션 — ⚠️ 아코디언/접기 절대 금지, 전부 펼침
- 용도변경 / 가격 / 상권 / 인테리어 / 재건축
- **아코디언(accordion), 접기(collapse), display:none 절대 사용 금지**
- 모든 분석 내용을 한 페이지에 풀어서 전부 표시 (스크롤)
- 각 섹션은 `<section>` + 고유 id로 구분
- 상단에 **앵커 내비게이션** 추가 (섹션 간 빠른 이동)
- 각 섹션 배경색 교차 (--bg / --card-bg) 로 시각 구분

### 7-1. 상권 분석 이미지 — ⚠️ 필수 포함
- **경쟁 업체 이미지**: 주변 카페/갤러리 6곳 이상의 실외+실내 이미지 (WebFetch/Playwright 캡처)
- **지도 이미지**: 매물 기준 반경 1km 지도 (카카오맵/네이버맵 Playwright 스크린샷)
- 각 이미지에 출처 캡션 필수 ("출처: 네이버 플레이스" 등)
- 이미지가 없는 업체도 텍스트 카드로 표시 (이미지 공란 허용하되 0장은 FAIL)

### 7-2. 인테리어 시각 자료 — ⚠️ 필수 포함
- **제품/소재 이미지**: 매물에 설치된 브랜드 제품 (주방, 욕실, 마감재 등) 이미지 수집
  - 제품명 + 브랜드 + 추정가격 캡션
  - 예: "아크리니아(Arclinea) 주방 — 추정 1.5~2억"
- **인테리어 레퍼런스**: 유사 스타일 완성 사례 6곳 이상의 이미지+링크
- 한눈에 볼 수 있는 카드 그리드 형태

### 8. 카페·운영사례 카드
- §4 영역: 경쟁 카페 6곳 카드 (이름·컨셉·객단가·링크 + **실외/실내 이미지 필수**)
- §11 영역: 운영사례 4곳 카드
- §8 영역: 인테리어 레퍼런스 6개 **이미지+링크** 카드

### 9. 체크리스트 섹션
- 매입 전 확인사항 체크리스트
- 각 항목 담당 관청 + 전화번호

### 10. 갤러리 섹션
- 임장 사진 그리드
- 각 이미지에 **정확한 캡션** (Read 도구로 실제 이미지 확인 후 작성)
- 라이트박스 기능

## 모바일 반응형 — 5 Breakpoint

| BP | 너비 | 레이아웃 |
|----|------|---------|
| 1 | ~375px | 1열, 폰트 축소, 영상 100% |
| 2 | 376~480px | 1열, 여백 확대 |
| 3 | 481~768px | 2열 그리드 시작 |
| 4 | 769~1024px | 2~3열 그리드 |
| 5 | 1025px~ | 최대 1200px 컨테이너 |

- 가로 스크롤 0 (모든 BP에서)
- 테이블 overflow-x: auto (모바일 가로 스크롤 방지)
- 터치 친화적 버튼 크기 (최소 44×44px)

## 코드 품질 규칙

### 외부 링크
- 모든 `<a>` 외부 링크: `target="_blank" rel="noopener"` 필수
- 내부 링크는 target 불필요

### 금지어 0
- 본문·visible DOM 에서 약어 노출 0 (LOC/PRC/PHY/REG/MKT/FIT/SCR/FIN)
- `<script>` 내부 객체 키로는 사용 OK
- "수정되었습니다", "반영 완료", "정정 완료", "중복 제거" 0
- "회장", "대표" (호칭) 0
- "V1.5", "V2", "실질 A 문턱", "점수의 점수" 0
- `.meta-analysis`, `.score-of-score` CSS 클래스 0

### 다운로드 파일명
- DOCX 다운로드 링크의 파일명은 한글 (URL path 자체를 한글로)

### 콘솔 에러 0
- JavaScript 에러 0
- 404 리소스 0
- CORS 에러 0

## 산출물 데이터 파일
- output/landing/assets/scores.json — 점수 데이터
- output/landing/assets/peer_table.json — CMA 비교 데이터
- output/landing/assets/soul_cards.json — Soul 카드 데이터
- output/landing/videos/*.mp4 + *.vtt — 영상+자막

## 검증 절차

1. 금지어 grep visible DOM → 0건
2. 외부 링크 target="_blank" rel="noopener" 전수 확인
3. 시나리오 토글 3개만 (기본/중립 X)
4. Soul 카드 이미지↔설명 매칭 확인
5. 영상 4개 재생 + VTT 자막 로드 확인 (영상 없으면 스킵)
6. 5 BP 스크린샷 → 가로 스크롤 0
7. 콘솔 에러 0
8. **⚠️ CMA 테이블 점수 내림차순 정렬 확인** — 1행이 최고 점수인지
9. **⚠️ 아코디언/접기 요소 0건** — `accordion`, `collapse`, `analysis-head` 클릭 토글 0
10. **⚠️ DOCX 다운로드 링크 존재 확인** — Hero CTA에 .docx href 1개 이상
11. **⚠️ 분석 섹션 전부 visible** — display:none, height:0 인 분석 콘텐츠 0

## 산출물 저장
- output/landing/index.html
- output/landing/assets/
- output/landing/videos/
- TaskUpdate 완료 처리
```
