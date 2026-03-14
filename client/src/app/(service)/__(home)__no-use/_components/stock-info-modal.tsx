'use client';

import React from 'react';
import { Text } from '@/components/shared/text';
import { Modal } from '@/components/shared/modal';

interface StockInfoModalProps {
  isVisible: boolean;
  onCloseAction: () => void;
}

export function StockInfoModal({
  isVisible,
  onCloseAction,
}: StockInfoModalProps) {
  return (
    <Modal
      isVisible={isVisible}
      onCloseAction={onCloseAction}
      title="미래가격전망이란?"
      variant="center"
      size="md"
    >
      {/* 콘텐츠 - 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <Text variant="b1">
          미래가격전망은 12개월 후 예상되는 주가입니다. <br /> 다양한 시장
          요소의 AI 분석을 통해 산출합니다.
        </Text>
        {/* 신뢰 방식 */}
        <div>
          <Text variant="b1" className="font-bold">
            📊 미래가격전망 산출 방식
          </Text>
          <ul className="list-disc pl-8">
            <Text variant="b1" as="li">
              주식 분석: 주가 차트의 추세와 패턴을 분석
            </Text>
            <Text variant="b1" as="li">
              투자심리 분석: 뉴스, 소셜미디어, 투자자 심리를 분석
            </Text>
            <Text variant="b1" as="li">
              시장 환경: 업종 동향, 거시경제 지표를 반영
            </Text>
            <Text variant="b1" as="li">
              AI 예측: 수집 가치 데이터 포인트를 학습한 AI 모델의 예측
            </Text>
          </ul>
        </div>
        {/* 해석하기 */}
        <div>
          <Text variant="b1" className="font-bold">
            📋 미래가격전망 해석하기
          </Text>
          <ul className="list-disc pl-8">
            <Text variant="b1" as="li">
              상승/하락 확률: 해당 가격대에 도달할 확률
            </Text>
            <Text variant="b1" as="li">
              변동성 범위: 예상 가격의 상하한 범위
            </Text>
            <Text variant="b1" as="li">
              주요 변수: 가격에 큰 영향을 줄 수 있는 핵심 요소
            </Text>
          </ul>
        </div>
        {/* 참고사항 */}
        <div>
          <Text variant="b1" className="font-bold">
            참고사항
          </Text>
          <ul className="list-disc pl-8">
            <Text variant="b1" as="li">
              모든 예측은 확률에 기반하여 100% 정확하지 않을 수 있습니다.
            </Text>
            <Text variant="b1" as="li">
              급격한 시장 변화나 예상치 못한 이벤트는 예측에 반영되지 않을 수
              있습니다.
            </Text>
            <Text variant="b1" as="li">
              투자 결정은 다양한 정보를 종합적으로 고려하여 시기 바랍니다.
            </Text>
          </ul>
        </div>
      </div>
    </Modal>
  );
}
