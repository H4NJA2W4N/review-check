// src/pages/AdminDashboard.jsx
import React, { useEffect, useState } from "react";
import DataManage from "./DataManage";
import {
  MessageSquare,
  FileText,
  Database,
  Cpu,
  Calendar,
  Download,
  LogOut,
  Trash2,
  PlusCircle,
  Send,
} from "lucide-react";
import { api } from "../utils/api";

export default function AdminDashboard({
  dateRange = { start: "2023-01-01", end: "2023-12-31" }, // 기본값 설정
  showToast,
  setDateRange = () => {},
  onDownload = () => {},
  onGoToHome = () => {},
  adminInfo,
  onLogout,
}) {
  const [activeTab, setActiveTab] = useState("inquiry");
  const [aiStats, setAiStats] = useState({
    total_jobs: 0,
    pending_jobs: 0,
    completed_jobs: 0,
    total_feedbacks: 0,
    active_model: null,
  });
  const [aiLoading, setAiLoading] = useState(false);
  const [retraining, setRetraining] = useState(false);

  // 문의 / 공지 상태들
  const [inquiries, setInquiries] = useState([]);
  const [inqLoading, setInqLoading] = useState(false);
  const [inquirySearch, setInquirySearch] = React.useState("");
  const [selectedInquiry, setSelectedInquiry] = useState(null);
  const [inquiryStatus, setInquiryStatus] = React.useState("all");
  const [inquiryTotal, setInquiryTotal] = React.useState(0);
  // 답변 입력을 위한 상태 추가 (각 문의 ID별 텍스트 저장)
  const [replyTexts, setReplyTexts] = useState({});
  const [isReplySaving, setIsReplySaving] = useState(false);

  const [notices, setNotices] = useState([]);
  const [noticeLoading, setNoticeLoading] = useState(false);

  const [noticeFormOpen, setNoticeFormOpen] = useState(false);
  const [noticeTitle, setNoticeTitle] = useState("");
  const [noticeContent, setNoticeContent] = useState("");
  const [noticeSaving, setNoticeSaving] = useState(false);

  const [isEditing, setIsEditing] = useState(false);
  const [editingNoticeId, setEditingNoticeId] = useState(null);
  // 탭 바뀔 때마다 해당 데이터 로딩
  useEffect(() => {
    if (activeTab === "inquiry") {
      fetchInquiries();
    } else if (activeTab === "notice") {
      fetchNotices();
    } else if (activeTab === "aimodel") {
      fetchAIStats();
    }
  }, [activeTab]);

  const fetchInquiries = async () => {
    try {
      setInqLoading(true);

      const params = {
        page: 1,
        size: 20,
      };

      if (inquiryStatus !== "all") params.status = inquiryStatus;
      if (inquirySearch.trim()) params.q = inquirySearch.trim();

      const res = await api.get("/admin/inquiries", { params });

      if (res.data.success) {
        setInquiries(res.data.items || []);
        setInquiryTotal(res.data.total || 0);
      }
    } catch (err) {
      console.error("문의 목록 조회 오류:", err);
      showToast("문의 목록을 불러오는데 실패했습니다.", "error");
    } finally {
      setInqLoading(false);
    }
  };

  const openInquiryDetail = async (inquiryId) => {
    try {
      const res = await api.get(`/admin/inquiries/${inquiryId}`);

      if (res.data.success && res.data.inquiry) {
        setSelectedInquiry(res.data.inquiry);
        setReplyTexts(res.data.inquiry.reply?.content || "");
      }
    } catch (err) {
      console.error("문의 상세 조회 오류:", err);
      showToast("문의 상세 정보를 불러오는데 실패했습니다.", "error");
    }
  };

  const fetchNotices = async () => {
    setNoticeLoading(true);
    try {
      const res = await api.get("/admin/notices", {
        params: { page: 1, size: 20 },
      });
      setNotices(res.data.items || []);
    } catch (err) {
      console.error("공지 목록 불러오기 실패:", err);
    } finally {
      setNoticeLoading(false);
    }
  };

  const fetchAIStats = async () => {
    try {
      setAiLoading(true);
      const res = await api.get("/admin/ai/stats");
      if (res.data.success) {
        setAiStats(res.data);
      }
    } catch (err) {
      console.error("AI 통계 조회 오류:", err);
      showToast("AI 모델 정보를 불러오는데 실패했습니다.", "error");
    } finally {
      setAiLoading(false);
    }
  };

  const handleRetrain = async () => {
    if (
      !window.confirm(
        "AI 모델 재학습을 요청하시겠습니까?\n\n피드백 데이터를 사용하여 모델을 개선합니다."
      )
    ) {
      return;
    }

    try {
      setRetraining(true);
      const res = await api.post("/admin/ai/retrain", {
        description: "관리자 수동 재학습 요청",
      });

      if (res.data.success) {
        showToast(res.data.message, "success");
        fetchAIStats();
      } else {
        showToast(res.data.message || "재학습 요청 실패", "error");
      }
    } catch (err) {
      console.error("재학습 요청 오류:", err);
      const msg =
        err.response?.data?.detail || "재학습 요청 중 오류가 발생했습니다.";
      showToast(msg, "error");
    } finally {
      setRetraining(false);
    }
  };

  const saveReply = async () => {
    if (!selectedInquiry) return;
    if (!replyTexts.trim()) {
      showToast("답변 내용을 입력해주세요.", "error");
      return;
    }

    try {
      setIsReplySaving(true);

      const res = await api.post(
        `/admin/inquiries/${selectedInquiry.inquiry_id}/reply`,
        { content: replyTexts }
      );

      if (res.data.success && res.data.inquiry) {
        setSelectedInquiry(res.data.inquiry);
        setReplyTexts(res.data.inquiry.reply?.content || "");
        showToast("답변이 저장되었습니다.", "success");

        // UI 즉시 반영
        fetchInquiries();
      } else {
        showToast(res.data.message || "답변 저장에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("답변 저장 오류:", err);
      showToast("답변 저장 중 오류가 발생했습니다.", "error");
    } finally {
      setIsReplySaving(false);
    }
  };

  const deleteReply = async () => {
    if (!selectedInquiry) return;
    if (!window.confirm("답변을 삭제하시겠습니까?")) return;

    try {
      const res = await api.delete(
        `/admin/inquiries/${selectedInquiry.inquiry_id}/reply`
      );

      if (res.data.success && res.data.inquiry) {
        setSelectedInquiry(res.data.inquiry);
        setReplyTexts("");
        showToast("답변이 삭제되었습니다.", "success");

        fetchInquiries();
      } else {
        showToast(res.data.message || "답변 삭제에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("답변 삭제 오류:", err);
      showToast("답변 삭제 중 오류가 발생했습니다.", "error");
    }
  };

  // 공지 생성
  const handleCreateNotice = async (e) => {
    if (!noticeTitle.trim() || !noticeContent.trim()) return;
    setNoticeSaving(true);
    try {
      const res = await api.post("/admin/notices", {
        title: noticeTitle,
        content: noticeContent,
      });
      if (res.data.success) {
        showToast("공지사항이 등록되었습니다.", "success");
        setNoticeTitle("");
        setNoticeContent("");
        setNoticeFormOpen(false);
        await fetchNotices();
      } else {
        alert(res.data.message || "공지 생성에 실패했습니다.");
      }
    } catch (err) {
      console.error("공지 생성 실패:", err);
      alert("공지 생성 중 오류가 발생했습니다.");
    } finally {
      setNoticeSaving(false);
    }
  };

  const handleupdateNotice = async () => {
    if (!noticeTitle.trim() || !noticeContent.trim()) {
      showToast("제목과 내용을 입력해주세요.", "error");
      return;
    }

    if (!editingNoticeId) {
      showToast("수정할 공지 정보가 없습니다.", "error");
      return;
    }

    try {
      setNoticeSaving(true);

      const res = await api.put(`/admin/notices/${editingNoticeId}`, {
        title: noticeTitle,
        content: noticeContent,
        attachments: [],
      });

      if (res.data.success) {
        showToast("공지사항이 수정되었습니다.", "success");

        // 수정 종료
        setEditingNoticeId(null);
        setNoticeTitle("");
        setNoticeContent("");
        setNoticeFormOpen(false);

        // 목록 새로고침
        fetchNotices();
      } else {
        showToast(res.data.message || "수정에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("공지 수정 오류:", err);
      showToast("서버 연결에 실패했습니다.", "error");
    } finally {
      setNoticeSaving(false);
    }
  };

  // 공지 삭제
  const handleDeleteNotice = async (noticeId) => {
    if (!window.confirm("정말 이 공지사항을 삭제할까요?")) return;
    try {
      const res = await api.delete(`/admin/notices/${noticeId}`);
      if (res.data.success) {
        setNotices((prev) => prev.filter((n) => n.notice_id !== noticeId));
      } else {
        alert(res.data.message || "삭제에 실패했습니다.");
      }
    } catch (err) {
      console.error("공지 삭제 실패:", err);
      alert("공지 삭제 중 오류가 발생했습니다.");
    }
  };

  // 로그아웃
  const handleLogout = async () => {
    try {
      await api.post("/admin/logout", {
        request_user: adminInfo?.username || "admin",
      });
    } catch (err) {
      console.error("로그아웃 요청 중 오류:", err);
    }
    if (onLogout) {
      onLogout();
    }
  };

  const tabs = [
    {
      id: "inquiry",
      label: "사용자 문의 관리",
      icon: <MessageSquare size={18} />,
    },
    { id: "notice", label: "공지사항 관리", icon: <FileText size={18} /> },
    { id: "data", label: "데이터 관리", icon: <Database size={18} /> },
    { id: "aimodel", label: "AI 모델 재학습", icon: <Cpu size={18} /> },
  ];

  const renderContent = () => {
    switch (activeTab) {
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
                {inqLoading ? (
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
            <div className="lg:col-span-2 flex items-start mt-23">
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
                      value={replyTexts}
                      onChange={(e) => setReplyTexts(e.target.value)}
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

      case "notice":
        return (
          <div className="space-y-4">
            {/* 헤더 */}
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-slate-800">
                등록된 공지사항
              </h3>

              <button
                onClick={() => {
                  setIsEditing(false);
                  setEditingNoticeId(null); // ← 반드시 reset
                  setNoticeTitle(""); // ← input 초기화
                  setNoticeContent(""); // ← textarea 초기화
                  setNoticeFormOpen((v) => !v);
                }}
                className="flex items-center gap-1 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-700"
              >
                {noticeFormOpen ? "작성 취소" : "+ 글쓰기"}
              </button>
            </div>

            {/* 공지 작성 / 수정 폼 */}
            {noticeFormOpen && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  isEditing ? handleupdateNotice() : handleCreateNotice();
                }}
                className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3"
              >
                <h4 className="font-bold text-slate-800">
                  {isEditing ? "공지사항 수정" : "새 공지사항 작성"}
                </h4>

                <input
                  type="text"
                  placeholder="제목"
                  value={noticeTitle}
                  onChange={(e) => setNoticeTitle(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500"
                  required
                />

                <textarea
                  placeholder="내용"
                  rows={5}
                  value={noticeContent}
                  onChange={(e) => setNoticeContent(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 resize-none"
                  required
                />

                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setNoticeFormOpen(false)}
                    className="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    disabled={noticeSaving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60"
                  >
                    {noticeSaving ? "저장 중..." : isEditing ? "수정" : "등록"}
                  </button>
                </div>
              </form>
            )}

            {/* 공지 로딩 */}
            {noticeLoading && (
              <div className="bg-white rounded-xl border border-slate-100 p-6 text-center text-slate-400">
                공지사항 불러오는 중...
              </div>
            )}

            {/* 공지 없음 */}
            {!noticeLoading && notices.length === 0 && (
              <div className="bg-white rounded-xl border border-slate-100 p-6 text-center text-slate-500">
                등록된 공지사항이 없습니다.
              </div>
            )}

            {/* 공지 목록 */}
            {!noticeLoading &&
              notices.length > 0 &&
              notices.map((notice) => (
                <div
                  key={notice.notice_id}
                  className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm hover:border-blue-100 transition-colors flex justify-between items-start"
                >
                  <div className="flex-1">
                    <div className="font-bold text-slate-800 text-lg">
                      {notice.title}
                    </div>

                    <div className="mt-2 mb-2 p-3 bg-slate-50 rounded-lg text-sm text-slate-700 whitespace-pre-wrap border border-slate-100">
                      {notice.content}
                    </div>

                    <div className="text-xs text-slate-500">
                      {notice.created_at?.slice(0, 10)}
                    </div>
                  </div>

                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => {
                        setIsEditing(true);
                        setEditingNoticeId(notice.notice_id);
                        setNoticeTitle(notice.title);
                        setNoticeContent(notice.content);
                        setNoticeFormOpen(true);
                      }}
                      className="px-3 py-1.5 bg-blue-50 text-blue-600 text-sm rounded-lg hover:bg-blue-100"
                    >
                      수정
                    </button>
                    <button
                      onClick={() => handleDeleteNotice(notice.notice_id)}
                      className="px-3 py-1.5 bg-red-50 text-red-600 text-sm rounded-lg hover:bg-red-100"
                    >
                      삭제
                    </button>
                  </div>
                </div>
              ))}
          </div>
        );

      case "data":
        return <DataManage />;

      case "aimodel":
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-bold text-slate-800">AI 모델 관리</h3>
              <button
                onClick={fetchAIStats}
                className="text-sm px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
              >
                새로고침
              </button>
            </div>

            {aiLoading ? (
              <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm text-center text-slate-400">
                AI 모델 정보를 불러오는 중...
              </div>
            ) : (
              <>
                {/* 현재 활성 모델 정보 */}
                <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <div className="font-bold text-slate-800 text-lg">
                        {aiStats.active_model
                          ? `${aiStats.active_model.model_name} ${aiStats.active_model.version}`
                          : "활성 모델 없음"}
                      </div>
                      <div className="text-green-500 text-sm font-medium mt-1">
                        ● 가동 중
                        {aiStats.active_model?.accuracy && (
                          /*<span className="text-slate-600 ml-2">
                            (정확도:{" "}
                            {(aiStats.active_model.accuracy * 100).toFixed(1)}%)
                          </span>*/
                          <span></span>
                        )}
                      </div>
                      {aiStats.active_model?.description && (
                        <div className="text-xs text-slate-500 mt-2">
                          {aiStats.active_model.description}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={handleRetrain}
                      disabled={retraining || aiStats.total_feedbacks === 0}
                      className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 shadow-md disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                    >
                      {retraining ? "요청 중..." : "재학습 시작"}
                    </button>
                  </div>

                  {aiStats.active_model?.updated_at && (
                    <div className="text-xs text-slate-400 text-right mt-2">
                      마지막 업데이트:{" "}
                      {new Date(aiStats.active_model.updated_at).toLocaleString(
                        "ko-KR"
                      )}
                    </div>
                  )}
                </div>

                {/* 통계 카드 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm">
                    <div className="text-xs text-slate-500 mb-1">전체 작업</div>
                    <div className="text-2xl font-bold text-slate-800">
                      {aiStats.total_jobs}
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm">
                    <div className="text-xs text-slate-500 mb-1">대기 중</div>
                    <div className="text-2xl font-bold text-yellow-600">
                      {aiStats.pending_jobs}
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm">
                    <div className="text-xs text-slate-500 mb-1">완료됨</div>
                    <div className="text-2xl font-bold text-green-600">
                      {aiStats.completed_jobs}
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm">
                    <div className="text-xs text-slate-500 mb-1">
                      피드백 데이터
                    </div>
                    <div className="text-2xl font-bold text-blue-600">
                      {aiStats.total_feedbacks}
                    </div>
                  </div>
                </div>

                {/* 안내 메시지 */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                  <div className="flex gap-3">
                    <div className="text-blue-600 mt-0.5">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-blue-900 text-sm mb-1">
                        AI 모델 재학습 안내
                      </div>
                      <div className="text-xs text-blue-800 space-y-1">
                        <p>
                          • 재학습 요청 시 수집된 사용자 피드백 데이터를
                          사용하여 모델을 개선합니다.
                        </p>
                        <p>
                          • 재학습은 백그라운드에서 진행되며, 서비스는 계속
                          제공됩니다.
                        </p>
                        <p>
                          • 재학습 완료 후 서버를 재시작하면 새 모델이 자동으로
                          적용됩니다.
                        </p>
                        {aiStats.total_feedbacks === 0 && (
                          <p className="text-red-600 font-semibold mt-2">
                            ⚠️ 재학습에 사용할 피드백 데이터가 없습니다. 사용자
                            피드백을 먼저 수집해주세요.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
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
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
            Dashboard
          </h2>
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
          <div className="flex items-center gap-3 text-sm">
            <button
              onClick={onGoToHome}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600 transition-colors"
            >
              사용자 화면으로 보기
            </button>
            <span className="text-slate-500">
              {adminInfo?.username || "Admin"} 님, 환영합니다.
            </span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <LogOut size={16} />
              로그아웃
            </button>
          </div>
        </header>

        <div className="animate-fade-in">{renderContent()}</div>
      </main>
    </div>
  );
}
