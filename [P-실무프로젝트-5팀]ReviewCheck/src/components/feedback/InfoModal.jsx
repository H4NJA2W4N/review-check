// src/components/feedback/InfoModal.jsx
import React from "react";

export default function InfoModal({ open, onClose }) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-slate-800">신뢰도 점수 기준</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            ✕
          </button>
        </div>

        {/* 빨간 박스 */}
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
            <div className="w-3 h-3 mt-1.5 rounded-full bg-red-500 shrink-0" />
            <div>
              <span className="block font-bold text-red-700">0% ~ 35%</span>
              <span className="text-sm text-red-600">
                상품 구매에 도움이 되지 않는 리뷰가 많습니다.
              </span>
            </div>
          </div>

          {/* 주황 박스 */}
          <div className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg border border-orange-100">
            <div className="w-3 h-3 mt-1.5 rounded-full bg-orange-500 shrink-0" />
            <div>
              <span className="block font-bold text-orange-700">
                36% ~ 75%
              </span>
              <span className="text-sm text-orange-600">
                상품 구매에 도움이 되는 정보가 일부 포함되어 있습니다.
              </span>
            </div>
          </div>

          {/* 초록 박스 */}
          <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-100">
            <div className="w-3 h-3 mt-1.5 rounded-full bg-green-500 shrink-0" />
            <div>
              <span className="block font-bold text-green-700">
                76% ~ 100%
              </span>
              <span className="text-sm text-green-600">
                상품 구매에 실질적인 도움을 주는 신뢰할 수 있는 리뷰입니다.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
