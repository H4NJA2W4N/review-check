import React, { useState } from "react";
import { ArrowLeft, Send, Search, MessageSquare, History, Edit3 } from "lucide-react";
import { api } from "../utils/api";

export default function Inquiry({ onBack, onSubmitted }) {
  // 탭 상태: 'write' (작성) | 'history' (내역 조회)
  const [activeTab, setActiveTab] = useState("write");

  // --- 작성 폼 상태 ---
  const [email, setEmail] = useState("");
  const [type, setType] = useState("분석 결과 문의");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  // --- 내역 조회 상태 ---
  const [searchEmail, setSearchEmail] = useState("");
  const [myInquiries, setMyInquiries] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [searched, setSearched] = useState(false); // 검색 시도 여부

  // 문의 작성 제출
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await api.post("/inquiries", {
        user_id: email,
        title: `[${type}] ${title}`,
        content: `${content}\n\n[문의 유형] ${type}\n[회신 이메일] ${email}`,
      });

      if (!res.data.success) {
        alert(res.data.message || "문의 등록에 실패했습니다.");
        return;
      }

      alert("문의가 정상적으로 접수되었습니다.");
      // 폼 초기화
      setEmail("");
      setType("분석 결과 문의");
      setTitle("");
      setContent("");

      if (onSubmitted) onSubmitted(res.data.inquiry);
    } catch (err) {
      console.error("문의 등록 오류:", err);
      alert("문의 등록 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 내 문의 내역 조회
  const handleSearchHistory = async (e) => {
    e.preventDefault();
    if (!searchEmail.trim()) {
      alert("이메일을 입력해주세요.");
      return;
    }
    setHistoryLoading(true);
    setSearched(true);

    try {
      // 백엔드 API: GET /user/inquiries?user_id=이메일
      const res = await api.get("/user/inquiries", {
        params: { user_id: searchEmail },
      });
      setMyInquiries(res.data.items || []);
    } catch (err) {
      console.error("내역 조회 오류:", err);
      alert("내역을 불러오는 중 오류가 발생했습니다.");
    } finally {
      setHistoryLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen px-4 pt-24 bg-slate-50">
      <div className="w-full max-w-2xl animate-fade-in">
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={onBack}
            className="p-2 hover:bg-white rounded-full transition-colors"
          >
            <ArrowLeft className="text-slate-600" />
          </button>
          <h2 className="text-3xl font-extrabold text-slate-800">고객센터</h2>
        </div>

        {/* 탭 버튼 영역 */}
        <div className="flex mb-6 bg-slate-200 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab("write")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-bold transition-all ${
              activeTab === "write"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <Edit3 size={16} /> 문의 작성하기
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-bold transition-all ${
              activeTab === "history"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <History size={16} /> 나의 문의 내역
          </button>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-100 min-h-[500px]">
          {/* --- 탭 1: 문의 작성 --- */}
          {activeTab === "write" && (
            <div className="animate-fade-in">
              <p className="text-slate-500 mb-6">
                서비스 이용 중 불편한 점이나 궁금한 점을 남겨주세요.
                <br />
                담당자가 확인 후 빠르게 답변 드리겠습니다.
              </p>

              <form className="space-y-6" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">
                    이메일 주소
                  </label>
                  <input
                    type="email"
                    placeholder="답변 받을 이메일을 입력하세요"
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">
                    문의 유형
                  </label>
                  <select
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                  >
                    <option>분석 결과 문의</option>
                    <option>서비스 오류 신고</option>
                    <option>기타 문의</option>
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
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
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
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  ></textarea>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-60"
                >
                  <Send size={18} /> {loading ? "전송 중..." : "문의 접수하기"}
                </button>
              </form>
            </div>
          )}

          {/* --- 탭 2: 나의 문의 내역 (답변 확인) --- */}
          {activeTab === "history" && (
            <div className="animate-fade-in h-full flex flex-col">
              <p className="text-slate-500 mb-6">
                이메일을 입력하여 이전에 작성한 문의와 답변을 확인하세요.
              </p>

              <form onSubmit={handleSearchHistory} className="flex gap-2 mb-8">
                <input
                  type="email"
                  placeholder="작성 시 입력한 이메일 주소"
                  className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500"
                  value={searchEmail}
                  onChange={(e) => setSearchEmail(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={historyLoading}
                  className="px-6 bg-slate-800 text-white rounded-lg font-bold hover:bg-slate-900 transition-colors flex items-center gap-2"
                >
                  <Search size={18} /> 조회
                </button>
              </form>

              {/* 조회 결과 영역 */}
              <div className="flex-1 overflow-y-auto">
                {historyLoading && (
                  <div className="text-center py-10 text-slate-400">
                    내역을 불러오는 중입니다...
                  </div>
                )}

                {!historyLoading && searched && myInquiries.length === 0 && (
                  <div className="text-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                    <p className="text-slate-500">조회된 문의 내역이 없습니다.</p>
                  </div>
                )}

                {!historyLoading && myInquiries.length > 0 && (
                  <div className="space-y-4">
                    {myInquiries.map((item) => (
                      <div
                        key={item.inquiry_id}
                        className="border border-slate-200 rounded-xl p-5 hover:border-blue-200 transition-colors"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-bold text-slate-800 text-lg">
                            {item.title}
                          </h4>
                          <span
                            className={`px-2 py-1 rounded text-xs font-bold ${
                              item.status === "done"
                                ? "bg-green-100 text-green-700"
                                : "bg-orange-100 text-orange-600"
                            }`}
                          >
                            {item.status === "done" ? "답변 완료" : "처리 중"}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 mb-3">
                          작성일: {item.created_at?.slice(0, 10)}
                        </div>
                        <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg mb-3">
                          {item.content}
                        </p>

                        {item.has_reply && (
                          <div className="mt-4 bg-blue-50 border border-blue-100 rounded-lg p-4 animate-fade-in">
                            <div className="flex items-center gap-2 text-blue-700 font-bold text-sm mb-2">
                              <MessageSquare size={16} /> 관리자 답변
                            </div>
                            <div className="text-slate-700 text-sm whitespace-pre-wrap">
                              {/* reply 객체 안의 content를 참조하도록 수정 */}
                              {item.reply?.content || item.reply_content}
                            </div>
                          </div>
                        )}
                        
                        {/* 답변 대기 중일 때 안내 */}
                        {!item.has_reply && (
                           <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
                             <span className="w-1.5 h-1.5 bg-orange-400 rounded-full"></span>
                             관리자가 내용을 확인하고 있습니다. 조금만 기다려주세요.
                           </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}