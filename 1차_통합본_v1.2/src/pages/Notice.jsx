// src/pages/Notice.jsx
import React, { useState, useEffect } from "react";
import { ArrowLeft, Plus, X, Edit, Trash2, ChevronRight } from "lucide-react";
import { api } from "../utils/api"; // axios instance

export default function Notice({ isAdmin, navigateTo, showToast }) {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ title: "", content: "" });

  // -------------------------------
  // 📌 공지 목록 조회
  // -------------------------------
  const fetchNotices = async () => {
    try {
      setLoading(true);
      const res = await api.get("/user/notices", {
        params: { page: 1, size: 20 },
      });

      setNotices(res.data.items || []);
    } catch (err) {
      console.error("공지 조회 실패:", err);
      showToast("공지사항을 불러오는 데 실패했습니다.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, []);

  // -------------------------------
  // 📌 공지 생성
  // -------------------------------
  const createNotice = async () => {
    if (!formData.title || !formData.content) {
      showToast("제목과 내용을 입력해주세요.", "error");
      return;
    }

    try {
      const token = localStorage.getItem("admin_token");

      const res = await api.post(
        "/admin/notices",
        {
          title: formData.title,
          content: formData.content,
          attachments: [],
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const data = res.data;

      if (data.success) {
        showToast("공지사항이 등록되었습니다.", "success");
        setShowForm(false);
        setFormData({ title: "", content: "" });
        fetchNotices();
      } else {
        showToast(data.message || "등록에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("공지 생성 실패:", err);
      showToast("서버 연결에 실패했습니다.", "error");
    }
  };

  // -------------------------------
  // 📌 공지 삭제
  // -------------------------------
  const deleteNotice = async (noticeId) => {
    if (!window.confirm("정말 삭제하시겠습니까?")) return;

    try {
      const token = localStorage.getItem("admin_token");

      const res = await api.delete(`/admin/notices/${noticeId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.data.success) {
        showToast("공지사항이 삭제되었습니다.", "success");
        fetchNotices();
      } else {
        showToast(res.data.message || "삭제에 실패했습니다.", "error");
      }
    } catch (err) {
      console.error("공지 삭제 오류:", err);
      showToast("서버 연결에 실패했습니다.", "error");
    }
  };

  // -------------------------------
  // 📌 렌더링
  // -------------------------------
  return (
    <div className="flex flex-col items-center min-h-screen px-4 pt-24 bg-slate-50">
      <div className="w-full max-w-3xl animate-fade-in">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigateTo("home")}
              className="p-2 hover:bg-white rounded-full transition-colors"
            >
              <ArrowLeft className="text-slate-600" />
            </button>
            <h2 className="text-3xl font-extrabold text-slate-800">공지사항</h2>
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

        {/* 작성 폼 */}
        {isAdmin && showForm && (
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-6">
            <input
              type="text"
              placeholder="제목"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-3"
            />

            <textarea
              placeholder="내용"
              rows={5}
              value={formData.content}
              onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
              }
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg mb-3 resize-none"
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

        {/* 공지 목록 */}
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
                className="p-6 border-b border-slate-100 hover:bg-slate-50 transition-colors group cursor-pointer"
                onClick={() => navigateTo("noticeDetail", notice.notice_id)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-bold text-lg mb-1 text-slate-800 group-hover:text-blue-600">
                      {notice.title}
                    </h3>
                    <p className="text-slate-500 text-sm mb-2">
                      {notice.content.substring(0, 80)}...
                    </p>
                    <p className="text-slate-400 text-xs">
                      {new Date(notice.created_at).toLocaleDateString("ko-KR")}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {isAdmin ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigateTo("noticeDetail", notice.notice_id);
                          }}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteNotice(notice.notice_id);
                          }}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                        >
                          <Trash2 size={18} />
                        </button>
                      </>
                    ) : (
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
}
