// src/components/layout/Navbar.jsx
import React from "react";
import { User, LogOut, LayoutDashboard } from "lucide-react";
import ReviewCheckIcon from "../icons/ReviewCheckIcon";

export default function Navbar({ isAdmin, onNavigate, onLogout, onLogoClick }) {
  return (
    <nav className="w-full fixed top-0 left-0 z-50 bg-white/80 backdrop-blur-md border-b border-blue-100 h-16 flex items-center justify-between px-6 lg:px-12 shadow-sm transition-all">
      <div
        className="flex items-center gap-2 cursor-pointer group"
        onClick={onLogoClick}
      >
        <ReviewCheckIcon className="w-6 h-6 text-blue-600 group-hover:text-blue-700 transition-colors" />
        <span className="text-lg font-extrabold text-slate-800 tracking-tight group-hover:text-blue-900 transition-colors">
          Review Check
        </span>
      </div>

      <div className="flex items-center gap-6 font-medium text-slate-600 text-sm">
        <button
          onClick={() => onNavigate("notice")}
          className="hover:text-blue-600 transition-colors"
        >
          공지사항
        </button>
        <button
          onClick={() => onNavigate("inquiry")}
          className="hover:text-blue-600 transition-colors"
        >
          문의
        </button>
        {isAdmin && (
          <button
            onClick={() => onNavigate("adminDashboard")}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 transition-colors font-bold"
          >
            <LayoutDashboard size={16} /> 대시보드
          </button>
        )}
        {isAdmin ? (
          <button
            onClick={onLogout}
            className="flex items-center gap-1 text-red-500 hover:text-red-700 font-bold"
          >
            <LogOut size={16} /> 로그아웃
          </button>
        ) : (
          <button
            onClick={() => onNavigate("adminLogin")}
            className="flex items-center gap-1 hover:text-blue-600 transition-colors"
          >
            <User size={16} /> 관리자
          </button>
        )}
      </div>
    </nav>
  );
}
