// src/utils/api.js
import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000", // 백엔드 FastAPI 주소
});

// 요청 보낼 때마다 자동으로 Authorization 헤더 붙여주는 인터셉터
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("admin_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function setAdminToken(token) {
  if (token) {
    localStorage.setItem("admin_token", token);
  } else {
    localStorage.removeItem("admin_token");
  }
}

export function getAdminToken() {
  return localStorage.getItem("admin_token");
}
