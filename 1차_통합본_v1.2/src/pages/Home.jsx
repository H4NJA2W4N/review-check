// src/pages/Home.jsx
import React from 'react';
import { Search, LayoutDashboard } from 'lucide-react';
import ReviewCheckIcon from '../components/icons/ReviewCheckIcon';

export default function Home({
  urlInput,
  setUrlInput,
  isAnalyzing,
  onAnalyze,
  onGoToAdmin,   // ✅ 오타 수정: onGoToADmin → onGoToAdmin
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 pt-16 bg-gradient-to-br from-blue-200 via-white to-blue-200">
      <div className="w-full max-w-4xl flex justify-end mb-4">
        {onGoToAdmin && (
          <button
            onClick={onGoToAdmin}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs md:text-sm text-slate-600 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LayoutDashboard size={16} />
            관리자 대시보드로 돌아가기
          </button>
        )}
      </div>

      <div className="w-full max-w-4xl flex flex-col items-center animate-fade-in-up">
        {/* 로고 + 타이틀 영역 */}
        <div className="flex flex-col items-center mb-10">
          <ReviewCheckIcon className="w-24 h-24 text-blue-600 mb-5 drop-shadow-md" />
          <h1 className="text-5xl md:text-7xl font-extrabold text-slate-800 tracking-tight mb-3">
            Review Check
          </h1>
          <p className="text-lg md:text-2xl text-slate-500 font-medium">
            패션 쇼핑 플랫폼 리뷰 신뢰도 분석 시스템
          </p>
        </div>

        {/* 검색 카드 */}
        <div className="w-full bg-white p-3 md:p-4 rounded-3xl shadow-xl border border-blue-100 relative overflow-hidden group hover:shadow-2xl transition-shadow duration-300">
          <div className="relative flex items-center py-1 md:py-2">
            {/* 돋보기 아이콘 */}
            <div className="absolute left-6 text-slate-400 group-focus-within:text-blue-500 transition-colors">
              <Search size={26} />
            </div>

            {/* URL 입력창 */}
            <input
              type="text"
              className="w-full pl-16 pr-40 py-6 bg-transparent rounded-2xl focus:outline-none text-xl md:text-2xl text-slate-700 placeholder-slate-400"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onAnalyze()}
            />

            {/* 플로팅 플레이스홀더 */}
            <div
              className={`absolute left-16 transition-all duration-300 pointer-events-none ${
                urlInput
                  ? 'opacity-0 -translate-y-2'
                  : 'opacity-100 top-1/2 -translate-y-1/2 text-slate-400'
              }`}
            >
              <span className="text-base md:text-lg">
                분석하고 싶은 쇼핑몰 상품 페이지 URL을 입력하세요
              </span>
            </div>

            {/* 분석하기 버튼 */}
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="absolute right-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-10 py-4 rounded-2xl text-lg md:text-xl font-bold shadow-md transition-all transform hover:scale-105 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? '분석중...' : '분석하기'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}