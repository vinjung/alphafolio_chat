#!/bin/bash

# WebP 이미지 변환 스크립트
# 사용법: ./scripts/image-optimization/convert-to-webp.sh

set -e  # 에러 발생 시 스크립트 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 로그 출력
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# WebP 도구 확인
check_webp_tools() {
    if ! command -v cwebp &> /dev/null; then
        log_error "cwebp 도구가 설치되지 않았습니다."
        echo ""
        echo "설치 방법:"
        echo "  macOS: brew install webp"
        echo "  Ubuntu: sudo apt-get install webp"
        echo "  Windows: https://developers.google.com/speed/webp/download"
        exit 1
    fi
    log_success "cwebp 도구 확인됨"
}

# 파일 크기 계산 (크로스 플랫폼)
get_file_size() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        stat -f%z "$1"
    else
        # Linux
        stat -c%s "$1"
    fi
}

# 바이트를 사람이 읽기 쉬운 형태로 변환
human_readable_size() {
    local bytes=$1
    if [ $bytes -gt 1048576 ]; then
        echo "$(($bytes / 1048576))MB"
    elif [ $bytes -gt 1024 ]; then
        echo "$(($bytes / 1024))KB"
    else
        echo "${bytes}B"
    fi
}

# 메인 변환 함수
convert_images() {
    local source_dir="public/images"
    local total_original=0
    local total_webp=0
    local converted_count=0

    log_info "이미지 변환 시작: $source_dir"

    if [ ! -d "$source_dir" ]; then
        log_error "디렉토리를 찾을 수 없습니다: $source_dir"
        exit 1
    fi

    # PNG 파일들 처리
    for file in "$source_dir"/*.png; do
        # 파일이 존재하는지 확인
        if [ ! -f "$file" ]; then
            log_warning "PNG 파일을 찾을 수 없습니다"
            continue
        fi

        filename=$(basename "$file" .png)
        webp_file="$source_dir/${filename}.webp"

        log_info "변환 중: $file"

        # WebP로 변환 (품질 85, 메타데이터 유지)
        if cwebp -q 85 -m 6 -mt "$file" -o "$webp_file" > /dev/null 2>&1; then
            # 파일 크기 비교
            original_size=$(get_file_size "$file")
            webp_size=$(get_file_size "$webp_file")

            # 백분율 계산
            if [ $original_size -gt 0 ]; then
                reduction=$(( (original_size - webp_size) * 100 / original_size ))
            else
                reduction=0
            fi

            log_success "완료: ${filename}.webp"
            echo "  📊 $(human_readable_size $original_size) → $(human_readable_size $webp_size) (${reduction}% 감소)"

            total_original=$((total_original + original_size))
            total_webp=$((total_webp + webp_size))
            converted_count=$((converted_count + 1))
        else
            log_error "변환 실패: $file"
        fi
    done

    # 총 결과 출력
    echo ""
    log_success "변환 완료!"
    echo "📈 총 결과:"
    echo "  • 변환된 파일: $converted_count개"
    echo "  • 원본 크기: $(human_readable_size $total_original)"
    echo "  • WebP 크기: $(human_readable_size $total_webp)"

    if [ $total_original -gt 0 ]; then
        total_reduction=$(( (total_original - total_webp) * 100 / total_original ))
        echo "  • 총 절약: $(human_readable_size $((total_original - total_webp))) (${total_reduction}% 감소)"
    fi
}

# 후속 작업 안내
show_next_steps() {
    echo ""
    log_info "다음 단계:"
    echo "1. 컴포넌트에서 .png → .webp 경로 수정"
    echo "2. git add scripts/ public/images/*.webp"
    echo "3. 배포 후 성능 테스트"
    echo ""
    echo "원본 PNG 파일 삭제 (선택사항):"
    echo "  find public/images -name '*.png' -not -path '*/icons/*' -delete"
}

# 메인 실행
main() {
    echo "🖼️  WebP 이미지 변환 스크립트"
    echo "================================"

    check_webp_tools
    convert_images
    show_next_steps
}

# 스크립트 실행
main "$@"
