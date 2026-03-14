import imageCompression from 'browser-image-compression';

interface CloudinaryUploadResult {
  success: boolean;
  url?: string;
  error?: string;
}

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

/**
 * Cloudinary에 이미지를 직접 업로드합니다
 */
export async function uploadToCloudinary(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<CloudinaryUploadResult> {
  try {
    // 환경변수 체크
    const cloudName = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME;
    const uploadPreset = process.env.NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET;


    if (!cloudName || !uploadPreset) {
      return {
        success: false,
        error: 'Cloudinary 설정이 누락되었습니다.',
      };
    }

    // 파일 타입 체크
    if (!file.type.startsWith('image/')) {
      return {
        success: false,
        error: '이미지 파일만 업로드 가능합니다.',
      };
    }

    // 파일 크기 체크 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      return {
        success: false,
        error: '파일 크기는 10MB 이하로 해주세요.',
      };
    }

    // 이미지 압축 옵션
    const compressionOptions = {
      maxSizeMB: 1, // 1MB로 압축
      maxWidthOrHeight: 800, // 최대 800px
      useWebWorker: true,
      fileType: 'image/jpeg', // JPEG로 변환
    };

    // 이미지 압축
    const compressedFile = await imageCompression(file, compressionOptions);

    // FormData 생성
    const formData = new FormData();
    formData.append('file', compressedFile);
    formData.append('upload_preset', uploadPreset);
    formData.append('folder', 'profile_images'); // 프로필 이미지 폴더

    // Cloudinary 업로드 URL
    const uploadUrl = `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`;


    // XMLHttpRequest로 진행률 추적
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();

      // 진행률 추적
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress: UploadProgress = {
              loaded: event.loaded,
              total: event.total,
              percentage: Math.round((event.loaded / event.total) * 100),
            };
            onProgress(progress);
          }
        });
      }

      // 완료 처리
      xhr.addEventListener('load', () => {

        if (xhr.status === 200) {
          try {
            const result = JSON.parse(xhr.responseText);
            resolve({
              success: true,
              url: result.secure_url,
            });
          } catch (_error) {
            resolve({
              success: false,
              error: '응답 파싱 오류가 발생했습니다.',
            });
          }
        } else {
          resolve({
            success: false,
            error: `업로드 실패: ${xhr.status} - ${xhr.responseText}`,
          });
        }
      });

      // 에러 처리
      xhr.addEventListener('error', () => {
        resolve({
          success: false,
          error: '네트워크 오류가 발생했습니다.',
        });
      });

      // 요청 시작
      xhr.open('POST', uploadUrl);
      xhr.send(formData);
    });
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '알 수 없는 오류',
    };
  }
}

export function generateThumbnailUrl(originalUrl: string): string {
  if (!originalUrl || !originalUrl.includes('cloudinary.com')) {
    return originalUrl; // Cloudinary URL이 아니면 원본 반환
  }

  return originalUrl.replace(
    '/upload/',
    '/upload/w_25,h_25,c_fill,g_face,r_max/'
  );
}
