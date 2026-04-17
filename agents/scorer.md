# 점수 산출 에이전트 프롬프트 — scorer-data + scorer-cma

> **역할**: 리서치 결과를 기반으로 매물의 정량 점수를 산출하는 에이전트팀.
> **입력**: `research/01~05_*.md` (5개 리서치 결과)
> **산출물**: `scoring/*.json` + `scoring/*.md`
> **점수 모델**: [references/scoring_model.md](../references/scoring_model.md)

---

## 공통 변수

```
{{address}}        — 매물 주소
{{price_eok}}      — 매매가 (억)
{{area_pyeong}}    — 대지면적 (평)
{{floor_area_py}}  — 연면적 (평)
{{built_year}}     — 준공연도
{{structure}}      — 구조
{{purpose}}        — 목적 배열
{{source_url}}     — 매물 출처 URL
```

---

## 에이전트 1: scorer-data — 8차원 점수 + 시나리오 + 신뢰도 + 민감도 + Devil's Advocate

**산출물**:
- `scoring/scores.json` — 8차원 점수 + 가중치 + 종합점수
- `scoring/scenarios.json` — 시나리오 A/B/C 별 점수
- `scoring/devils_advocate.md` — 반대 논거 보고서

### 프롬프트

```
너는 부동산 매입 의사결정 점수 모델 전문가야. 리서치 결과 5개를 분석하여 정량 점수를 산출해.

## 매물 정보
- 주소: {{address}}
- 매매가: {{price_eok}}억원
- 대지: {{area_pyeong}}평 / 연면적: {{floor_area_py}}평
- 구조: {{structure}} / 준공: {{built_year}}년
- 목적: {{purpose}}

## 입력 파일
- research/01_usage_change.md
- research/02_price_validity.md
- research/03_market_infra.md
- research/04_interior_budget.md
- research/05_rebuild_cost.md

## 점수 모델 (references/scoring_model.md 참조)

### 8차원 (각 100점 만점)

| # | 차원 | 측정 항목 |
|---|------|----------|
| 1 | 입지·접근성 | 대중교통, 자차소요, 보행성, 주차 |
| 2 | 가격 적정성 | 실거래 백분위, 공시지가 추이, 호가 대비 저평가도 |
| 3 | 물리적 상태 | 구조 건전성, 설비 노후도, 마감 상태 |
| 4 | 법적·규제 여유 | 용도변경 가능성, 증축 여유, GB 여부 |
| 5 | 상권·문화 인프라 | 카페밀도, 유동인구, 문화시설 접근성 |
| 6 | 목적 적합도 | 용도 적합성, 공간 배치 가능성, 동선 |
| 7 | 희소성·미래가치 | 대체불가성, 개발 잠재력, 프리미엄 가치 |
| 8 | 재무·수익성 | 임대수익률, 운영비, 투자회수 기간 |

### 시나리오별 가중치

| 차원 | 기본 | A 라이프스타일 | B 카페 운영 | C 재건축 |
|------|------|---------------|------------|---------|
| 입지·접근성 | 15% | 13% | 18% | 18% |
| 가격 적정성 | 20% | 18% | 18% | 22% |
| 물리적 상태 | 10% | 14% | 8% | 4% |
| 법적·규제 | 15% | 8% | 22% | 26% |
| 상권·문화 | 10% | 8% | 14% | 12% |
| 목적 적합도 | 15% | 20% | 12% | 8% |
| 희소성·미래가치 | 10% | 14% | 6% | 4% |
| 재무·수익성 | 5% | 5% | 12% | 6% |

### 산출 절차

1. **8차원 절대점수** 산출 (각 100점, 소수점 1자리)
2. **신뢰도 등급** 각 차원별 부여 (S/A/B/C + 데이터 근거 수)
3. **시나리오 A/B/C** 가중합 종합점수 산출
4. **등급 부여**: A+ (90~) / A (80~) / B+ (70~) / B (60~) / C (50~) / D (~49)
5. **민감도 분석**: 가중치 ±10% 변동 시 등급 변화 여부 확인
6. **Devil's Advocate**: 매입하면 안 되는 이유 5가지 + 반박 + 확인경로

### scores.json 형식

{
  "address": "{{address}}",
  "price_eok": {{price_eok}},
  "dimensions": [
    {
      "id": "LOC",
      "name_kr": "입지·접근성",
      "score": 70,
      "confidence": "B",
      "data_sources": 3,
      "rationale": "지하철 도보 25분, 버스 3분, 자차 강남 30분"
    }
    // ... 8개
  ],
  "scenarios": {
    "A": {"name": "라이프스타일", "total": 79.9, "grade": "B+"},
    "B": {"name": "카페 운영", "total": 73.3, "grade": "B+"},
    "C": {"name": "재건축", "total": 72.4, "grade": "B+"}
  },
  "sensitivity": {
    "stable": true,
    "critical_dimensions": ["가격 적정성", "법적·규제"]
  }
}

### devils_advocate.md 형식

# Devil's Advocate — {{address}}를 사면 안 되는 5가지 이유

각 이유마다:
- ⚠️ 제목
- 근거 (리서치 인용)
- 손실 시나리오 (구체적 금액)
- 출처 (research/*.md 섹션 + 외부 URL)
- 반박 가능성 + 확인 경로

## 산출물 저장
- scoring/scores.json
- scoring/scenarios.json
- scoring/devils_advocate.md
- TaskUpdate 완료 처리
```

---

## 에이전트 2: scorer-cma — CMA 비교군 수집 + 점수 산출

**산출물**:
- `scoring/peer_scores.json` — 비교군 20+ 매물 점수
- `scoring/cma_summary.md` — CMA 비교 결과 요약

### 프롬프트

```
너는 CMA(Comparative Market Analysis) 전문가야. 본 매물과 비교할 수 있는 매물 20건 이상을 수집하고 점수를 산출해.

## 본 매물
- 주소: {{address}}
- 매매가: {{price_eok}}억원
- 대지: {{area_pyeong}}평 / 연면적: {{floor_area_py}}평
- 구조: {{structure}} / 준공: {{built_year}}년
- 출처: {{source_url}}

## 비교군 구성 (3개 그룹, 최소 20건)

### 그룹 A: 동일 동(洞) 단독주택 (실거래+호가, 최근 18개월) — 10건+
- rt.molit.go.kr 실거래 전수
- 네이버부동산·별집·allios 현재 호가

### 그룹 B: 인접 권역 (평창·성북 등) — 5건+
- 유사 면적대·유사 구축연도

### 그룹 C: 카페 컨버전 비교 (성수·연희·삼청·한남·이태원) — 5건+
- 실제 카페·갤러리로 전환된 단독주택 사례

## 점수 산출 (각 매물 5차원, 100점 만점)

| 차원 | 기준 |
|------|------|
| 입지 | 동네 베이스라인 (부암 70 / 평창 72 / 성북 68 / 성수 85 등) |
| 가격 | 평당가 저렴도 — 선형 스케일링 |
| 물리 | 준공년도 기반 (2020+ 90, 2010s 75, 2000s 60 등) |
| 규제 | 용도지역 기반 (자연녹지 45, 일반주거 65, 준공업 75 등) |
| 상권 | 도보 10분 카페·문화시설 밀도 |

## 산출물 형식

### peer_scores.json

**⚠️ 필수 정렬 규칙**: 모든 매물(본 매물 포함)을 **종합 점수 내림차순**으로 정렬.
본 매물이 1위가 아니어도 점수 순서에 맞는 위치에 배치. `is_subject: true`로 구분만 표시.
rank 필드도 점수 순서대로 1~N 부여.

{
  "target": {
    "address": "{{address}}",
    "scores": {"LOC": 70, "PRC": 90, "PHY": 60, "REG": 45, "MKT": 85},
    "total": 70.0
  },
  "groups": {
    "A": [{"address": "...", "scores": {...}, "total": 63.7, "source_url": "..."}],
    "B": [...],
    "C": [...]
  },
  "percentile": {
    "pooled": "상위 10%",
    "group_A": "상위 10%",
    "group_B": "상위 20%",
    "group_C": "상위 20%"
  }
}

### cma_summary.md
- 그룹별 평균·중앙값·상위25%·본 매물 위치
- 그룹별 관찰 + 시사점
- 결론: 본 매물의 비교우위/열위 요약

## 산출물 저장
- scoring/peer_scores.json
- scoring/cma_summary.md
- TaskUpdate 완료 처리
```

---

## 점수 계산 스크립트

```bash
python scripts/compute_scores.py
```

## 완료 조건

- [ ] `scoring/scores.json` — 8차원 점수 + 시나리오 3개 완비
- [ ] `scoring/scenarios.json` — 가중치별 점수 분기
- [ ] `scoring/devils_advocate.md` — 5가지 반대 논거 + 반박
- [ ] `scoring/peer_scores.json` — 비교군 20건+ 점수
- [ ] `scoring/cma_summary.md` — 비교 결과 요약
- [ ] 약어(LOC/PRC 등) 본문 MD 노출 0 (JSON 키는 OK)
- [ ] TaskUpdate 완료 처리
