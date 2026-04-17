# 랜딩 페이지 HTML 구조 — v3 부암동에서 추출

이 문서는 실제 v3 index.html(1566줄)의 구조를 정리한 것입니다.
새 매물 랜딩 페이지 생성 시 이 구조를 그대로 따릅니다.

## CSS 변수 (`:root`)

```css
:root{
  --bg:#f5f1e8;        /* 크림 베이지 배경 */
  --bg-2:#ebe4d4;
  --bg-3:#e3dbc6;
  --ink:#1a1a1a;
  --ink-2:#3c3c3c;
  --mute:#6a6a6a;
  --rule:#d6cdb8;
  --green:#2d4a3e;     /* 딥그린 (주 강조) */
  --green-2:#3e6655;
  --gold:#c8a96a;      /* 골드 (점수·뱃지) */
  --gold-2:#e8c77a;
  --gold-deep:#a6841a;
  --red:#c44536;       /* 경고 */
  --shadow:0 10px 30px rgba(20,20,20,.08);
  --shadow-xl:0 20px 60px rgba(20,20,20,.15);
}
```

## 폰트

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700;900&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```
- 제목: `'Noto Serif KR', serif`
- 본문: `'Noto Sans KR', system-ui, sans-serif`

## 섹션 순서 (위→아래)

### 1. Hero (`#hero`)
- 배경: 매물 대표 사진 (brightness .48 + saturate 1.05)
- SVG 원형 게이지 (stroke-dasharray 기반)
- 점수 + 등급 뱃지 + 핵심 스탯
- 가격 (호가 취소선 → 합의가 골드)
- CTA: PDF 다운로드 + DOCX 원본 + 영상 보기

```html
<section class="hero" id="hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <div class="hero-inner">
    <span class="hero-tag">{{date}} · 매입 타당성 검토</span>
    <h1>{{address_short}}</h1>
    <p class="hero-sub">8개 평가 차원 · 3개 시나리오 · 4편 임장영상 · 20개 비교군</p>
    <div class="hero-score">
      <div class="hero-gauge">
        <svg viewBox="0 0 200 200"><circle class="track" cx="100" cy="100" r="86"/><circle class="bar" id="heroBar" cx="100" cy="100" r="86" stroke-dasharray="0 540" pathLength="540"/></svg>
        <div class="center"><div class="score-num" id="heroScore">80</div><div class="score-label">A 라이프스타일 / 100</div></div>
      </div>
      <div class="hero-grade" id="heroGrade">B+</div>
    </div>
    <div class="hero-price">
      <span class="strike">호가 {{asking_price}}억</span>
      <span class="gold">합의가 {{agreed_price}}억원</span>
    </div>
    <div class="hero-cta">
      <a class="btn btn-primary" href="assets/{{pdf_filename}}" download>📄 상세 보고서 다운로드 (PDF)</a>
      <a class="btn btn-ghost" href="assets/{{docx_filename}}" download>📝 DOCX 원본</a>
      <a class="btn btn-ghost" href="#videos">🎬 임장 영상 보기</a>
    </div>
  </div>
</section>
```

### 2. 시나리오 토글 (`#scenario`)
- 버튼 정확히 3개: A / B / C (기본/중립 X)
- 초기 active = A 라이프스타일
- 클릭 시: Hero 점수 + 가중치 + 요약 전부 재계산

```javascript
const SCENARIOS = {
  A_lifestyle: { score: 79.9, grade: 'B+', weights: {...}, summary: '...' },
  B_cafe:      { score: 73.3, grade: 'B+', weights: {...}, summary: '...' },
  C_rebuild:   { score: 72.4, grade: 'B+', weights: {...}, summary: '...' }
};
function applyScenario(scn) {
  const s = SCENARIOS[scn];
  scnScoreEl.textContent = s.score.toFixed(1);
  heroScoreEl.textContent = Math.round(s.score);
  setHeroGauge(s.score);
  renderWeights(scn);
  scnBtns.forEach(b => b.classList.toggle('active', b.dataset.scn === scn));
}
applyScenario('A_lifestyle'); // 초기 로드
```

### 3. 비교 테이블 (`#peer-comparison`)
- `fetch('assets/peer_table.json')` 로 동적 렌더
- 본 매물 `tr.subject` 클래스 (금색 배경 + ★ 마커)
- 각 매물 `source_url` 하이퍼링크 필수
- 데이터 출처 (rt.molit.go.kr + 네이버부동산)

### 4. 그룹 카드 (`#groups`)
- G1 머니&시장 / G2 위치&환경 / G3 이 집만의 매력
- 카드 클릭 → `.open` 토글 → 차원 상세 펼침
- CSS bar로 각 차원 점수 시각화

### 5. Soul 풀블리드 (`#soul`)
- 6장 카드: `.soul-card` (이미지 + 제목 + 설명 + 출처)
- 하단: Soul 스코어바 (목적 적합도 + 희소성 가중평균)
- **이미지↔설명 매칭은 Read 도구로 실제 이미지 확인 후**

### 6. 영상 4편 (`#videos`)
- 탭 UI: 버튼 4개 → 패인 4개 토글
- `<video controls preload="metadata" playsinline>`
- `<track kind="captions" src="videos/XX.vtt" srclang="ko" label="한국어" default>`
- **하드서브 절대 X — VTT 트랙만**
- 세로 영상: `.video-frame.vertical` + orient-badge
- loadedmetadata → textTracks[0].mode = 'showing'

### 7. CMA 비교 차트 (`#cma`)
- CSS barh (본 매물 vs 부암동 vs 인접권역 vs 카페컨버전 vs Pooled)
- KPI 인라인 패널 (격차 + 순위)

### 8. 5대 분석 (`#analysis`)
- 아코디언: `.analysis-item` → `.analysis-head` 클릭 → `.open`
- 5개: 용도변경 / 가격 / 상권 / 인테리어 / 재건축

### 9. Devil's Advocate (`#devils`)
- 아코디언 5항목: 각 리스크 + 근거 + 반박

### 10. 체크리스트 (`#checklist`)
- `.phase-list li` 클릭 → `.done` 토글
- 매입 전 확인사항 + 담당 관청

### 11. 갤러리 (`#gallery`)
- masonry 그리드: 임장 사진 + 매물 원본 사진
- figure > img + figcaption
- 클릭 → 라이트박스 오버레이

### 12. Footer
- 보고서 일자 + 면책

## 반응형 BP (5단계)

```css
@media(max-width:768px){
  .hero-cta{flex-direction:column}
  .soul-grid{grid-template-columns:1fr}
  .group-grid{grid-template-columns:1fr}
}
@media(max-width:480px){
  h1{font-size:2rem}
  .hero-gauge{width:130px;height:130px}
  .scenario-bar{flex-direction:column}
}
```

## 데이터 파일

| 파일 | 용도 |
|------|------|
| `assets/peer_table.json` | 비교 테이블 렌더 |
| `assets/scores.json` | 점수 데이터 (선택) |
| `assets/soul_cards.json` | Soul 카드 데이터 (선택) |
| `videos/01_approach.mp4` + `.vtt` | 진입 영상 + 자막 |
| `videos/02_site.mp4` + `.vtt` | 부지 영상 + 자막 |
| `videos/03_exterior.mp4` + `.vtt` | 외관 영상 + 자막 |
| `videos/04_interior.mp4` + `.vtt` | 내부 영상 + 자막 |
