#!/bin/bash
# deploy_vercel.sh -- Vercel 배포 스크립트
#
# 처리:
#   1. 영상 파일 100MB 초과 시 자동 압축 (ffmpeg CRF 30 + scale 720)
#   2. vercel deploy --prod --yes
#   3. 배포 URL 출력
#
# 사용법:
#   ./deploy_vercel.sh [랜딩_디렉토리]
#   VERCEL_TOKEN=xxx ./deploy_vercel.sh ./landing
#   VERCEL_SCOPE=my-team ./deploy_vercel.sh ./landing

set -euo pipefail

LANDING_DIR="${1:-.}"
SCOPE="${VERCEL_SCOPE:-grafys-projects}"

# ---- Vercel 토큰 자동 탐색 ----
if [ -z "${VERCEL_TOKEN:-}" ]; then
    # 로컬 Vercel CLI auth.json에서 토큰 추출
    AUTH_FILE="$HOME/.local/share/com.vercel.cli/auth.json"
    if [ -f "$AUTH_FILE" ]; then
        TOKEN=$(python3 -c "import json; print(json.load(open('$AUTH_FILE'))['token'])" 2>/dev/null || true)
    fi

    if [ -z "${TOKEN:-}" ]; then
        echo "오류: VERCEL_TOKEN 환경변수가 설정되지 않았고, 로컬 인증 정보도 찾을 수 없습니다."
        echo "  export VERCEL_TOKEN=your_token"
        echo "  또는 vercel login 실행"
        exit 1
    fi
else
    TOKEN="$VERCEL_TOKEN"
fi

# ---- 디렉토리 확인 ----
if [ ! -d "$LANDING_DIR" ]; then
    echo "오류: 디렉토리를 찾을 수 없습니다: $LANDING_DIR"
    exit 1
fi

echo "=== Vercel 배포 시작 ==="
echo "  디렉토리: $LANDING_DIR"
echo "  스코프: $SCOPE"

# ---- 영상 파일 100MB 초과 압축 ----
VIDEO_COMPRESSED=0
if command -v ffmpeg &>/dev/null; then
    # mp4 파일 검색 (videos 하위 또는 전체)
    for dir_pattern in "$LANDING_DIR/videos" "$LANDING_DIR/video" "$LANDING_DIR/assets/videos" "$LANDING_DIR"; do
        if [ -d "$dir_pattern" ]; then
            while IFS= read -r -d '' f; do
                size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo 0)
                if [ "$size" -gt 104857600 ]; then
                    size_mb=$((size / 1048576))
                    echo "  압축 중: $(basename "$f") (${size_mb}MB > 100MB)..."
                    compressed="${f%.mp4}_compressed.mp4"
                    if ffmpeg -i "$f" \
                        -vf "scale=-2:720" \
                        -c:v libx264 -crf 30 -preset fast \
                        -c:a aac -b:a 96k \
                        -movflags +faststart \
                        "$compressed" -y -loglevel warning 2>&1; then
                        mv "$compressed" "$f"
                        new_size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo 0)
                        new_mb=$((new_size / 1048576))
                        echo "    -> ${new_mb}MB 로 압축 완료"
                        VIDEO_COMPRESSED=$((VIDEO_COMPRESSED + 1))
                    else
                        echo "    -> 압축 실패, 원본 유지"
                        rm -f "$compressed"
                    fi
                fi
            done < <(find "$dir_pattern" -maxdepth 1 -name "*.mp4" -print0 2>/dev/null)
        fi
    done
else
    echo "  경고: ffmpeg가 설치되지 않았습니다. 영상 압축을 건너뜁니다."
fi

if [ "$VIDEO_COMPRESSED" -gt 0 ]; then
    echo "  총 ${VIDEO_COMPRESSED}개 영상 압축 완료"
fi

# ---- Vercel 배포 ----
echo ""
echo "Vercel 배포 실행 중..."
DEPLOY_OUTPUT=$(vercel deploy --prod --yes \
    --token="$TOKEN" \
    --scope "$SCOPE" \
    "$LANDING_DIR" 2>&1)

DEPLOY_EXIT=$?

if [ $DEPLOY_EXIT -ne 0 ]; then
    echo "오류: Vercel 배포 실패 (exit code: $DEPLOY_EXIT)"
    echo "$DEPLOY_OUTPUT"
    exit $DEPLOY_EXIT
fi

# 배포 URL 추출
DEPLOY_URL=$(echo "$DEPLOY_OUTPUT" | grep -oP 'https://[^\s]+\.vercel\.app[^\s]*' | head -1)

if [ -z "$DEPLOY_URL" ]; then
    # URL 패턴이 다를 수 있음
    DEPLOY_URL=$(echo "$DEPLOY_OUTPUT" | tail -1 | tr -d '[:space:]')
fi

echo ""
echo "=== 배포 완료 ==="
echo "  URL: $DEPLOY_URL"
echo "  스코프: $SCOPE"
echo "  영상 압축: ${VIDEO_COMPRESSED}개"
echo ""
echo "$DEPLOY_URL"
