#!/usr/bin/env python3
"""
compute_scores.py -- 8차원 점수 계산 유틸리티

입력: scoring/scores.json (8차원 x 4항목 점수) + 시나리오 가중치
출력: scoring/result.json (종합점수, 등급, 시나리오별 점수, 백분위)

사용법:
  python compute_scores.py --scores scoring/scores.json --output scoring/result.json
  python compute_scores.py --scores scoring/scores.json --validate   # JSON 스키마 검증만
"""
import argparse
import json
import sys
from pathlib import Path

# ---- 8차원 코드 ----
DIMENSIONS = ["LOC", "PRC", "PHY", "REG", "MKT", "FIT", "SCR", "FIN"]
DIMENSION_NAMES = {
    "LOC": "입지·접근성",
    "PRC": "가격 적정성",
    "PHY": "물리적 상태",
    "REG": "법적·규제",
    "MKT": "상권·문화 인프라",
    "FIT": "목적 적합도",
    "SCR": "희소성·미래가치",
    "FIN": "재무·수익성",
}

# ---- 등급 판정 ----
def grade(score: float) -> str:
    """종합 점수 → 등급 변환"""
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


# ---- 가중평균 ----
def weighted_score(dim_scores: dict, weights: dict) -> float:
    """가중평균 계산. 가중치 합 != 100이면 자동 정규화."""
    total_w = sum(weights[d] for d in dim_scores)
    if total_w == 0:
        return 0.0
    return round(sum(dim_scores[d] * weights[d] for d in dim_scores) / total_w, 2)


def normalize_weights(weights: dict) -> dict:
    """가중치 합이 100이 아니면 정규화하여 100으로 맞춤."""
    total = sum(weights.values())
    if total == 0:
        return weights
    if total == 100:
        return weights
    factor = 100.0 / total
    return {k: round(v * factor, 2) for k, v in weights.items()}


# ---- 백분위 추정 ----
def percentile_estimate(score: float) -> int:
    """종합 점수 기반 백분위 추정 (단순 선형 매핑)"""
    if score >= 95: return 99
    if score >= 90: return 95
    if score >= 85: return 90
    if score >= 80: return 80
    if score >= 75: return 70
    if score >= 70: return 60
    if score >= 65: return 50
    if score >= 60: return 40
    if score >= 55: return 30
    if score >= 50: return 20
    return 10


# ---- 민감도 분석 ----
def sensitivity_weight(dim_scores: dict, base_weights: dict, pct: float = 0.1) -> dict:
    """각 차원 가중치 ±pct 변동 시 총점 변화 (기본 ±10%)"""
    base_total = weighted_score(dim_scores, base_weights)
    result = {"base_total": base_total, "per_dimension": {}}
    for d in dim_scores:
        plus_w = base_weights.copy()
        minus_w = base_weights.copy()
        plus_w[d] = round(base_weights[d] * (1 + pct), 3)
        minus_w[d] = round(base_weights[d] * (1 - pct), 3)
        result["per_dimension"][d] = {
            "plus_total": weighted_score(dim_scores, plus_w),
            "minus_total": weighted_score(dim_scores, minus_w),
            "delta_plus": round(weighted_score(dim_scores, plus_w) - base_total, 2),
            "delta_minus": round(weighted_score(dim_scores, minus_w) - base_total, 2),
        }
    return result


def sensitivity_dimension(dim_scores: dict, weights: dict, pct: float = 0.2) -> dict:
    """각 차원 점수 ±pct 변동 시 총점 변화 (기본 ±20%). 0~100 클램프."""
    base_total = weighted_score(dim_scores, weights)
    result = {"base_total": base_total, "per_dimension": {}}
    for d, s in dim_scores.items():
        plus_s = min(100, round(s * (1 + pct), 2))
        minus_s = max(0, round(s * (1 - pct), 2))
        plus_scores = dim_scores.copy()
        minus_scores = dim_scores.copy()
        plus_scores[d] = plus_s
        minus_scores[d] = minus_s
        plus_total = weighted_score(plus_scores, weights)
        minus_total = weighted_score(minus_scores, weights)
        result["per_dimension"][d] = {
            "base_dim_score": s,
            "plus_dim": plus_s,
            "minus_dim": minus_s,
            "plus_total": plus_total,
            "minus_total": minus_total,
            "plus_grade": grade(plus_total),
            "minus_grade": grade(minus_total),
        }
    return result


# ---- 신뢰도 ----
def aggregate_confidence(confidence_pct: dict, weights: dict) -> dict:
    """신뢰도 가중평균"""
    total_w = sum(weights[d] for d in confidence_pct)
    if total_w == 0:
        return {"weighted_confidence_pct": 0, "grade": "D"}
    pct = round(sum(confidence_pct[d] * weights[d] for d in confidence_pct) / total_w, 2)
    if pct >= 95: g = "S"
    elif pct >= 80: g = "A"
    elif pct >= 60: g = "B"
    elif pct >= 40: g = "C"
    else: g = "D"
    return {"weighted_confidence_pct": pct, "grade": g}


# ---- JSON 스키마 검증 ----
SCORES_SCHEMA = {
    "required_keys": ["dimensions", "scenarios"],
    "dimension_fields": ["score", "confidence"],
    "scenario_fields": DIMENSIONS,
}

def validate_scores_json(data: dict) -> list:
    """scores.json 스키마 검증. 오류 목록 반환."""
    errors = []
    for key in SCORES_SCHEMA["required_keys"]:
        if key not in data:
            errors.append(f"최상위 키 '{key}' 누락")

    if "dimensions" in data:
        dims = data["dimensions"]
        for d in DIMENSIONS:
            if d not in dims:
                errors.append(f"차원 '{d}' ({DIMENSION_NAMES.get(d, '')}) 누락")
            else:
                for field in SCORES_SCHEMA["dimension_fields"]:
                    if field not in dims[d]:
                        errors.append(f"차원 '{d}'에 '{field}' 필드 누락")
                    elif not isinstance(dims[d][field], (int, float)):
                        errors.append(f"차원 '{d}'의 '{field}'가 숫자가 아님: {dims[d][field]}")
                    elif not (0 <= dims[d][field] <= 100):
                        errors.append(f"차원 '{d}'의 '{field}'가 범위 밖: {dims[d][field]} (0~100)")

    if "scenarios" in data:
        scenarios = data["scenarios"]
        if not isinstance(scenarios, dict):
            errors.append("'scenarios'가 dict 형식이 아님")
        else:
            for sname, sweights in scenarios.items():
                if not isinstance(sweights, dict):
                    errors.append(f"시나리오 '{sname}'의 가중치가 dict 형식이 아님")
                    continue
                for d in DIMENSIONS:
                    if d not in sweights:
                        errors.append(f"시나리오 '{sname}'에 차원 '{d}' 가중치 누락")

    return errors


# ---- 메인 계산 ----
def compute(data: dict) -> dict:
    """scores.json 데이터로부터 전체 결과 계산"""
    dims = data["dimensions"]
    scenarios_def = data["scenarios"]

    # 차원별 점수 추출
    dim_scores = {d: dims[d]["score"] for d in DIMENSIONS}
    confidence = {d: dims[d]["confidence"] for d in DIMENSIONS}

    # 시나리오별 점수 계산
    scenario_results = {}
    for sname, sweights in scenarios_def.items():
        norm_w = normalize_weights(sweights)
        total = weighted_score(dim_scores, norm_w)
        scenario_results[sname] = {
            "weights_original": sweights,
            "weights_normalized": norm_w,
            "weight_sum": sum(sweights.values()),
            "total_score": total,
            "grade": grade(total),
            "percentile": percentile_estimate(total),
        }

    # 기본 시나리오 (첫 번째) 기준 민감도
    default_scenario = list(scenarios_def.keys())[0]
    default_weights = normalize_weights(scenarios_def[default_scenario])

    sens_w = sensitivity_weight(dim_scores, default_weights)
    sens_d = sensitivity_dimension(dim_scores, default_weights)
    conf = aggregate_confidence(confidence, default_weights)

    return {
        "dim_scores": dim_scores,
        "dimension_names": DIMENSION_NAMES,
        "scenarios": scenario_results,
        "sensitivity_weight_pm10": sens_w,
        "sensitivity_dim_pm20": sens_d,
        "confidence_aggregate": conf,
        "default_scenario": default_scenario,
    }


def main():
    parser = argparse.ArgumentParser(
        description="8차원 점수 계산 유틸리티",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시 scores.json 형식:
{
  "dimensions": {
    "LOC": {"score": 70, "confidence": 87},
    "PRC": {"score": 92, "confidence": 87},
    ...
  },
  "scenarios": {
    "default": {"LOC": 15, "PRC": 20, ...},
    "A_lifestyle": {"LOC": 13, "PRC": 18, ...},
    ...
  }
}
        """,
    )
    parser.add_argument("--scores", required=True, help="입력 scores.json 경로")
    parser.add_argument("--output", default=None, help="출력 result.json 경로 (미지정 시 stdout)")
    parser.add_argument("--validate", action="store_true", help="JSON 스키마 검증만 수행")
    args = parser.parse_args()

    # 입력 로드
    scores_path = Path(args.scores)
    if not scores_path.exists():
        print(f"오류: 파일을 찾을 수 없습니다: {scores_path}", file=sys.stderr)
        sys.exit(1)

    with open(scores_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 스키마 검증
    errors = validate_scores_json(data)
    if errors:
        print("스키마 검증 오류:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    if args.validate:
        print("스키마 검증 통과")
        sys.exit(0)

    # 계산
    result = compute(data)

    # 콘솔 요약 출력
    print("\n=== 시나리오별 종합점수 ===")
    for sname, sv in result["scenarios"].items():
        marker = " (기본)" if sname == result["default_scenario"] else ""
        print(f"  {sname:20s} -> {sv['total_score']:.2f} {sv['grade']} (상위 {sv['percentile']}%){marker}")

    print(f"\n=== 신뢰도 가중평균 ===")
    conf = result["confidence_aggregate"]
    print(f"  {conf['weighted_confidence_pct']}% -> {conf['grade']}")

    # 결과 저장
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n결과 저장: {out_path}")
    else:
        print("\n=== 전체 결과 JSON ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
