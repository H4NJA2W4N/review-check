import React, { useState, useEffect } from "react";
import {
  Search,
  User,
  LogOut,
  Info,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  FileText,
  Database,
  Cpu,
  Download,
  Calendar,
  ChevronRight,
  Send,
  ArrowLeft,
  X,
  Edit,
  Trash2,
  Plus,
  Home,
  LayoutDashboard,
} from "lucide-react";

// ===== API 설정 =====
const API_BASE_URL = "http://localhost:8000";

/**
 * Review Check 시스템 - 버그 수정 버전
 */
export default function App() {
  // --- 기본 상태 관리 ---
  const [currentPage, setCurrentPage] = useState("home");
  const [isAdmin, setIsAdmin] = useState(false);
  const [toast, setToast] = useState({
    show: false,
    message: "",
    type: "info",
  });
  const [selectedNoticeId, setSelectedNoticeId] = useState(null);

  // --- 분석 관련 (urlInput 제거 - HomeScreen 내부로 이동) ---
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  // --- 모달 ---
  const [showInfoModal, setShowInfoModal] = useState(false);

  // --- 대시보드 관련 ---
  const [dateRange, setDateRange] = useState({ start: "", end: "" });

  // --- 페이지 로드 시 토큰 확인 ---
  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    if (token) {
      setIsAdmin(true);
    }
  }, []);

  // --- 커스텀 아이콘 ---
  const ReviewCheckIcon = ({ className }) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
      <path d="m9 11 3 3L22 4" />
    </svg>
  );

  // --- 기능 함수 ---
  const showToast = (message, type = "info") => {
    setToast({ show: true, message, type });
  };

  useEffect(() => {
    if (toast.show) {
      const timer = setTimeout(() => {
        setToast({ ...toast, show: false });
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [toast.show]);

  const navigateTo = (page, noticeId = null) => {
    setCurrentPage(page);
    if (noticeId) setSelectedNoticeId(noticeId);
    window.scrollTo(0, 0);
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    const username = e.target.elements[0].value;
    const password = e.target.elements[1].value;

    try {
      const response = await fetch(`${API_BASE_URL}/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success && data.token) {
        localStorage.setItem("admin_token", data.token);
        localStorage.setItem("admin_username", username);
        setIsAdmin(true);
        navigateTo("adminDashboard");
        showToast("로그인에 성공했습니다!", "success");
      } else {
        showToast(data.message || "로그인에 실패했습니다.", "error");
      }
    } catch (error) {
      console.error("로그인 오류:", error);
      showToast("서버 연결에 실패했습니다.", "error");
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem("admin_token");
    const username = localStorage.getItem("admin_username");

    if (token && username) {
      try {
        await fetch(`${API_BASE_URL}/admin/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ request_user: username }),
        });
      } catch (error) {
        console.error("로그아웃 오류:", error);
      }
    }

    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_username");
    setIsAdmin(false);
    navigateTo("home");
    showToast("로그아웃 되었습니다.", "info");
  };

  const handleDownload = () => {
    if (!dateRange.start || !dateRange.end) {
      showToast("날짜 범위를 먼저 설정해주세요.", "error");
      return;
    }
    showToast(
      `[${dateRange.start} ~ ${dateRange.end}] 기간의 리뷰 분석 데이터를 다운로드합니다.`,
      "success"
    );
  };

  const getScoreInfo = (score) => {
    if (score >= 76)
      return {
        color: "text-green-600",
        bg: "bg-green-100",
        border: "border-green-500",
        label: "매우 도움됨",
      };
    if (score >= 36)
      return {
        color: "text-orange-500",
        bg: "bg-orange-100",
        border: "border-orange-400",
        label: "일부 도움됨",
      };
    return {
      color: "text-red-500",
      bg: "bg-red-100",
      border: "border-red-500",
      label: "도움 안 됨",
    };
  };

  // --- 컴포넌트 ---

  // Toast Notification
  const ToastNotification = () => {
    if (!toast.show) return null;

    let classes = "";
    let Icon = Info;
    let iconColor = "";

    switch (toast.type) {
      case "success":
        classes = "bg-green-600 border-green-700";
        Icon = ThumbsUp;
        iconColor = "text-green-100";
        break;
      case "error":
        classes = "bg-red-600 border-red-700";
        Icon = X;
        iconColor = "text-red-100";
        break;
      case "info":
      default:
        classes = "bg-blue-600 border-blue-700";
        Icon = Info;
        iconColor = "text-blue-100";
        break;
    }

    return (
      <div
        className={`fixed bottom-6 left-1/2 transform -translate-x-1/2 z-[200] p-4 rounded-xl shadow-2xl transition-all duration-300 ${classes} flex items-center gap-3`}
        style={{ animation: "toastIn 0.3s ease-out forwards" }}
      >
        <Icon size={20} className={iconColor} />
        <span className="text-white font-medium text-sm">{toast.message}</span>
        <button
          onClick={() => setToast({ ...toast, show: false })}
          className="text-white/70 hover:text-white ml-2"
        >
          <X size={16} />
        </button>
      </div>
    );
  };

  // Navbar
  const Navbar = () => (
    <nav className="w-full fixed top-0 left-0 z-50 bg-white/80 backdrop-blur-md border-b border-blue-100 h-16 flex items-center justify-between px-6 lg:px-12 shadow-sm transition-all">
      <div
        className="flex items-center gap-2 cursor-pointer group"
        onClick={() => navigateTo("home")}
      >
        <ReviewCheckIcon className="w-6 h-6 text-blue-600 group-hover:text-blue-700 transition-colors" />
        <span className="text-lg font-extrabold text-slate-800 tracking-tight group-hover:text-blue-900 transition-colors">
          Review Check
        </span>
      </div>

      <div className="flex items-center gap-6 font-medium text-slate-600 text-sm">
        <button
          onClick={() => navigateTo("notice")}
          className="hover:text-blue-600 transition-colors"
        >
          공지사항
        </button>
        <button
          onClick={() => navigateTo("inquiry")}
          className="hover:text-blue-600 transition-colors"
        >
          문의
        </button>
        {isAdmin && (
          <button
            onClick={() => navigateTo("adminDashboard")}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 transition-colors font-bold"
          >
            <LayoutDashboard size={16} /> 대시보드
          </button>
        )}
        {isAdmin ? (
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 text-red-500 hover:text-red-700 font-bold"
          >
            <LogOut size={16} /> 로그아웃
          </button>
        ) : (
          <button
            onClick={() => navigateTo("adminLogin")}
            className="flex items-center gap-1 hover:text-blue-600 transition-colors"
          >
            <User size={16} /> 관리자
          </button>
        )}
      </div>
    </nav>
  );

  // HomeScreen
  const HomeScreen = () => {
    // ⭐ URL 입력 상태를 HomeScreen 내부로 이동!
    const [urlInput, setUrlInput] = React.useState("");

    // ⭐ handleAnalyze도 HomeScreen 내부로
    const handleAnalyze = () => {
      if (!urlInput.trim()) {
        showToast("URL을 입력해주세요.", "error");
        return;
      }

      setIsAnalyzing(true);
      showToast("분석을 시작합니다...", "info");

      setTimeout(() => {
        const mockScore = Math.floor(Math.random() * 100);
        setAnalysisResult({
          url: urlInput, // ⭐ URL 저장
          score: mockScore,
          productName: "베이직 오버핏 코튼 셔츠",
          summary:
            "대부분의 리뷰가 긍정적이나, 배송 관련 불만이 일부 감지되었습니다. 패턴 분석 결과 조작된 리뷰 비율은 낮습니다.",
          details: [
            { label: "실구매자 비율", value: "92%" },
            { label: "리뷰 긍정률", value: "85%" },
            { label: "언어 패턴 일치도", value: "High" },
          ],
        });
        setIsAnalyzing(false);
        showToast("분석이 완료되었습니다!", "success");
        navigateTo("result");
      }, 1500);
    };

    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-4 pt-16 bg-gradient-to-br from-blue-50 via-white to-blue-50">
        <div className="w-full max-w-3xl flex flex-col items-center animate-fade-in-up">
          <div className="flex flex-col items-center mb-8">
            <ReviewCheckIcon className="w-20 h-20 text-blue-600 mb-4 drop-shadow-md" />
            <h1 className="text-5xl font-extrabold text-slate-800 tracking-tight mb-2">
              Review Check
            </h1>
            <p className="text-slate-500 text-lg font-medium">
              쇼핑몰 리뷰 신뢰도 분석 시스템
            </p>

            {isAdmin && (
              <button
                onClick={() => navigateTo("adminDashboard")}
                className="mt-4 flex items-center gap-2 px-6 py-3 bg-slate-800 text-white rounded-xl font-bold hover:bg-slate-900 shadow-lg transition-all"
              >
                <LayoutDashboard size={18} />
                관리자 대시보드로 이동
              </button>
            )}
          </div>

          <div className="w-full bg-white p-2 rounded-2xl shadow-xl border border-blue-100 relative overflow-hidden group hover:shadow-2xl transition-shadow duration-300">
            <div className="relative flex items-center p-2">
              <div className="absolute left-6 text-slate-400 group-focus-within:text-blue-500 transition-colors">
                <Search size={24} />
              </div>
              <input
                type="text"
                placeholder=""
                className="w-full pl-14 pr-36 py-5 bg-transparent rounded-xl focus:outline-none text-lg text-slate-700 placeholder-slate-400"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
              />
              <div
                className={`absolute left-16 transition-all duration-300 pointer-events-none ${
                  urlInput ? "-top-2 opacity-0" : "top-5 text-slate-400"
                }`}
              >
                <span className="text-sm md:text-base">
                  분석하고 싶은 쇼핑몰 상품 페이지 URL을 입력하세요
                </span>
              </div>

              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="absolute right-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3 rounded-xl font-bold shadow-md transition-all transform hover:scale-105 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? "분석중..." : "분석하기"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ResultScreen
  const ResultScreen = () => {
    if (!analysisResult) return null;
    const { score, color, bg, border, label } = {
      ...analysisResult,
      ...getScoreInfo(analysisResult.score),
    };

    return (
      <div className="flex flex-col items-center min-h-screen px-4 pt-28 pb-12 bg-slate-50">
        <div className="w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden animate-fade-in">
          <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-800">
                분석 결과 리포트
              </h2>
              <button
                onClick={() => setShowInfoModal(true)}
                className="text-slate-400 hover:text-blue-600 transition-colors"
                title="점수 기준 보기"
              >
                <Info size={18} />
              </button>
            </div>
            <button
              onClick={() => navigateTo("home")}
              className="text-blue-600 text-sm font-semibold hover:underline"
            >
              새로운 분석하기
            </button>
          </div>
          <div className="px-8 py-2 bg-slate-50/50 border-b border-slate-100 text-slate-500 text-sm truncate">
            {analysisResult.url || ""}
          </div>

          <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-10">
            <div className="flex flex-col items-center justify-center space-y-6">
              <div
                className={`w-48 h-48 rounded-full flex items-center justify-center border-8 ${border} ${bg} transition-all duration-500`}
              >
                <div className="text-center">
                  <span className={`text-5xl font-extrabold ${color}`}>
                    {score}
                  </span>
                  <span className="text-slate-400 text-lg">/100</span>
                </div>
              </div>

              <div
                className={`px-4 py-2 rounded-full font-bold text-lg ${bg} ${color}`}
              >
                {label}
              </div>

              <p className="text-center text-slate-600 leading-relaxed px-4">
                {analysisResult.summary}
              </p>
            </div>

            <div className="flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="font-bold text-slate-700 mb-4">
                  세부 분석 지표
                </h3>
                {analysisResult.details.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between items-center p-4 bg-slate-50 rounded-xl border border-slate-100"
                  >
                    <span className="text-slate-600 font-medium">
                      {item.label}
                    </span>
                    <span className="text-slate-800 font-bold">
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-8 border-t border-slate-100 pt-6">
                <p className="text-center text-slate-500 text-sm mb-4">
                  이 분석 결과가 도움이 되셨나요?
                </p>
                <div className="flex justify-center gap-4">
                  <button className="flex items-center gap-2 px-6 py-3 bg-white border border-slate-200 rounded-xl text-slate-600 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-all shadow-sm">
                    <ThumbsUp size={18} />
                    <span>네, 도움됨</span>
                  </button>
                  <button className="flex items-center gap-2 px-6 py-3 bg-white border border-slate-200 rounded-xl text-slate-600 hover:border-red-500 hover:text-red-500 hover:bg-red-50 transition-all shadow-sm">
                    <ThumbsDown size={18} />
                    <span>아니요</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // InfoModal
  const InfoModal = () => {
    if (!showInfoModal) return null;
    return (
      <div
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        onClick={() => setShowInfoModal(false)}
      >
        <div
          className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-slate-800">
              신뢰도 점수 기준
            </h3>
            <button
              onClick={() => setShowInfoModal(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              ✕
            </button>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
              <div className="w-3 h-3 mt-1.5 rounded-full bg-red-500 shrink-0"></div>
              <div>
                <span className="block font-bold text-red-700">0% ~ 35%</span>
                <span className="text-sm text-red-600">
                  상품 구매에 도움이 되지 않는 리뷰가 많습니다.
                </span>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg border border-orange-100">
              <div className="w-3 h-3 mt-1.5 rounded-full bg-orange-500 shrink-0"></div>
              <div>
                <span className="block font-bold text-orange-700">
                  36% ~ 75%
                </span>
                <span className="text-sm text-orange-600">
                  상품 구매에 도움이 되는 정보가 일부 포함되어 있습니다.
                </span>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-100">
              <div className="w-3 h-3 mt-1.5 rounded-full bg-green-500 shrink-0"></div>
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
  };

  // NoticeScreen
  const NoticeScreen = () => {
    const [notices, setNotices] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [showForm, setShowForm] = React.useState(false);
    const [formData, setFormData] = React.useState({ title: "", content: "" });

    React.useEffect(() => {
      fetchNotices();
    }, []);

    const fetchNotices = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${API_BASE_URL}/user/notices?page=1&size=20`
        );
        const data = await response.json();

        if (data.success) {
          setNotices(data.items);
        }
      } catch (error) {
        console.error("공지사항 조회 오류:", error);
        showToast("공지사항을 불러오는데 실패했습니다.", "error");
      } finally {
        setLoading(false);
      }
    };

    const createNotice = async () => {
      if (!formData.title || !formData.content) {
        showToast("제목과 내용을 입력해주세요.", "error");
        return;
      }

      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(`${API_BASE_URL}/admin/notices`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: formData.title,
            content: formData.content,
            attachments: [],
          }),
        });

        const data = await response.json();
        if (data.success) {
          showToast("공지사항이 등록되었습니다.", "success");
          setShowForm(false);
          setFormData({ title: "", content: "" });
          fetchNotices();
        } else {
          showToast(data.message || "등록에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("공지사항 생성 오류:", error);
        showToast("서버 연결에 실패했습니다.", "error");
      }
    };

    const deleteNotice = async (noticeId) => {
      if (!window.confirm("정말 삭제하시겠습니까?")) return;

      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/notices/${noticeId}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const data = await response.json();
        if (data.success) {
          showToast("공지사항이 삭제되었습니다.", "success");
          fetchNotices();
        } else {
          showToast(data.message || "삭제에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("공지사항 삭제 오류:", error);
        showToast("서버 연결에 실패했습니다.", "error");
      }
    };

    return (
      <div className="flex flex-col items-center min-h-screen px-4 pt-24 bg-slate-50">
        <div className="w-full max-w-3xl animate-fade-in">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigateTo("home")}
                className="p-2 hover:bg-white rounded-full transition-colors"
              >
                <ArrowLeft className="text-slate-600" />
              </button>
              <h2 className="text-3xl font-extrabold text-slate-800">
                공지사항
              </h2>
            </div>

            {isAdmin && (
              <button
                onClick={() => setShowForm(!showForm)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-colors"
              >
                {showForm ? <X size={18} /> : <Plus size={18} />}
                {showForm ? "취소" : "글쓰기"}
              </button>
            )}
          </div>

          {isAdmin && showForm && (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-6">
              <input
                type="text"
                placeholder="제목"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-3 focus:outline-none focus:border-blue-500"
              />
              <textarea
                placeholder="내용"
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                rows={5}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-3 focus:outline-none focus:border-blue-500 resize-none"
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setShowForm(false);
                    setFormData({ title: "", content: "" });
                  }}
                  className="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200"
                >
                  취소
                </button>
                <button
                  onClick={createNotice}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  등록
                </button>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-slate-500">로딩 중...</div>
            ) : notices.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                등록된 공지사항이 없습니다.
              </div>
            ) : (
              notices.map((notice) => (
                <div
                  key={notice.notice_id}
                  className="p-6 border-b border-slate-100 hover:bg-slate-50 transition-colors group"
                >
                  <div className="flex justify-between items-start">
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() =>
                        navigateTo("noticeDetail", notice.notice_id)
                      }
                    >
                      <h3 className="font-bold text-slate-800 text-lg mb-1 group-hover:text-blue-600 transition-colors">
                        {notice.title}
                      </h3>
                      <p className="text-slate-500 text-sm mb-2">
                        {notice.content.substring(0, 80)}...
                      </p>
                      <p className="text-slate-400 text-xs">
                        {new Date(notice.created_at).toLocaleDateString(
                          "ko-KR"
                        )}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {isAdmin && (
                        <>
                          <button
                            onClick={() =>
                              navigateTo("noticeDetail", notice.notice_id)
                            }
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="수정"
                          >
                            <Edit size={18} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteNotice(notice.notice_id);
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="삭제"
                          >
                            <Trash2 size={18} />
                          </button>
                        </>
                      )}
                      {!isAdmin && (
                        <ChevronRight className="text-slate-300 group-hover:text-blue-500" />
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  };

  // NoticeDetailScreen
  const NoticeDetailScreen = () => {
    const [notice, setNotice] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [isEditing, setIsEditing] = React.useState(false);
    const [editForm, setEditForm] = React.useState({ title: "", content: "" });

    React.useEffect(() => {
      if (selectedNoticeId) {
        fetchNoticeDetail();
      }
    }, [selectedNoticeId]);

    const fetchNoticeDetail = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${API_BASE_URL}/user/notices/${selectedNoticeId}`
        );
        const data = await response.json();

        if (data.success && data.notice) {
          setNotice(data.notice);
          setEditForm({
            title: data.notice.title,
            content: data.notice.content,
          });
        }
      } catch (error) {
        console.error("공지사항 조회 오류:", error);
        showToast("공지사항을 불러오는데 실패했습니다.", "error");
      } finally {
        setLoading(false);
      }
    };

    const updateNotice = async () => {
      if (!editForm.title || !editForm.content) {
        showToast("제목과 내용을 입력해주세요.", "error");
        return;
      }

      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/notices/${selectedNoticeId}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              title: editForm.title,
              content: editForm.content,
            }),
          }
        );

        const data = await response.json();
        if (data.success) {
          showToast("공지사항이 수정되었습니다.", "success");
          setIsEditing(false);
          fetchNoticeDetail();
        } else {
          showToast(data.message || "수정에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("공지사항 수정 오류:", error);
        showToast("서버 연결에 실패했습니다.", "error");
      }
    };

    const deleteNotice = async () => {
      if (!window.confirm("정말 삭제하시겠습니까?")) return;

      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/notices/${selectedNoticeId}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const data = await response.json();
        if (data.success) {
          showToast("공지사항이 삭제되었습니다.", "success");
          navigateTo("notice");
        } else {
          showToast(data.message || "삭제에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("공지사항 삭제 오류:", error);
        showToast("서버 연결에 실패했습니다.", "error");
      }
    };

    if (loading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-slate-500">로딩 중...</div>
        </div>
      );
    }

    if (!notice) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-slate-500">공지사항을 찾을 수 없습니다.</div>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center min-h-screen px-4 pt-24 pb-12 bg-slate-50">
        <div className="w-full max-w-3xl animate-fade-in">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigateTo("notice")}
                className="p-2 hover:bg-white rounded-full transition-colors"
              >
                <ArrowLeft className="text-slate-600" />
              </button>
              <h2 className="text-2xl font-extrabold text-slate-800">
                공지사항
              </h2>
            </div>

            {isAdmin && !isEditing && (
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700"
                >
                  <Edit size={18} /> 수정
                </button>
                <button
                  onClick={deleteNotice}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg font-bold hover:bg-red-700"
                >
                  <Trash2 size={18} /> 삭제
                </button>
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            {isEditing ? (
              <div className="p-8">
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) =>
                    setEditForm({ ...editForm, title: e.target.value })
                  }
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-4 text-xl font-bold focus:outline-none focus:border-blue-500"
                />
                <textarea
                  value={editForm.content}
                  onChange={(e) =>
                    setEditForm({ ...editForm, content: e.target.value })
                  }
                  rows={15}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-4 focus:outline-none focus:border-blue-500 resize-none"
                />
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditForm({
                        title: notice.title,
                        content: notice.content,
                      });
                    }}
                    className="px-6 py-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 font-bold"
                  >
                    취소
                  </button>
                  <button
                    onClick={updateNotice}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold"
                  >
                    저장
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-8">
                <div className="border-b border-slate-100 pb-6 mb-6">
                  <h1 className="text-2xl font-bold text-slate-800 mb-3">
                    {notice.title}
                  </h1>
                  <div className="flex items-center gap-4 text-sm text-slate-500">
                    <span>
                      작성일:{" "}
                      {new Date(notice.created_at).toLocaleDateString("ko-KR")}
                    </span>
                    <span>•</span>
                    <span>
                      수정일:{" "}
                      {new Date(notice.updated_at).toLocaleDateString("ko-KR")}
                    </span>
                  </div>
                </div>
                <div className="prose max-w-none">
                  <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {notice.content}
                  </p>
                </div>
                {notice.attachments && notice.attachments.length > 0 && (
                  <div className="mt-8 pt-6 border-t border-slate-100">
                    <h3 className="font-bold text-slate-700 mb-3">첨부파일</h3>
                    <div className="space-y-2">
                      {notice.attachments.map((att) => (
                        <a
                          key={att.attachment_id}
                          href={att.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                          <FileText size={18} className="text-slate-500" />
                          <span className="text-slate-700">
                            {att.file_name}
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // InquiryScreen (상태를 내부로 이동!)
  const InquiryScreen = () => {
    // ⭐ 상태를 컴포넌트 내부로 이동
    const [inquiryEmail, setInquiryEmail] = React.useState("");
    const [inquiryType, setInquiryType] = React.useState("분석 결과 문의");
    const [inquiryTitle, setInquiryTitle] = React.useState("");
    const [inquiryContent, setInquiryContent] = React.useState("");
    const [isInquirySubmitting, setIsInquirySubmitting] = React.useState(false);

    const handleInquirySubmit = async (e) => {
      e.preventDefault();
      if (isInquirySubmitting) return;

      if (
        !inquiryEmail.trim() ||
        !inquiryTitle.trim() ||
        !inquiryContent.trim()
      ) {
        showToast("이메일, 제목, 내용을 모두 입력해주세요.", "error");
        return;
      }

      try {
        setIsInquirySubmitting(true);

        const response = await fetch(`${API_BASE_URL}/user/inquiry`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: inquiryEmail,
            title: inquiryTitle,
            content: `[${inquiryType}]\n\n${inquiryContent.trim()}`,
          }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
          showToast("문의가 성공적으로 접수되었습니다.", "success");

          // 폼 초기화
          setInquiryEmail("");
          setInquiryType("분석 결과 문의");
          setInquiryTitle("");
          setInquiryContent("");

          navigateTo("home");
        } else {
          showToast(data.message || "문의 접수에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("문의 등록 오류:", error);
        showToast("서버와 통신 중 오류가 발생했습니다.", "error");
      } finally {
        setIsInquirySubmitting(false);
      }
    };

    return (
      <div className="flex flex-col items-center min-h-screen px-4 pt-24 bg-slate-50">
        <div className="w-full max-w-2xl animate-fade-in">
          <div className="flex items-center gap-4 mb-8">
            <button
              onClick={() => navigateTo("home")}
              className="p-2 hover:bg-white rounded-full transition-colors"
            >
              <ArrowLeft className="text-slate-600" />
            </button>
            <h2 className="text-3xl font-extrabold text-slate-800">문의하기</h2>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-100">
            <p className="text-slate-500 mb-6">
              서비스 이용 중 불편한 점이나 궁금한 점을 남겨주세요.
              <br />
              담당자가 확인 후 빠르게 답변 드리겠습니다.
            </p>

            <form className="space-y-6" onSubmit={handleInquirySubmit}>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  이메일 주소
                </label>
                <input
                  type="email"
                  placeholder="답변 받을 이메일을 입력하세요"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                  required
                  value={inquiryEmail}
                  onChange={(e) => setInquiryEmail(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  문의 유형
                </label>
                <select
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                  value={inquiryType}
                  onChange={(e) => setInquiryType(e.target.value)}
                >
                  <option>분석 결과 문의</option>
                  <option>서비스 오류 신고</option>
                  <option>제휴 및 기타 문의</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  제목
                </label>
                <input
                  type="text"
                  placeholder="문의 제목을 입력하세요"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                  required
                  value={inquiryTitle}
                  onChange={(e) => setInquiryTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  내용
                </label>
                <textarea
                  placeholder="문의 내용을 상세히 적어주세요"
                  rows={5}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors resize-none"
                  required
                  value={inquiryContent}
                  onChange={(e) => setInquiryContent(e.target.value)}
                />
              </div>

              <button
                type="submit"
                disabled={isInquirySubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isInquirySubmitting ? (
                  "접수 중..."
                ) : (
                  <>
                    <Send size={18} /> 문의 접수하기
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  };

  // AdminLoginScreen
  const AdminLoginScreen = () => (
    <div className="flex items-center justify-center min-h-screen px-4 bg-slate-50">
      <div className="bg-white p-10 rounded-3xl shadow-xl border border-blue-50 w-full max-w-md">
        <h2 className="text-2xl font-extrabold text-center text-slate-800 mb-2">
          관리자 로그인
        </h2>
        <p className="text-center text-slate-500 mb-8 text-sm">
          시스템 관리를 위해 로그인해주세요.
        </p>

        <form onSubmit={handleAdminLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              아이디
            </label>
            <input
              type="text"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="admin"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              비밀번호
            </label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="••••••"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-slate-800 text-white py-3 rounded-lg font-bold hover:bg-slate-900 transition-colors mt-4"
          >
            접속하기
          </button>
        </form>
        <div className="mt-6 text-center">
          <button
            onClick={() => navigateTo("home")}
            className="text-sm text-slate-400 hover:text-slate-600"
          >
            ← 메인으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );

  // AdminDashboardScreen
  const AdminDashboardScreen = () => {
    const [activeTab, setActiveTab] = useState("notice");
    const [notices, setNotices] = React.useState([]);
    const [showNoticeForm, setShowNoticeForm] = React.useState(false);
    const [editingNotice, setEditingNotice] = React.useState(null);
    const [noticeForm, setNoticeForm] = React.useState({
      title: "",
      content: "",
    });

    // ⭐ 문의 관련 상태들
    const [inquiries, setInquiries] = React.useState([]);
    const [inquiryLoading, setInquiryLoading] = React.useState(false);
    const [inquiryStatus, setInquiryStatus] = React.useState("all");
    const [inquirySearch, setInquirySearch] = React.useState("");
    const [inquiryTotal, setInquiryTotal] = React.useState(0);
    const [selectedInquiry, setSelectedInquiry] = React.useState(null);
    const [replyContent, setReplyContent] = React.useState("");
    const [isReplySaving, setIsReplySaving] = React.useState(false);

    const tabs = [
      { id: "notice", label: "공지사항 관리", icon: <FileText size={18} /> },
      {
        id: "inquiry",
        label: "사용자 문의 관리",
        icon: <MessageSquare size={18} />,
      },
      { id: "data", label: "데이터 관리", icon: <Database size={18} /> },
      { id: "aimodel", label: "AI 모델 재학습", icon: <Cpu size={18} /> },
    ];

    // 공지사항 관련 함수들
    const fetchNotices = async () => {
      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/notices?page=1&size=20`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        const data = await response.json();
        if (data.success) {
          setNotices(data.items);
        }
      } catch (error) {
        console.error("공지사항 조회 오류:", error);
        showToast("공지사항을 불러오는데 실패했습니다.", "error");
      }
    };

    const createOrUpdateNotice = async () => {
      if (!noticeForm.title || !noticeForm.content) {
        showToast("제목과 내용을 입력해주세요.", "error");
        return;
      }

      try {
        const token = localStorage.getItem("admin_token");
        const isEditing = editingNotice !== null;
        const url = isEditing
          ? `${API_BASE_URL}/admin/notices/${editingNotice.notice_id}`
          : `${API_BASE_URL}/admin/notices`;
        const method = isEditing ? "PUT" : "POST";

        const response = await fetch(url, {
          method,
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: noticeForm.title,
            content: noticeForm.content,
            attachments: [],
          }),
        });

        const data = await response.json();
        if (data.success) {
          showToast(
            isEditing
              ? "공지사항이 수정되었습니다."
              : "공지사항이 등록되었습니다.",
            "success"
          );
          setShowNoticeForm(false);
          setEditingNotice(null);
          setNoticeForm({ title: "", content: "" });
          fetchNotices();
        } else {
          showToast(data.message || "처리에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("공지사항 처리 오류:", error);
        showToast("서버 연결에 실패했습니다.", "error");
      }
    };

    const startEdit = (notice) => {
      setEditingNotice(notice);
      setNoticeForm({ title: notice.title, content: notice.content });
      setShowNoticeForm(true);
    };

    const cancelEdit = () => {
      setShowNoticeForm(false);
      setEditingNotice(null);
      setNoticeForm({ title: "", content: "" });
    };

    const deleteNotice = async (noticeId) => {
      if (!window.confirm("정말 삭제하시겠습니까?")) return;

      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/notices/${noticeId}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const data = await response.json();
        if (data.success) {
          showToast("공지사항이 삭제되었습니다.", "success");
          fetchNotices();
        } else {
          showToast(data.message || "삭제에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("공지사항 삭제 오류:", error);
        showToast("서버 연결에 실패했습니다.", "error");
      }
    };

    // ⭐ 문의 관련 함수들
    const fetchInquiries = async () => {
      try {
        setInquiryLoading(true);
        const token = localStorage.getItem("admin_token");

        let url = `${API_BASE_URL}/admin/inquiries?page=1&size=20`;
        if (inquiryStatus !== "all") {
          url += `&status=${inquiryStatus}`;
        }
        if (inquirySearch.trim()) {
          url += `&q=${encodeURIComponent(inquirySearch)}`;
        }

        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();

        if (data.success) {
          setInquiries(data.items || []);
          setInquiryTotal(data.total || 0);
        }
      } catch (error) {
        console.error("문의 목록 조회 오류:", error);
        showToast("문의 목록을 불러오는데 실패했습니다.", "error");
      } finally {
        setInquiryLoading(false);
      }
    };

    const openInquiryDetail = async (inquiryId) => {
      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/inquiries/${inquiryId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        const data = await response.json();

        if (data.success && data.inquiry) {
          setSelectedInquiry(data.inquiry);
          setReplyContent(data.inquiry.reply ? data.inquiry.reply.content : "");
        }
      } catch (error) {
        console.error("문의 상세 조회 오류:", error);
        showToast("문의 상세 정보를 불러오는데 실패했습니다.", "error");
      }
    };

    const saveReply = async () => {
      if (!selectedInquiry) return;
      if (!replyContent.trim()) {
        showToast("답변 내용을 입력해주세요.", "error");
        return;
      }

      try {
        setIsReplySaving(true);
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/inquiries/${selectedInquiry.inquiry_id}/reply`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              content: replyContent,
            }),
          }
        );
        const data = await response.json();

        if (response.ok && data.success && data.inquiry) {
          setSelectedInquiry(data.inquiry);
          setReplyContent(data.inquiry.reply ? data.inquiry.reply.content : "");
          showToast("답변이 저장되었습니다.", "success");
          // ⭐ fetchInquiries()를 await 없이 호출
          fetchInquiries();
        } else {
          showToast(data.message || "답변 저장에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("답변 저장 오류:", error);
        showToast("답변 저장 중 오류가 발생했습니다.", "error");
      } finally {
        setIsReplySaving(false);
      }
    };

    const deleteReply = async () => {
      if (!selectedInquiry) return;
      if (!window.confirm("답변을 삭제하시겠습니까?")) return;

      try {
        const token = localStorage.getItem("admin_token");
        const response = await fetch(
          `${API_BASE_URL}/admin/inquiries/${selectedInquiry.inquiry_id}/reply`,
          {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const data = await response.json();

        if (response.ok && data.success && data.inquiry) {
          setSelectedInquiry(data.inquiry);
          setReplyContent("");
          showToast("답변이 삭제되었습니다.", "success");
          fetchInquiries();
        } else {
          showToast(data.message || "답변 삭제에 실패했습니다.", "error");
        }
      } catch (error) {
        console.error("답변 삭제 오류:", error);
        showToast("답변 삭제 중 오류가 발생했습니다.", "error");
      }
    };

    // ⭐ 탭 변경 추적
    const prevTabRef = React.useRef(activeTab);

    React.useEffect(() => {
      const prevTab = prevTabRef.current;

      if (activeTab === "notice") {
        fetchNotices();
      } else if (activeTab === "inquiry") {
        // ⭐ 다른 탭에서 inquiry로 변경될 때만 초기화
        if (prevTab !== "inquiry") {
          setSelectedInquiry(null);
          setReplyContent("");
        }
        fetchInquiries();
      }

      // 현재 탭을 이전 탭으로 저장
      prevTabRef.current = activeTab;
    }, [activeTab]);

    const renderContent = () => {
      switch (activeTab) {
        case "notice":
          return (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-slate-800">
                  등록된 공지사항
                </h3>
                <button
                  onClick={() => {
                    if (showNoticeForm && !editingNotice) {
                      setShowNoticeForm(false);
                    } else {
                      setShowNoticeForm(true);
                      setEditingNotice(null);
                      setNoticeForm({ title: "", content: "" });
                    }
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-700"
                >
                  {showNoticeForm && !editingNotice ? "취소" : "+ 글쓰기"}
                </button>
              </div>

              {showNoticeForm && (
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-4">
                  <h4 className="font-bold text-slate-800 mb-4">
                    {editingNotice ? "공지사항 수정" : "새 공지사항 작성"}
                  </h4>
                  <input
                    type="text"
                    placeholder="제목"
                    value={noticeForm.title}
                    onChange={(e) =>
                      setNoticeForm({ ...noticeForm, title: e.target.value })
                    }
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-3 focus:outline-none focus:border-blue-500"
                  />
                  <textarea
                    placeholder="내용"
                    value={noticeForm.content}
                    onChange={(e) =>
                      setNoticeForm({ ...noticeForm, content: e.target.value })
                    }
                    rows={5}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-3 focus:outline-none focus:border-blue-500 resize-none"
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={cancelEdit}
                      className="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200"
                    >
                      취소
                    </button>
                    <button
                      onClick={createOrUpdateNotice}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      {editingNotice ? "수정" : "등록"}
                    </button>
                  </div>
                </div>
              )}

              {notices.length === 0 ? (
                <div className="bg-white rounded-xl border border-slate-100 p-6 text-center text-slate-500">
                  등록된 공지사항이 없습니다.
                </div>
              ) : (
                <div className="space-y-2">
                  {notices.map((notice) => (
                    <div
                      key={notice.notice_id}
                      className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex justify-between items-start"
                    >
                      <div className="flex-1">
                        <div className="font-bold text-slate-800 mb-1">
                          {notice.title}
                        </div>
                        <div className="text-sm text-slate-500 mb-2">
                          {notice.content.substring(0, 100)}...
                        </div>
                        <div className="text-xs text-slate-400">
                          {new Date(notice.created_at).toLocaleDateString(
                            "ko-KR"
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => startEdit(notice)}
                          className="px-3 py-1.5 bg-blue-50 text-blue-600 text-sm rounded-lg hover:bg-blue-100"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => deleteNotice(notice.notice_id)}
                          className="px-3 py-1.5 bg-red-50 text-red-600 text-sm rounded-lg hover:bg-red-100"
                        >
                          삭제
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );

        case "inquiry":
          return (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 왼쪽: 문의 목록 */}
              <div className="lg:col-span-1 space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xl font-bold text-slate-800">
                    사용자 문의 목록
                  </h3>
                  <button
                    onClick={fetchInquiries}
                    className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
                  >
                    새로고침
                  </button>
                </div>

                <div className="flex gap-2 mb-3">
                  <select
                    className="flex-1 px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg"
                    value={inquiryStatus}
                    onChange={(e) => setInquiryStatus(e.target.value)}
                  >
                    <option value="all">전체</option>
                    <option value="pending">대기 중</option>
                    <option value="done">답변 완료</option>
                  </select>
                  <input
                    type="text"
                    placeholder="제목/내용 검색"
                    className="flex-[2] px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg"
                    value={inquirySearch}
                    onChange={(e) => setInquirySearch(e.target.value)}
                  />
                  <button
                    onClick={fetchInquiries}
                    className="px-5 py-3 text-sm bg-blue-600 text-white rounded-lg whitespace-nowrap min-w-[64px] flex items-center justify-center"
                  >
                    검색
                  </button>
                </div>

                <div className="bg-white rounded-xl border border-slate-100 shadow-sm max-h-[480px] overflow-y-auto">
                  {inquiryLoading ? (
                    <div className="p-4 text-sm text-slate-500">
                      문의 목록을 불러오는 중입니다...
                    </div>
                  ) : inquiries.length === 0 ? (
                    <div className="p-4 text-sm text-slate-500">
                      등록된 문의가 없습니다.
                    </div>
                  ) : (
                    inquiries.map((inq) => (
                      <button
                        key={inq.inquiry_id}
                        onClick={() => openInquiryDetail(inq.inquiry_id)}
                        className={`w-full text-left px-4 py-3 border-b last:border-b-0 border-slate-100 hover:bg-slate-50 transition-colors ${
                          selectedInquiry &&
                          selectedInquiry.inquiry_id === inq.inquiry_id
                            ? "bg-blue-50"
                            : ""
                        }`}
                      >
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-semibold text-sm text-slate-800">
                            {inq.title}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              inq.status === "done"
                                ? "bg-green-100 text-green-700"
                                : "bg-yellow-100 text-yellow-700"
                            }`}
                          >
                            {inq.status === "done" ? "답변 완료" : "대기 중"}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 flex justify-between">
                          <span>{inq.user_id}</span>
                          <span>
                            {new Date(inq.created_at).toLocaleString("ko-KR")}
                          </span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  총 {inquiryTotal}건
                </div>
              </div>

              {/* 오른쪽: 문의 상세 + 답변 */}
              <div className="lg:col-span-2 flex items-start mt-25">
                {selectedInquiry ? (
                  <div className="w-full bg-white rounded-xl border border-slate-100 shadow-sm p-6 space-y-4">
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <div className="text-xs text-slate-400 mb-1">
                          {selectedInquiry.user_id}
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">
                          {selectedInquiry.title}
                        </h3>
                        <div className="text-xs text-slate-400">
                          작성일:{" "}
                          {new Date(selectedInquiry.created_at).toLocaleString(
                            "ko-KR"
                          )}
                        </div>
                      </div>
                      <span
                        className={`text-xs px-3 py-1 rounded-full ${
                          selectedInquiry.status === "done"
                            ? "bg-green-100 text-green-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {selectedInquiry.status === "done"
                          ? "답변 완료"
                          : "대기 중"}
                      </span>
                    </div>

                    <div className="p-4 bg-slate-50 rounded-lg text-sm text-slate-700 whitespace-pre-wrap">
                      {selectedInquiry.content}
                    </div>

                    <div className="border-t border-slate-100 pt-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-700">
                          관리자 답변
                        </span>
                        {selectedInquiry.reply && (
                          <span className="text-xs text-slate-400">
                            마지막 수정:{" "}
                            {new Date(
                              selectedInquiry.reply.updated_at
                            ).toLocaleString("ko-KR")}
                          </span>
                        )}
                      </div>

                      <textarea
                        rows={5}
                        className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 resize-none"
                        placeholder="사용자에게 보낼 답변 내용을 입력하세요."
                        value={replyContent}
                        onChange={(e) => setReplyContent(e.target.value)}
                      />

                      <div className="flex justify-end gap-2">
                        {selectedInquiry.reply && (
                          <button
                            type="button"
                            onClick={deleteReply}
                            className="px-4 py-2 text-sm rounded-lg bg-red-50 text-red-600 hover:bg-red-100"
                          >
                            답변 삭제
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={saveReply}
                          disabled={isReplySaving}
                          className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300"
                        >
                          {isReplySaving
                            ? "저장 중..."
                            : selectedInquiry.reply
                            ? "답변 수정"
                            : "답변 등록"}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="w-full bg-white rounded-xl border border-slate-100 shadow-sm p-6 text-center text-slate-500">
                    왼쪽에서 문의를 선택해주세요.
                  </div>
                )}
              </div>
            </div>
          );

        case "data":
          return (
            <div className="space-y-6">
              <h3 className="text-xl font-bold text-slate-800 mb-4">
                데이터 추출 및 관리
              </h3>

              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <Calendar className="text-blue-600" size={20} />
                  <span className="font-bold text-slate-700">
                    날짜 구간 설정
                  </span>
                </div>
                <div className="flex flex-col md:flex-row gap-4 items-end md:items-center">
                  <div className="flex-1 w-full">
                    <label className="block text-xs font-semibold text-slate-500 mb-1">
                      시작일
                    </label>
                    <input
                      type="date"
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-700 focus:border-blue-500 outline-none"
                      value={dateRange.start}
                      onChange={(e) =>
                        setDateRange({ ...dateRange, start: e.target.value })
                      }
                    />
                  </div>
                  <span className="text-slate-400 hidden md:block">~</span>
                  <div className="flex-1 w-full">
                    <label className="block text-xs font-semibold text-slate-500 mb-1">
                      종료일
                    </label>
                    <input
                      type="date"
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-700 focus:border-blue-500 outline-none"
                      value={dateRange.end}
                      onChange={(e) =>
                        setDateRange({ ...dateRange, end: e.target.value })
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm hover:border-blue-200 transition-colors">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-bold text-slate-700 text-lg mb-1">
                      리뷰 분석 데이터 로그
                    </div>
                    <p className="text-sm text-slate-500">
                      선택한 기간 내의 URL별 신뢰도 분석 결과 기록 (.csv)
                    </p>
                  </div>
                  <button
                    onClick={handleDownload}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow-md transition-all transform active:scale-95"
                  >
                    <Download size={18} /> 데이터 다운로드
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
                  <div className="text-blue-600 text-sm font-semibold mb-1">
                    총 누적 분석
                  </div>
                  <div className="text-3xl font-extrabold text-blue-800">
                    12,450 건
                  </div>
                </div>
                <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-100">
                  <div className="text-indigo-600 text-sm font-semibold mb-1">
                    오늘 분석 요청
                  </div>
                  <div className="text-3xl font-extrabold text-indigo-800">
                    142 건
                  </div>
                </div>
              </div>
            </div>
          );

        case "aimodel":
          return (
            <div className="space-y-6">
              <h3 className="text-xl font-bold text-slate-800">AI 모델 관리</h3>
              <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <div className="font-bold text-slate-800 text-lg">
                      Model V2.4
                    </div>
                    <div className="text-green-500 text-sm font-medium">
                      ● 가동 중 (정확도 94.2%)
                    </div>
                  </div>
                  <button className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 shadow-md">
                    재학습 시작
                  </button>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2.5 mb-2">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full"
                    style={{ width: "100%" }}
                  ></div>
                </div>
                <div className="text-xs text-slate-400 text-right">
                  마지막 업데이트: 2023.10.20
                </div>
              </div>
            </div>
          );
        default:
          return null;
      }
    };

    return (
      <div className="flex min-h-screen bg-slate-50 pt-16">
        <aside className="w-64 bg-white border-r border-slate-200 fixed h-full hidden md:block">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Dashboard
              </h2>
              <button
                onClick={() => navigateTo("home")}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                title="메인화면"
              >
                <Home size={18} className="text-slate-600" />
              </button>
            </div>
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    activeTab === tab.id
                      ? "bg-blue-50 text-blue-600 font-bold shadow-sm"
                      : "text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </aside>

        <main className="flex-1 md:ml-64 p-8">
          <header className="mb-8 flex justify-between items-center">
            <h1 className="text-2xl font-extrabold text-slate-800">
              관리자 대시보드
            </h1>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigateTo("home")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
              >
                <Home size={18} />
                메인화면
              </button>
              <div className="text-sm text-slate-500">
                Admin 님, 환영합니다.
              </div>
            </div>
          </header>

          <div className="animate-fade-in">{renderContent()}</div>
        </main>
      </div>
    );
  };

  return (
    <div className="min-h-screen font-sans bg-slate-50 text-slate-800">
      {currentPage !== "adminDashboard" && <Navbar />}

      {currentPage === "home" && <HomeScreen />}
      {currentPage === "result" && <ResultScreen />}
      {currentPage === "notice" && <NoticeScreen />}
      {currentPage === "noticeDetail" && <NoticeDetailScreen />}
      {currentPage === "inquiry" && <InquiryScreen />}
      {currentPage === "adminLogin" && <AdminLoginScreen />}
      {currentPage === "adminDashboard" && <AdminDashboardScreen />}

      <InfoModal />
      <ToastNotification />

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes toastIn {
          from { opacity: 0; transform: translate(-50%, 20px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }
        .animate-fade-in-up { animation: fadeInUp 0.8s ease-out forwards; }
        .animate-fade-in { animation: fadeInUp 0.5s ease-out forwards; }
        .animate-scale-in { animation: scaleIn 0.3s ease-out forwards; }
      `}</style>
    </div>
  );
}
