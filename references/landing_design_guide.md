# 랜딩 디자인 시스템

> 부동산 리서치 보고서의 웹 랜딩 페이지 디자인 표준.
> 바닐라 HTML/CSS/JS 기반. Vercel 배포.

---

## 1. 색상 팔레트

| 용도 | 이름 | HEX | RGB | CSS 변수 |
|------|------|-----|-----|---------|
| 배경 (메인) | 베이지 | `#f5f1e8` | 245, 241, 232 | `--color-bg` |
| 주색상 | 딥그린 | `#2d4a3e` | 45, 74, 62 | `--color-primary` |
| 강조 | 골드 | `#c8a96a` | 200, 169, 106 | `--color-accent` |
| 위험/경고 | 레드 | `#c44536` | 196, 69, 54 | `--color-danger` |
| 텍스트 | 다크 | `#1a1a1a` | 26, 26, 26 | `--color-text` |
| 카드 배경 | 화이트 | `#ffffff` | 255, 255, 255 | `--color-card` |
| 보조 텍스트 | 그레이 | `#6b7280` | 107, 114, 128 | `--color-muted` |

### CSS 변수 정의

```css
:root {
  --color-bg: #f5f1e8;
  --color-primary: #2d4a3e;
  --color-accent: #c8a96a;
  --color-danger: #c44536;
  --color-text: #1a1a1a;
  --color-card: #ffffff;
  --color-muted: #6b7280;
}
```

### 명도 대비 필수 규칙 (WCAG AA 기준)

| 상황 | 규칙 |
|------|------|
| Hero (이미지 배경) | `filter:brightness(.2)` 이하 + `hero::after` gradient overlay + `hero-inner` 반투명 배경 |
| Hero 텍스트 | `opacity:1` 필수. opacity .8 이하 절대 금지 |
| 어두운 배경(primary) 위 텍스트 | `color:#fff` + `opacity:1`. Soul 카드, 결론박스, 테이블 헤더 포함 |
| 밝은 배경 위 보조 텍스트 | `color:var(--color-muted)` 허용하되 font-size .75rem 이상 |
| 골드 텍스트 | 어두운 배경에서만 사용. 밝은 배경에서 골드는 가독성 불량 |

### Hero 이미지 배경 필수 3중 보호 (brightness만으로 부족 — 반드시 3겹)

```css
/* 1층: 배경 이미지 자체를 매우 어둡게 */
.hero-bg { filter: brightness(.18) saturate(1.1); }

/* 2층: pseudo-element gradient overlay */
.hero::after {
  content: '';
  position: absolute; inset: 0; z-index: 0;
  background: linear-gradient(180deg, rgba(0,0,0,.6) 0%, rgba(0,0,0,.3) 40%, rgba(0,0,0,.5) 100%);
}

/* 3층: hero-inner 자체에 반투명 배경 */
.hero-inner {
  position: relative; z-index: 2;
  background: rgba(0,0,0,.45);
  border-radius: 20px;
  backdrop-filter: blur(2px);
  max-width: 700px;
  padding: 50px 40px;
}
```

**brightness 필터만으로 절대 충분하지 않음.** 건물 사진은 흰색 외벽·하늘·창문 반사 등 밝은 영역이 있어서 filter만으로는 텍스트가 섞임. 반드시 hero-inner에 반투명 배경을 깔아야 함.

**금지 패턴:**
- 이미지 배경 위 `opacity:.7` 이하 텍스트
- 어두운 배경에 text-shadow 없는 텍스트
- 비슷한 명도의 배경+텍스트 조합 (눈으로 구분 안 되면 FAIL)
- **hero-inner에 반투명 배경 없이 brightness + text-shadow만 사용** → FAIL

---

## 2. 폰트

| 용도 | 폰트 | Google Fonts |
|------|------|-------------|
| 타이틀 (h1, h2) | Noto Serif KR | `family=Noto+Serif+KR:wght@400;700` |
| 본문·UI | Noto Sans KR | `family=Noto+Sans+KR:wght@300;400;500;700` |

### 로드 코드

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Noto+Serif+KR:wght@400;700&display=swap" rel="stylesheet">
```

### CSS 적용

```css
h1, h2 {
  font-family: 'Noto Serif KR', serif;
  color: var(--color-primary);
}

body, p, li, td, th, button, input {
  font-family: 'Noto Sans KR', sans-serif;
  color: var(--color-text);
}
```

---

## 3. 영상

### 기본 구조

```html
<video controls preload="metadata" poster="thumbnail.jpg">
  <source src="video.mp4" type="video/mp4">
  <track kind="subtitles" src="video.vtt" srclang="ko" label="한국어" default>
</video>
```

### 핵심 규칙

1. **`controls`**: 브라우저 기본 컨트롤 사용
2. **`preload="metadata"`**: 메타데이터만 미리 로드 (전체 프리로드 X → 트래픽 절감)
3. **VTT 자막만 사용**: ffmpeg subtitles 필터(하드서브) 절대 금지 → VTT track `default`로 소프트서브만
4. **`::cue` 스타일링**: 자막 가독성 향상

### 자막 스타일

```css
video::cue {
  background-color: rgba(0, 0, 0, 0.7);
  color: #ffffff;
  font-family: 'Noto Sans KR', sans-serif;
  font-size: 14px;
  line-height: 1.4;
}
```

### 영상 인코딩 (ffmpeg)

```bash
# 2K 인코딩 (Vercel 배포용 압축)
ffmpeg -i input.mp4 \
  -vf "scale=-2:720" \
  -c:v libx264 -crf 30 -preset slow \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

**주의**: `movflags +faststart` 사용 시 WSL 셧다운으로 moov atom 미완성 가능 → `nohup` + `ffprobe` 완료 검증 필수.

---

## 4. 시나리오 토글

### 구조

3버튼, 2줄 레이블 (메인 + 부제).

```html
<div class="scenario-toggle" role="tablist">
  <button class="scenario-btn active" data-scenario="A" role="tab" aria-selected="true">
    <span class="scenario-main">시나리오 A</span>
    <span class="scenario-sub">갤러리·라이프스타일</span>
  </button>
  <button class="scenario-btn" data-scenario="B" role="tab" aria-selected="false">
    <span class="scenario-main">시나리오 B</span>
    <span class="scenario-sub">카페 운영</span>
  </button>
  <button class="scenario-btn" data-scenario="C" role="tab" aria-selected="false">
    <span class="scenario-main">시나리오 C</span>
    <span class="scenario-sub">재건축</span>
  </button>
</div>
```

### CSS

```css
.scenario-toggle {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin: 24px 0;
}

.scenario-btn {
  padding: 12px 24px;
  border: 2px solid var(--color-primary);
  border-radius: 8px;
  background: var(--color-card);
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
}

.scenario-btn.active {
  background: var(--color-primary);
  color: #fff;
}

.scenario-main {
  display: block;
  font-weight: 700;
  font-size: 15px;
}

.scenario-sub {
  display: block;
  font-size: 12px;
  opacity: 0.8;
  margin-top: 2px;
}
```

### JS — 즉시 업데이트

```javascript
const scenarioButtons = document.querySelectorAll('.scenario-btn');
const scoreElements = document.querySelectorAll('[data-score]');

const WEIGHTS = {
  A: { LOC: 13, PRC: 18, PHY: 14, REG: 8, MKT: 8, FIT: 20, SCR: 14, FIN: 5 },
  B: { LOC: 18, PRC: 18, PHY: 8, REG: 22, MKT: 14, FIT: 12, SCR: 6, FIN: 12 },
  C: { LOC: 18, PRC: 22, PHY: 4, REG: 26, MKT: 12, FIT: 8, SCR: 4, FIN: 6 }
};

function switchScenario(scenario) {
  // 버튼 상태 업데이트
  scenarioButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.scenario === scenario);
    btn.setAttribute('aria-selected', btn.dataset.scenario === scenario);
  });

  // 점수 즉시 재계산
  const weights = WEIGHTS[scenario];
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  let totalScore = 0;

  for (const [dim, weight] of Object.entries(weights)) {
    const normalizedWeight = weight / totalWeight;
    const dimScore = parseFloat(document.querySelector(`[data-dim="${dim}"]`)?.dataset.rawScore || 0);
    totalScore += dimScore * normalizedWeight;
  }

  // DOM 즉시 업데이트
  document.querySelector('.total-score').textContent = Math.round(totalScore);
  document.querySelector('.grade').textContent = getGrade(totalScore);
}

scenarioButtons.forEach(btn => {
  btn.addEventListener('click', () => switchScenario(btn.dataset.scenario));
});
```

---

## 5. 비교 테이블

### 규칙

1. **본 매물 행**: 골드 하이라이트 배경
2. **출처 링크**: 각 비교 매물의 실거래 출처 링크 필수
3. 평당가 기준 정렬 (오름차순)

### CSS

```css
.compare-table {
  width: 100%;
  border-collapse: collapse;
  margin: 24px 0;
}

.compare-table th {
  background: var(--color-primary);
  color: #fff;
  padding: 10px 12px;
  text-align: left;
  font-size: 13px;
}

.compare-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 13px;
}

.compare-table tr.highlight {
  background: rgba(200, 169, 106, 0.15);
  font-weight: 600;
}

.compare-table .source-link {
  color: var(--color-accent);
  text-decoration: underline;
  font-size: 11px;
}
```

---

## 6. 모바일 브레이크포인트

| BP | 너비 | 대상 기기 |
|----|------|---------|
| xs | 360px | 소형 모바일 (Galaxy S) |
| sm | 414px | 중형 모바일 (iPhone) |
| md | 768px | 태블릿 |
| lg | 1024px | 소형 데스크톱 / 태블릿 가로 |
| xl | 1440px | 데스크톱 |

### 미디어 쿼리

```css
/* Mobile first */
.container { padding: 16px; max-width: 100%; }

@media (min-width: 768px) {
  .container { padding: 24px; max-width: 720px; margin: 0 auto; }
  .scenario-toggle { flex-direction: row; }
}

@media (min-width: 1024px) {
  .container { max-width: 960px; }
}

@media (min-width: 1440px) {
  .container { max-width: 1200px; }
}

/* 시나리오 토글: 모바일에서 세로 정렬 */
@media (max-width: 767px) {
  .scenario-toggle { flex-direction: column; }
  .scenario-btn { width: 100%; }
}
```

---

## 7. 배포 — Vercel

### 제한사항

- **100MB 파일 크기 제한**: 영상은 반드시 CRF 30 + scale 720으로 압축 후 배포
- 로컬 서버 사용 금지 — **무조건 Vercel 프로덕션 배포**

### 배포 명령

```bash
# Vercel CLI 배포
vercel --prod
```

### 디렉토리 구조

```
output/landing/
├── index.html
├── styles.css
├── script.js
├── assets/
│   ├── images/
│   ├── charts/
│   └── fonts/
├── videos/
│   ├── tour.mp4        # ≤ 100MB (압축 필수)
│   └── tour.vtt
└── vercel.json         # 라우팅 설정
```

---

## 8. 랜딩 레이아웃

```
[Hero — 매물 대표 이미지 + 주소 + 한 줄 추천]
    ↓
[종합 점수 카드]  큰 게이지 + 등급 뱃지 + 백분위
    ↓
[시나리오 토글 바]  A · B · C 버튼
    ↓
[3그룹 카드 (G1·G2·G3)]  레이더 차트 옆 배치
    ↓
[Soul 풀블리드 섹션]  금박 카드 + 차별 자산 갤러리
    ↓
[G4 메타]  신뢰도 + 민감도 + Devil's Advocate 펼침
    ↓
[G5 — CMA 비교 막대 차트 + 비교 테이블]
    ↓
[임장 영상 섹션]  video + VTT 자막
    ↓
[상세 분석 12섹션]
    ↓
[다운로드]  PDF 메인 + DOCX 원본 버튼 2개
    ↓
[Footer]  출처·면책·생성일시
```
