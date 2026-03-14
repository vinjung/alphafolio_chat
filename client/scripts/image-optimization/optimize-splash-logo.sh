#!/bin/bash

# 기존 PNG 스플래시 로고 최적화 스크립트
# scripts/image-optimization/optimize-splash-logo.sh

set -e

# 색상 코드
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "🖼️ 스플래시 로고 최적화"
echo "========================"

# 원본 PNG 파일 찾기
PNG_FILES=(
    "public/splash-logo.png"
    "public/images/splash-logo.png"
    "src/assets/splash-logo.png"
    "assets/splash-logo.png"
)

ORIGINAL_PNG=""
for file in "${PNG_FILES[@]}"; do
    if [ -f "$file" ]; then
        ORIGINAL_PNG="$file"
        log_success "원본 PNG 발견: $file"
        break
    fi
done

if [ -z "$ORIGINAL_PNG" ]; then
    log_warning "PNG 파일을 찾을 수 없습니다. 다음 위치들을 확인했습니다:"
    printf '%s\n' "${PNG_FILES[@]}"
    echo ""
    echo "수동으로 파일 경로를 지정하려면:"
    echo "./scripts/image-optimization/optimize-splash-logo.sh /path/to/your/logo.png"
    exit 1
fi

# 수동 경로 지정된 경우
if [ ! -z "$1" ] && [ -f "$1" ]; then
    ORIGINAL_PNG="$1"
    log_info "수동 지정된 PNG 사용: $1"
fi

# 출력 디렉토리 생성
OUTPUT_DIR="public/images"
mkdir -p "$OUTPUT_DIR"

# 원본 파일 정보
ORIGINAL_SIZE=$(stat -f%z "$ORIGINAL_PNG" 2>/dev/null || stat -c%s "$ORIGINAL_PNG")
log_info "원본 크기: $((ORIGINAL_SIZE / 1024))KB"

# 1. public/images/로 복사 (경로 통일)
DEST_PNG="$OUTPUT_DIR/splash-logo.png"
if [ "$ORIGINAL_PNG" != "$DEST_PNG" ]; then
    cp "$ORIGINAL_PNG" "$DEST_PNG"
    log_success "PNG 복사 완료: $DEST_PNG"
fi

# 2. 고해상도 버전 생성 (ImageMagick 사용, 선택사항)
if command -v convert &> /dev/null; then
    log_info "고해상도 버전 생성 중..."
    convert "$DEST_PNG" -resize 200% "$OUTPUT_DIR/splash-logo@2x.png"
    convert "$DEST_PNG" -resize 300% "$OUTPUT_DIR/splash-logo@3x.png"
    log_success "레티나 이미지 생성 완료"
fi

# 3. WebP 변환
if command -v cwebp &> /dev/null; then
    log_info "WebP 변환 중..."

    # 1x WebP
    cwebp -q 90 -m 6 "$DEST_PNG" -o "$OUTPUT_DIR/splash-logo.webp" > /dev/null 2>&1
    WEBP_SIZE=$(stat -f%z "$OUTPUT_DIR/splash-logo.webp" 2>/dev/null || stat -c%s "$OUTPUT_DIR/splash-logo.webp")
    REDUCTION=$(( (ORIGINAL_SIZE - WEBP_SIZE) * 100 / ORIGINAL_SIZE ))
    log_success "WebP 생성: $((WEBP_SIZE / 1024))KB (${REDUCTION}% 감소)"

    # 2x, 3x WebP (있다면)
    for scale in "2x" "3x"; do
        if [ -f "$OUTPUT_DIR/splash-logo@${scale}.png" ]; then
            cwebp -q 90 -m 6 "$OUTPUT_DIR/splash-logo@${scale}.png" -o "$OUTPUT_DIR/splash-logo@${scale}.webp" > /dev/null 2>&1
            log_success "@${scale} WebP 생성"
        fi
    done
else
    log_warning "cwebp가 설치되지 않음. WebP 변환 건너뜀"
    echo "설치: brew install webp (macOS) 또는 sudo apt-get install webp (Ubuntu)"
fi

echo ""
log_success "최적화 완료!"
echo "생성된 파일들:"
ls -la "$OUTPUT_DIR"/splash-logo* 2>/dev/null || echo "파일 확인 불가"

echo ""
log_info "다음 단계:"
echo "1. 컴포넌트에서 Next.js Image 컴포넌트로 교체"
echo "2. SVG 파일 제거 (백업 후)"
echo "3. 성능 테스트"
