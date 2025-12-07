// src/utils/api.js
import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000", // 백엔드 FastAPI 주소
});

// 요청 보낼 때마다 자동으로 Authorization 헤더 붙여주는 인터셉터
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("adminToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function setAdminToken(token) {
  if (token) {
    localStorage.setItem("adminToken", token);
  } else {
    localStorage.removeItem("adminToken");
  }
}

export function getAdminToken() {
  return localStorage.getItem("adminToken");
}
