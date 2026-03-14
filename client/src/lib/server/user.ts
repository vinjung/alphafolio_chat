import { db } from './db';
import { users } from '@schema';
import { User, NewUser } from './models';
import { and, eq, isNull, isNotNull } from 'drizzle-orm';

/**
 * 데이터베이스에 새로운 사용자를 생성합니다.
 *
 * @param data - 생성할 사용자 정보 객체
 * @param data.oauthProvider - OAuth 제공자 이름 (예: "google", "github")
 * @param data.oauthId - OAuth 제공자로부터 받은 고유 ID
 * @param data.email - 사용자의 이메일 주소
 * @param data.nickname - 사용자의 닉네임/표시 이름
 * @param data.profileImageUrl - 사용자의 프로필 이미지 URL
 * @param data.thumbnailImageUrl - 사용자의 프로필 이미지 썸네일 URL
 * @param data.phoneNumber - 사용자의 전화번호 (선택 필드)
 * @returns 새로 생성된 사용자 객체
 * @throws 사용자 생성 실패 시 Error 발생
 */
export async function createUser(data: NewUser): Promise<User> {
  const [user] = await db
    .insert(users)
    .values({
      ...data,
    })
    .returning();

  if (user == null) {
    throw new Error('Unexpected error: user was not created');
  }

  return user;
}

/**
 * OAuth ID와 제공자를 기반으로 활성 사용자를 조회합니다.
 * ✅ 삭제된 사용자(deleted_at이 NULL이 아닌 경우)는 제외됩니다.
 *
 * @param oauthId - OAuth 제공자로부터 받은 고유 ID
 * @param oauthProvider - OAuth 제공자 이름 (예: "google", "github")
 * @returns 활성 사용자를 찾으면 사용자 객체, 없으면 null
 */
export async function getUserFromOauthId(
  oauthId: string,
  oauthProvider: string
): Promise<User | null> {
  const [user] = await db
    .select()
    .from(users)
    .where(
      and(
        eq(users.oauthProvider, oauthProvider),
        eq(users.oauthId, oauthId),
        isNull(users.deletedAt) // ✅ 삭제되지 않은 사용자만 조회
      )
    );

  return user ?? null;
}

/**
 * 이메일을 기반으로 활성 사용자를 조회합니다.
 * ✅ 삭제된 사용자는 제외됩니다.
 *
 * @param email - 사용자 이메일
 * @returns 활성 사용자를 찾으면 사용자 객체, 없으면 null
 */
export async function getUserFromEmail(email: string): Promise<User | null> {
  const [user] = await db
    .select()
    .from(users)
    .where(
      and(
        eq(users.email, email),
        isNull(users.deletedAt) // ✅ 삭제되지 않은 사용자만 조회
      )
    );

  return user ?? null;
}

/**
 * 탈퇴된 사용자를 확인합니다.
 * 재가입 방지를 위해 삭제된 사용자 정보를 조회합니다.
 *
 * @param oauthId - OAuth 제공자로부터 받은 고유 ID
 * @param oauthProvider - OAuth 제공자 이름
 * @returns 탈퇴된 사용자를 찾으면 사용자 객체, 없으면 null
 */
export async function getDeletedUserFromOauthId(
  oauthId: string,
  oauthProvider: string
): Promise<User | null> {
  const [user] = await db
    .select()
    .from(users)
    .where(
      and(
        eq(users.oauthProvider, oauthProvider),
        eq(users.oauthId, oauthId),
        isNotNull(users.deletedAt) // ✅ 삭제된 사용자만 조회
      )
    );

  return user ?? null;
}

/**
 * 이메일을 기반으로 탈퇴된 사용자를 확인합니다.
 *
 * @param email - 사용자 이메일
 * @returns 탈퇴된 사용자를 찾으면 사용자 객체, 없으면 null
 */
export async function getDeletedUserFromEmail(
  email: string
): Promise<User | null> {
  const [user] = await db
    .select()
    .from(users)
    .where(
      and(
        eq(users.email, email),
        isNotNull(users.deletedAt) // ✅ 삭제된 사용자만 조회
      )
    );

  return user ?? null;
}

/**
 * 사용자를 소프트 삭제합니다.
 * ✅ 실제 데이터는 삭제하지 않고 deleted_at 타임스탬프만 설정합니다.
 *
 * @param userId - 삭제할 사용자 UUID
 * @returns 삭제 처리된 사용자 객체
 */
export async function softDeleteUser(userId: string): Promise<User> {
  const [deletedUser] = await db
    .update(users)
    .set({
      deletedAt: new Date(),
      updatedAt: new Date(),
    })
    .where(eq(users.id, userId))
    .returning();

  if (!deletedUser) {
    throw new Error('User not found or already deleted');
  }

  return deletedUser;
}

/**
 * 사용자를 하드 삭제합니다. (기존 함수 유지)
 * ⚠️ 응급 상황이나 GDPR 요청 시에만 사용하세요.
 *
 * @param userId - 삭제할 사용자 UUID
 */
export async function deleteUser(userId: string): Promise<void> {
  await db.delete(users).where(eq(users.id, userId));
}
