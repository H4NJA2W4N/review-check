import React, { useState, useEffect } from 'react';
import { api } from '../utils/api'; // ⚠️ api 유틸 경로가 다르다면 수정 필요 (없으면 axios 사용)
// import axios from 'axios'; // api 유틸이 없다면 이걸 주석 해제하고 사용

const DataManage = () => {
  // --- [1] 여기에 상태(State) 코드를 넣으세요 ---
  const [stats, setStats] = useState({ total_count: 0, today_count: 0 });
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // --- [2] 페이지 켜지면 통계 가져오는 함수 (useEffect) ---
  useEffect(() => {
    const fetchStats = async () => {
      try {
        // 백엔드: /admin/stats 호출
        const response = await api.get('/admin/stats'); 
        setStats(response.data);
      } catch (error) {
        console.error("통계 불러오기 실패:", error);
      }
    };
    fetchStats();
  }, []);

  // --- [3] 다운로드 버튼 누르면 실행될 함수 ---
  const handleDownload = async () => {
    if (!startDate || !endDate) {
      alert("시작일과 종료일을 모두 설정해주세요.");
      return;
    }

    try {
      // 백엔드: /admin/download-csv 호출
      const response = await api.get('/admin/download-csv', {
        params: { start_date: startDate, end_date: endDate },
        responseType: 'blob', // ⭐️ 중요: 파일 데이터로 받기 설정
      });

      // 브라우저에서 강제로 다운로드 실행시키는 코드
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_data_${startDate}_${endDate}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      alert("다운로드에 실패했습니다. (데이터가 없거나 서버 오류)");
    }
  };

  return (
    <div className="p-6"> 

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="font-bold text-lg mb-4">데이터 추출 및 관리</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {/* 1. 누적 분석 수 카드 */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-sm font-semibold text-slate-500 mb-1">총 누적 분석 수</p>
          <div className="text-3xl font-extrabold text-slate-800">
            {stats.total_count} <span className="text-lg font-bold text-blue-600">건</span>
          </div>
        </div>
        
        {/* 2. 금일 분석 요청 카드 */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-sm font-semibold text-slate-500 mb-1">금일 분석 요청</p>
          <div className="text-3xl font-extrabold text-blue-600">
            {stats.today_count} <span className="text-lg font-bold text-slate-800">건</span>
          </div>
        </div>
      </div>
      
        {/* 날짜 입력 구간 */}
        <div className="flex gap-4 items-center mb-6">
           {/* 시작일 input 찾아서 value랑 onChange 연결 */}
           <input 
             type="date" 
             className="border p-2 rounded"
             value={startDate} // 👈 추가
             onChange={(e) => setStartDate(e.target.value)} // 👈 추가
           />
           <span>~</span>
           {/* 종료일 input 찾아서 value랑 onChange 연결 */}
           <input 
             type="date" 
             className="border p-2 rounded"
             value={endDate} // 👈 추가
             onChange={(e) => setEndDate(e.target.value)} // 👈 추가
           />
        </div>

        {/* 다운로드 버튼 찾아서 onClick 연결 */}
        <div className="flex justify-between items-center border p-4 rounded bg-gray-50">
           <div>
             <p className="font-bold">리뷰 분석 데이터 로그</p>
             <p className="text-sm text-gray-500">선택한 기간 내의 URL별 신뢰도 분석 결과 기록 (.csv)</p>
           </div>
           <button 
             onClick={handleDownload} // 👈 여기에 연결!
             className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-bold"
           >
             데이터 다운로드
           </button>
        </div>
      </div>
    </div>
  );
};

export default DataManage;