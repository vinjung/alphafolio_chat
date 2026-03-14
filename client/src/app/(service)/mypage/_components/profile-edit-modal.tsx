'use client';

import { useState, useRef } from 'react';
import { Modal } from '@/components/shared/modal';
import { Text } from '@/components/shared/text';
import { Input } from '@/components/shared/input';
import { Icon } from '@/components/icons';
import { updateProfileAction } from '@/lib/server/actions/user';
import { showGlobalSnackbar } from '@/components/shared/snackbar';
import { uploadToCloudinary } from '@/lib/utils/cloudinary-upload';
import { cx } from '@/lib/utils/cva.config';
import type { User } from '@/lib/server/models';
import Image from 'next/image';

interface ProfileEditModalProps {
  isVisible: boolean;
  onCloseAction: () => void;
  user: User;
}

interface ValidationState {
  isValid: boolean;
  message: string;
}

export function ProfileEditModal({
  isVisible,
  onCloseAction,
  user,
}: ProfileEditModalProps) {
  // 기본 상태
  const [nickname, setNickname] = useState(user.nickname || '');
  const [validation, setValidation] = useState<ValidationState>({
    isValid: true,
    message: '',
  });
  const [isLoading, setIsLoading] = useState(false);

  // 이미지 업로드 관련 상태
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 클라이언트 validation 함수
  const validateNickname = (value: string): ValidationState => {
    if (!value || value.trim() === '') {
      return {
        isValid: false,
        message: '닉네임이 비어있어요! 전설의 그 이름 지어주세요!',
      };
    }

    const trimmed = value.trim();

    if (trimmed.length < 2) {
      return {
        isValid: false,
        message: '닉네임은 최소 2자 이상... 좀만 더...',
      };
    }

    if (trimmed.length > 8) {
      return {
        isValid: false,
        message: '닉네임은 최대 8자까지 가능! 너무 길면 기억못돼',
      };
    }

    if (!/^[가-힣a-zA-Z0-9]+$/.test(trimmed)) {
      return {
        isValid: false,
        message: '특수문자는 안 돼상. 한글, 영어, 숫자만 써주세요!',
      };
    }

    return { isValid: true, message: '' };
  };

  // 닉네임 변경 핸들러
  const handleNicknameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setNickname(value);

    // 실시간 validation
    const validationResult = validateNickname(value);
    setValidation(validationResult);
  };

  // 이미지 선택 버튼 클릭 핸들러
  const handleImageSelect = () => {
    fileInputRef.current?.click();
  };

  // 파일 선택 핸들러
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingImage(true);

    try {
      // Cloudinary 업로드
      const result = await uploadToCloudinary(file);

      if (result.success && result.url) {
        // 서버에 이미지 URL 저장
        const formData = new FormData();
        formData.append('profileImageUrl', result.url);
        if (nickname !== user.nickname) {
          formData.append('nickname', nickname.trim());
        }

        const updateResult = await updateProfileAction(formData);

        if (updateResult.success) {
          showGlobalSnackbar('프로필 이미지가 업데이트되었습니다! 🎉', {
            position: 'top',
          });
        } else {
          showGlobalSnackbar(
            updateResult.message || '프로필 업데이트에 실패했습니다.',
            {
              variant: 'error',
              position: 'top',
            }
          );
        }
      } else {
        showGlobalSnackbar(result.error || '이미지 업로드에 실패했습니다.', {
          variant: 'error',
          position: 'top',
        });
      }
    } catch (uploadError) {
      console.error('이미지 업로드 오류:', uploadError);
      showGlobalSnackbar('이미지 업로드 중 오류가 발생했습니다.', {
        variant: 'error',
        position: 'top',
      });
    } finally {
      setIsUploadingImage(false);
      // 파일 input 리셋
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 저장 핸들러 (닉네임만)
  const handleSave = async () => {
    if (!validation.isValid || nickname.trim() === '') return;

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('nickname', nickname.trim());

      const result = await updateProfileAction(formData);

      if (result.success) {
        showGlobalSnackbar('프로필이 업데이트되었습니다! 🎉', {
          position: 'top',
        });
        onCloseAction();
      } else if (result.errors?.nickname) {
        setValidation({ isValid: false, message: result.errors.nickname });
      } else {
        showGlobalSnackbar(result.message || '업데이트에 실패했습니다.', {
          variant: 'error',
          position: 'top',
        });
      }
    } catch (saveError) {
      console.error('프로필 업데이트 오류:', saveError);
      showGlobalSnackbar('네트워크 오류가 발생했습니다.', {
        variant: 'error',
        position: 'top',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 취소 핸들러
  const handleCancel = () => {
    setNickname(user.nickname || '');
    setValidation({ isValid: true, message: '' });
    onCloseAction();
  };

  // 저장 버튼 활성화 조건
  const canSave = nickname.trim() !== '' && !isLoading && !isUploadingImage;
  const hasChanges = nickname.trim() !== (user.nickname || '');

  const profileImage = user.profileImageUrl || '/images/default-profile.webp';

  return (
    <Modal
      isVisible={isVisible}
      onCloseAction={handleCancel}
      title=""
      variant="fullscreen"
      size="full"
      showCloseButton={false}
      disableAnimation
    >
      <div className="flex flex-col h-full">
        {/* 커스텀 헤더 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200 flex-shrink-0">
          <button
            onClick={handleCancel}
            className="p-1 rounded-full hover:bg-neutral-100 transition-colors"
            aria-label="모달 닫기"
          >
            <Icon.close className="text-neutral-1100" />
          </button>

          <Text variant="s1">프로필 편집</Text>

          <button
            onClick={handleSave}
            disabled={!canSave || !hasChanges}
            className={`p-2 rounded-lg transition-colors ${
              canSave && hasChanges
                ? 'text-red-900 hover:bg-red-50'
                : 'text-neutral-400 cursor-not-allowed'
            }`}
          >
            <Text
              variant="b2"
              className={
                canSave && hasChanges ? 'text-red-900' : 'text-neutral-400'
              }
            >
              {isLoading ? '저장 중...' : '완료'}
            </Text>
          </button>
        </div>

        {/* 콘텐츠 영역 */}
        <div className="flex-1 px-8 py-6 space-y-6 overflow-y-auto">
          {/* 프로필 이미지 섹션 */}
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              {/* 스피너 링 (이미지 위에 오버레이) */}
              {isUploadingImage && (
                <div className="absolute inset-0 border-4 border-red-200 border-t-red-900 rounded-full animate-spin" />
              )}

              <Image
                src={profileImage}
                alt="프로필 이미지"
                width={80}
                height={80}
                className={cx(
                  'max-w-20 max-h-20 rounded-full ring-neutral-200 ring-1 transition-opacity',
                  isUploadingImage ? 'opacity-70' : 'opacity-100'
                )}
                priority
              />

              {/* 카메라 버튼 */}
              <button
                onClick={handleImageSelect}
                disabled={isUploadingImage || isLoading}
                className="absolute bottom-0 right-0 w-8 h-8 bg-neutral-0 rounded-full flex items-center justify-center ring-1 ring-neutral-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="프로필 이미지 변경"
              >
                <Icon.camera size={18} className="text-white" />
              </button>
            </div>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* 닉네임 섹션 */}
          <div className="space-y-2">
            <Text variant="s2" className="text-neutral-700">
              닉네임
            </Text>
            <Input
              value={nickname}
              onChange={handleNicknameChange}
              placeholder="전설의 투자자 이름을 넣어 주세요"
              disabled={isLoading || isUploadingImage}
              className={`${!validation.isValid ? 'ring-red-500' : ''}`}
            />

            {/* Validation 에러 메시지 */}
            {!validation.isValid && validation.message && (
              <Text variant="b3" className="text-red-900 px-1">
                {validation.message}
              </Text>
            )}
          </div>

          {/* 현재 이메일 표시 (읽기 전용) */}
          <div className="space-y-2">
            <Text variant="s2" className="text-neutral-700">
              아이디
            </Text>
            <Input value={user.email} disabled />
          </div>
        </div>
      </div>
    </Modal>
  );
}
