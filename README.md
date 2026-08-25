# ⚾ KBO 프로야구 연봉 & 경력 정보관 (kbo-money)

> KBO 프로야구 10개 구단 선수들의 연봉·이적 히스토리와 감독/코치진의 선수·지도자 경력을 한눈에 볼 수 있는 웹 서비스입니다.

🔗 **웹사이트 바로가기:** [https://kbomoney.github.io/kbo-money/](https://kbomoney.github.io/kbo-money/)

---

## 📌 주요 기능

* **10개 구단 필터링:** KIA, 삼성, LG, 두산, SSG, KT, NC, 롯데, 한화, 키움 등 원하는 구단 선택 조회
* **포지션 & 코치진 분류:** 코치진, 투수, 포수, 내야수, 외야수 카테고리 구분
* **선수 연봉 타임라인:** 신인 첫 연봉, FA/다년 계약 내역, 연도별 소속 구단 변동 시각화
* **코치진 경력 타임라인:** 선수 시절 기록과 지도자(코치/감독) 보직 변경 이력을 구분하여 제공
* **실시간 이름 검색:** 선수 및 코치 이름을 입력하면 즉시 데이터 필터링

---

## 🛠️ 기술 스택 (Tech Stack)

* **Frontend:** HTML5, CSS3, JavaScript (ES6+)
* **Data Format:** JSON (`data/players.json`)
* **Hosting:** GitHub Pages

---

## 📂 프로젝트 구조 (Project Structure)

```text
kbo-money/
├── index.html        # 메인 레이아웃 및 모달 UI
├── style.css         # 반응형 UI 디자인
├── app.js            # 데이터 필터링, 검색, 모달 제어 로직
├── README.md         # 프로젝트 안내 문서
└── data/
    └── players.json  # 선수 연봉 히스토리 & 코치진 경력 데이터
