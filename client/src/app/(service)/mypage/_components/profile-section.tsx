'use client';

import Image from 'next/image';
import { Text } from '@/components/shared/text';
import type { User } from '@/lib/server/models';
import { Button } from '@/components/shared/button';
import { ProfileEditModal } from './profile-edit-modal';
import { useState } from 'react';

interface ProfileSectionProps {
  user: User;
}

export function ProfileSection({ user }: ProfileSectionProps) {
  const [showEditModal, setShowEditModal] = useState(false);

  const profileImage = user.profileImageUrl || '/images/default-profile.webp';

  return (
    <>
      <div className="p-4 flex items-center gap-4">
        <Image
          src={profileImage}
          alt="프로필 이미지"
          width={64}
          height={64}
          className="rounded-full border-1 border-neutral-200 max-w-16 max-h-16"
          priority
        />
        <div className="flex flex-col">
          <Text variant="s1" className="text-neutral-1100">
            {user.nickname || '사용자'}
          </Text>
          <Text variant="b3" className="text-neutral-600">
            {user.email}
          </Text>
        </div>

        <Button
          variant="outline"
          className="ml-auto rounded-lg ripple-effect"
          onClick={() => setShowEditModal(true)}
        >
          <Text variant="s2" className="text-neutral-900">
            프로필 편집
          </Text>
        </Button>
      </div>

      <ProfileEditModal
        isVisible={showEditModal}
        onCloseAction={() => setShowEditModal(false)}
        user={user}
      />
    </>
  );
}
