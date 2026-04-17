#!/usr/bin/env python3
"""
validate_images.py -- 이미지 중복 검출 + 매칭 검증 스크립트

입력: 이미지 디렉토리
출력: 중복 검출 + 매칭 리포트 JSON

사용법:
  python validate_images.py --dir img/ --output report.json
  python validate_images.py --dir img/ --threshold 20 --output report.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


# ---- Perceptual Hash ----
def compute_phash(image_path: str, hash_size: int = 16) -> str:
    """PIL 기반 perceptual hash (hash_size x hash_size -> hash_size^2 bit)"""
    try:
        from PIL import Image
    except ImportError:
        print("오류: Pillow 패키지가 필요합니다. pip install Pillow", file=sys.stderr)
        sys.exit(1)

    img = Image.open(image_path).convert("L")  # 그레이스케일
    img = img.resize((hash_size, hash_size), Image.LANCZOS)

    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)

    # 평균보다 밝으면 1, 어두우면 0
    bits = "".join("1" if p > avg else "0" for p in pixels)

    # 바이너리 -> 16진수
    hex_hash = hex(int(bits, 2))[2:].zfill(hash_size * hash_size // 4)
    return hex_hash


def hamming_distance(hash1: str, hash2: str) -> int:
    """두 해시 간 해밍 거리 (다른 비트 수)"""
    if len(hash1) != len(hash2):
        return max(len(hash1), len(hash2)) * 4  # 최대 거리 반환

    # 16진수 -> 정수 -> XOR -> 1비트 카운트
    xor = int(hash1, 16) ^ int(hash2, 16)
    return bin(xor).count("1")


# ---- 이미지 메타데이터 ----
def get_image_info(image_path: str) -> dict:
    """이미지 기본 정보 추출"""
    try:
        from PIL import Image
        img = Image.open(image_path)
        return {
            "path": str(image_path),
            "filename": os.path.basename(image_path),
            "size_bytes": os.path.getsize(image_path),
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
        }
    except Exception as e:
        return {
            "path": str(image_path),
            "filename": os.path.basename(image_path),
            "error": str(e),
        }


# ---- 중복 검출 ----
def find_duplicates(image_dir: str, threshold: int = 25, hash_size: int = 16) -> dict:
    """디렉토리 내 이미지 중복/유사 검출"""
    img_dir = Path(image_dir)
    if not img_dir.exists():
        print(f"오류: 디렉토리를 찾을 수 없습니다: {img_dir}", file=sys.stderr)
        sys.exit(1)

    # 이미지 파일 수집
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(img_dir.glob(f"*{ext}"))
        image_files.extend(img_dir.glob(f"*{ext.upper()}"))
    image_files = sorted(set(image_files))

    if not image_files:
        return {
            "summary": {"total_images": 0, "duplicates": 0, "unique": 0},
            "images": [],
            "duplicate_pairs": [],
        }

    print(f"  {len(image_files)}개 이미지 파일 발견")

    # 해시 계산
    hashes = {}
    images_info = []
    for img_path in image_files:
        print(f"  해싱: {img_path.name}", end="...", flush=True)
        try:
            h = compute_phash(str(img_path), hash_size)
            info = get_image_info(str(img_path))
            info["phash"] = h
            hashes[str(img_path)] = h
            images_info.append(info)
            print(" OK")
        except Exception as e:
            print(f" 오류: {e}")
            images_info.append({
                "path": str(img_path),
                "filename": img_path.name,
                "error": str(e),
            })

    # 쌍별 비교
    paths = list(hashes.keys())
    duplicate_pairs = []
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            dist = hamming_distance(hashes[paths[i]], hashes[paths[j]])
            if dist <= threshold:
                pair = {
                    "file_a": os.path.basename(paths[i]),
                    "file_b": os.path.basename(paths[j]),
                    "path_a": paths[i],
                    "path_b": paths[j],
                    "hamming_distance": dist,
                    "similarity_pct": round((1 - dist / (hash_size * hash_size)) * 100, 1),
                    "flag": "EXACT" if dist == 0 else "SIMILAR",
                }
                duplicate_pairs.append(pair)

    # 중복에 관련된 고유 파일 수
    dup_files = set()
    for pair in duplicate_pairs:
        dup_files.add(pair["path_a"])
        dup_files.add(pair["path_b"])

    return {
        "summary": {
            "total_images": len(image_files),
            "hashed": len(hashes),
            "duplicate_pairs": len(duplicate_pairs),
            "files_with_duplicates": len(dup_files),
            "unique": len(image_files) - len(dup_files),
            "threshold": threshold,
            "hash_size": hash_size,
        },
        "images": images_info,
        "duplicate_pairs": sorted(duplicate_pairs, key=lambda x: x["hamming_distance"]),
    }


def main():
    parser = argparse.ArgumentParser(description="이미지 중복 검출 + 매칭 검증 스크립트")
    parser.add_argument("--dir", required=True, help="이미지 디렉토리 경로")
    parser.add_argument("--output", default=None, help="리포트 JSON 출력 경로")
    parser.add_argument("--threshold", type=int, default=25,
                        help="해밍 거리 임계값 (기본 25, 낮을수록 엄격)")
    parser.add_argument("--hash-size", type=int, default=16,
                        help="해시 크기 (기본 16 -> 256bit)")
    args = parser.parse_args()

    print(f"이미지 디렉토리 스캔: {args.dir}")
    report = find_duplicates(args.dir, threshold=args.threshold, hash_size=args.hash_size)

    summary = report["summary"]
    print(f"\n=== 검증 완료 ===")
    print(f"  전체: {summary['total_images']} | 해싱: {summary['hashed']}")
    print(f"  중복 쌍: {summary['duplicate_pairs']} | 중복 관련 파일: {summary['files_with_duplicates']}")

    if report["duplicate_pairs"]:
        print(f"\n=== 중복/유사 이미지 쌍 ===")
        for pair in report["duplicate_pairs"]:
            flag = pair["flag"]
            print(f"  [{flag}] {pair['file_a']} <-> {pair['file_b']} "
                  f"(거리: {pair['hamming_distance']}, 유사도: {pair['similarity_pct']}%)")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n리포트 저장: {out_path}")


if __name__ == "__main__":
    main()
