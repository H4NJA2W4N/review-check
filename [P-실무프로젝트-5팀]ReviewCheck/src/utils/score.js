// src/utils/score.js

/**
 * 신뢰도 점수에 따른 상태 정보 반환
 */
export function getScoreInfo(score) {
  if (score >= 76) {
    return {
      color: 'text-green-600',
      bg: 'bg-green-100',
      border: 'border-green-500',
      label: '매우 도움됨',
    };
  }
  if (score >= 36) {
    return {
      color: 'text-orange-500',
      bg: 'bg-orange-100',
      border: 'border-orange-400',
      label: '부분적으로 도움됨',
    };
  }
  return {
    color: 'text-red-500',
    bg: 'bg-red-100',
    border: 'border-red-500',
    label: '도움 안 됨',
  };
}