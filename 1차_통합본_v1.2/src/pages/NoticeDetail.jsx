// src/pages/NoticeDetail.jsx
import React, { useEffect, useState } from "react";
import { ArrowLeft, Edit, Trash2, FileText } from "lucide-react";
import { api } from "../utils/api";

export default function NoticeDetail({
  selectedNoticeId,
  navigateTo,
  showToast,
  isAdmin,
}) {
  const [notice, setNotice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ title: "", content: "" });

  // --------------------------------------------------------
  // 📌 공지 상세 조회
  // --------------------------------------------------------
  const fetchNoticeDetail = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/user/notices/${selectedNoticeId}`);

      if (res.data.success && res.data.notice) {
        setNotice(res.data.notice);
        setEditForm({
          title: res.data.notice.title,
          content: res.data.notice.content,
        });
      }
    } catch (err) {
      console.error("공지 조회 오류:", err);
      showToast("공지사항을 불러오는데 실패했습니다.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedNoticeId) fetchNoticeDetail();
  }, [selectedNoticeId]);

  // --------------------------------------------------------
  // 📌 공지 수정
  // --------------------------------------------------------
  const updateNotice = async () => {
    if (!editForm.title || !editForm.content) {
      showToast("제목과 내용을 입력해주세요.", "error");
      return;
    }

    try {
      const token = localStorage.getItem("admin_token");

      const res = await api.put(
        `/admin/notices/${selectedNoticeId}`,
        {
          title: editForm.title,
          content: editForm.content,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (res.data.success) {
        showToast("공지사항이 수정되었습니다.", "success");
        setIsEditing(false);
        fetchNoticeDetail();
      } else {
        showToast(res.data.message || "수정에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("공지 수정 오류:", err);
      showToast("서버 연결에 실패했습니다.", "error");
    }
  };

  // --------------------------------------------------------
  // 📌 공지 삭제
  // --------------------------------------------------------
  const deleteNotice = async () => {
    if (!window.confirm("정말 삭제하시겠습니까?")) return;

    try {
      const token = localStorage.getItem("admin_token");

      const res = await api.delete(`/admin/notices/${selectedNoticeId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.data.success) {
        showToast("공지사항이 삭제되었습니다.", "success");
        navigateTo("notice");
      } else {
        showToast(res.data.message || "삭제에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("공지 삭제 오류:", err);
      showToast("서버 연결에 실패했습니다.", "error");
    }
  };

  // --------------------------------------------------------
  // 📌 로딩 처리
  // --------------------------------------------------------
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

  // --------------------------------------------------------
  // 📌 렌더링
  // --------------------------------------------------------
  return (
    <div className="flex flex-col items-center min-h-screen px-4 pt-24 pb-12 bg-slate-50">
      <div className="w-full max-w-3xl animate-fade-in">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigateTo("notice")}
              className="p-2 hover:bg-white rounded-full transition-colors"
            >
              <ArrowLeft className="text-slate-600" />
            </button>
            <h2 className="text-2xl font-extrabold text-slate-800">공지사항</h2>
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

        {/* 본문 */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          {isEditing ? (
            // -------------------------------
            // 📌 수정 모드
            // -------------------------------
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
            // -------------------------------
            // 📌 읽기 모드
            // -------------------------------
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

              {/* 본문 */}
              <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                {notice.content}
              </p>

              {/* 첨부파일 */}
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
                        <span className="text-slate-700">{att.file_name}</span>
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
}
