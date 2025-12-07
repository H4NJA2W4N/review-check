import React, { useState, useEffect } from "react";

import Navbar from "./components/layout/Navbar";
import ToastNotification from "./components/feedback/ToastNotification";
import InfoModal from "./components/feedback/InfoModal";

import Home from "./pages/Home";
import Result from "./pages/Result";
import Notice from "./pages/Notice";
import Inquiry from "./pages/Inquiry";
import AdminLogin from "./pages/AdminLogin";
import AdminDashboard from "./pages/AdminDashboard";
import NoticeDetail from "./pages/NoticeDetail";
import { api } from "./utils/api";
import { setAdminToken } from "./utils/api";

export default function App() {
  // --------------------------------------------------
  // 페이지 & 관리자 상태
  // --------------------------------------------------
  const [currentPage, setCurrentPage] = useState("home");
  const [adminInfo, setAdminInfo] = useState(null);
  const isAdmin = !!adminInfo;

  // --------------------------------------------------
  // 공통 상태
  // --------------------------------------------------
  const [urlInput, setUrlInput] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showInfoModal, setShowInfoModal] = useState(false);

  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [analysisResult, setAnalysisResult] = useState(null);

  const [toast, setToast] = useState({
    show: false,
    message: "",
    type: "info",
  });
  const [selectedNoticeId, setSelectedNoticeId] = useState(null);

  const showToast = (message, type = "info") => {
    setToast({ show: true, message, type });
  };

  useEffect(() => {
    if (!toast.show) return;
    const timer = setTimeout(
      () => setToast((prev) => ({ ...prev, show: false })),
      3000
    );
    return () => clearTimeout(timer);
  }, [toast.show]);

  const navigateTo = (page, noticeId) => {
    setCurrentPage(page);
    if (noticeId) setSelectedNoticeId(noticeId);
    window.scrollTo(0, 0);
  };

  // --------------------------------------------------
  // 분석 버튼 (백엔드 API 연동)
  // --------------------------------------------------
  const handleAnalyze = async () => {
    if (!urlInput.trim()) {
      showToast("URL을 입력해주세요.", "error");
      return;
    }

    setIsAnalyzing(true);
    showToast("분석을 시작합니다...", "info");

    try {
      const res = await api.post("/users/analyses", {
        review_url: urlInput.trim(),
      });

      const data = res.data;

      if (!data.success) {
        setIsAnalyzing(false);
        showToast(data.message || "분석 요청 실패", "error");
        return;
      }

      const analysisId = data.analysis_id;
      showToast("분석 중입니다...", "info");

      // 폴링 시작
      let attempts = 0;
      const maxAttempts = 30;

      const poll = async () => {
        if (attempts >= maxAttempts) {
          setIsAnalyzing(false);
          showToast("분석 시간이 초과되었습니다.", "error");
          return;
        }

        const result = await api.get(`/users/analyses/${analysisId}`);
        const resultData = result.data;

        if (resultData.status === "completed") {
          // ✅ [수정됨] 백엔드 데이터를 가공 없이 그대로 저장합니다.
          // Result.jsx가 원본 키 이름(review_count 등)을 기대하기 때문입니다.
          setAnalysisResult(resultData);

          setIsAnalyzing(false);
          showToast("분석이 완료되었습니다!", "success");
          navigateTo("result");
        } else {
          attempts++;
          setTimeout(poll, 2000);
        }
      };

      setTimeout(poll, 2000);
    } catch (err) {
      console.error("분석 요청 오류:", err);
      showToast("서버 연결 실패", "error");
      setIsAnalyzing(false);
    }
  };

  // --------------------------------------------------
  // 관리자 로그인 / 로그아웃
  // --------------------------------------------------
  const handleAdminLoginSuccess = (info) => {
    setAdminInfo(info);
    setAdminToken(info.token);
    navigateTo("adminDashboard");
    showToast("관리자 모드로 접속했습니다.", "success");
  };

  const handleLogout = () => {
    setAdminInfo(null);
    setAdminToken(null);
    navigateTo("home");
    showToast("로그아웃 되었습니다.", "info");
  };

  // --------------------------------------------------
  // 데이터 다운로드
  // --------------------------------------------------
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

  const handleInquirySubmitted = () => {
    showToast("문의가 성공적으로 접수되었습니다.", "success");
    navigateTo("home");
  };

  const handleLogoClick = () => {
    setUrlInput("");
    navigateTo("home");
  };

  // --------------------------------------------------
  // 렌더링
  // --------------------------------------------------
  return (
    <div className="min-h-screen font-sans bg-slate-50 text-slate-800">
      {currentPage !== "adminDashboard" && (
        <Navbar
          isAdmin={isAdmin}
          onNavigate={navigateTo}
          onLogout={handleLogout}
          onLogoClick={handleLogoClick}
        />
      )}

      {currentPage === "home" && (
        <Home
          urlInput={urlInput}
          setUrlInput={setUrlInput}
          isAnalyzing={isAnalyzing}
          onAnalyze={handleAnalyze}
        />
      )}

      {/* ✅ [수정됨] Result 컴포넌트에 props를 올바르게 전달합니다 */}
      {currentPage === "result" && (
        <Result
          result={analysisResult} // analysisResult -> result 이름 변경
          showToast={showToast}
          onBack={() => navigateTo("home")} // onNewAnalyze -> onBack 이름 변경
        />
      )}

      {currentPage === "notice" && (
        <Notice
          isAdmin={isAdmin}
          navigateTo={navigateTo}
          showToast={showToast}
        />
      )}

      {currentPage === "noticeDetail" && (
        <NoticeDetail
          selectedNoticeId={selectedNoticeId}
          isAdmin={isAdmin}
          navigateTo={navigateTo}
          showToast={showToast}
        />
      )}

      {currentPage === "inquiry" && (
        <Inquiry
          onBack={() => navigateTo("home")}
          onSubmitted={handleInquirySubmitted}
        />
      )}

      {currentPage === "adminLogin" && (
        <AdminLogin
          onLoginSuccess={handleAdminLoginSuccess}
          onBack={() => navigateTo("home")}
        />
      )}

      {currentPage === "adminDashboard" && (
        <AdminDashboard
          dateRange={dateRange}
          showToast={showToast}
          setDateRange={setDateRange}
          onDownload={handleDownload}
          onGoToHome={() => navigateTo("home")}
          adminInfo={adminInfo}
          onLogout={handleLogout}
        />
      )}

      <InfoModal open={showInfoModal} onClose={() => setShowInfoModal(false)} />
      <ToastNotification
        toast={toast}
        onClose={() => setToast((prev) => ({ ...prev, show: false }))}
      />

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
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up { animation: fadeInUp 0.8s ease-out forwards; }
        .animate-fade-in { animation: fadeInUp 0.5s ease-out forwards; }
        .animate-scale-in { animation: scaleIn 0.3s ease-out forwards; }
        .animate-toast-in { animation: toastIn 0.3s ease-out forwards; }
      `}</style>
    </div>
  );
}
