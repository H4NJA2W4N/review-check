// src/pages/AdminLogin.jsx
import React, { useState } from "react";
import { api, setAdminToken } from "../utils/api";

export default function AdminLogin({ onLoginSuccess, onBack }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setLoading(true);

    try {
      const res = await api.post("/admin/login", {
        username,
        password,
      });

      if (!res.data.success) {
        setErrorMsg(res.data.message || "로그인에 실패했습니다.");
        return;
      }

      // 토큰 저장
      setAdminToken(res.data.token);

      // 부모(App)에게 로그인 성공 알림
      if (onLoginSuccess) {
        onLoginSuccess({
          username,
          token: res.data.token,
          expiresAt: res.data.expires_at,
        });
      }
    } catch (err) {
      console.error("로그인 오류:", err);
      setErrorMsg("로그인 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-4 bg-slate-50">
      <div className="bg-white p-10 rounded-3xl shadow-xl border border-blue-50 w-full max-w-md">
        <h2 className="text-2xl font-extrabold text-center text-slate-800 mb-2">
          관리자 로그인
        </h2>
        <p className="text-center text-slate-500 mb-8 text-sm">
          시스템 관리를 위해 로그인해주세요.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              아이디
            </label>
            <input
              type="text"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              비밀번호
            </label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {errorMsg && <p className="text-sm text-red-500 mt-2">{errorMsg}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-800 text-white py-3 rounded-lg font-bold hover:bg-slate-900 transition-colors mt-4 disabled:opacity-60"
          >
            {loading ? "로그인 중..." : "접속하기"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-sm text-slate-400 hover:text-slate-600"
          >
            ← 메인으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
}
