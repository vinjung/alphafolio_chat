# 🛠️ 프로젝트 스크립트 가이드

이 폴더에는 프로젝트 개발 및 배포에 필요한 유틸리티 스크립트들이 있습니다.

## 📁 폴더 구조

```
scripts/
├── image-optimization/
│   ├── convert-to-webp.sh       # WebP 변환 스크립트
│   └── README.md                # 이미지 최적화 가이드
├── deployment/
│   ├── build-check.sh           # 빌드 전 검증
│   └── deploy.sh                # 배포 스크립트
└── README.md                    # 이 파일
```

## 🚀 빠른 시작

### 1️⃣ 스크립트 권한 설정
```bash
# 모든 스크립트에 실행 권한 부여
npm run scripts:setup

# 또는 수동으로
chmod +x scripts/**/*.sh
```

### 2️⃣ 이미지 최적화 실행
```bash
# WebP 변환 (권장)
npm run images:optimize

# 또는 직접 실행
./scripts/image-optimization/convert-to-webp.sh
```

### 3️⃣ 빌드 전 체크
```bash
# 빌드 전 검증 + 빌드
npm run build:check
```

## 📋 사용 가능한 npm 스크립트

| 명령어 | 설명 | 파일 |
|--------|------|------|
| `npm run images:optimize` | 이미지를 WebP로 변환 | `convert-to-webp.sh` |
| `npm run scripts:setup` | 모든 스크립트 권한 설정 | - |
| `npm run build:check` | 빌드 전 검증 | `build-check.sh` |
| `npm run optimize` | 이미지 최적화 + 빌드 | 복합 명령 |

## 🛠️ 개별 스크립트 설명

### 🖼️ 이미지 최적화 (`image-optimization/`)
- **목적**: PNG 이미지를 WebP로 변환하여 파일 크기 절약
- **대상**: `public/images/` 폴더의 PNG 파일들
- **효과**: 평균 40-50% 파일 크기 감소

```bash
# 사용법
./scripts/image-optimization/convert-to-webp.sh

# 결과 예시
✅ slide-1.webp 완료
  📊 150KB → 85KB (43% 감소)
```

### 🚀 배포 스크립트 (`deployment/`)
- **목적**: 배포 전 필수 검증 및 자동화
- **포함**: Lint 체크, 타입 체크, 빌드 테스트

## ⚠️ 주의사항

### 🔧 필수 도구 설치
```bash
# macOS
brew install webp

# Ubuntu/Debian
sudo apt-get install webp

# 확인
cwebp -version
```

### 📂 실행 위치
**모든 스크립트는 프로젝트 루트에서 실행해야 합니다!**

```bash
# ✅ 올바른 실행 (프로젝트 루트에서)
./scripts/image-optimization/convert-to-webp.sh

# ❌ 잘못된 실행 (scripts 폴더 안에서)
cd scripts && ./image-optimization/convert-to-webp.sh
```

### 🔄 백업 권장
중요한 작업 전에는 git으로 커밋하거나 백업을 만들어 두세요.

```bash
# 작업 전 커밋
git add .
git commit -m "이미지 최적화 전 백업"

# 이미지 최적화 실행
npm run images:optimize
```

## 🆘 문제 해결

### 권한 오류
```bash
chmod +x scripts/image-optimization/convert-to-webp.sh
```

### cwebp 도구 없음
```bash
# macOS
brew install webp

# Ubuntu
sudo apt-get install webp
```

### 경로 오류
프로젝트 루트 디렉토리에서 실행했는지 확인:
```bash
ls -la | grep package.json  # package.json이 보여야 함
```

## 📞 지원

스크립트 관련 문제나 개선 제안이 있으면 팀에 문의하세요.

---
📝 **마지막 업데이트**: 2025-06-02
