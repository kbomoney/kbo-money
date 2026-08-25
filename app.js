document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const playerList = document.getElementById("player-list");

  let allPlayers = [];

  // JSON 데이터 불러오기
  fetch("./data.json")
    .then((response) => {
      if (!response.ok) throw new Error("HTTP error " + response.status);
      return response.json();
    })
    .then((data) => {
      if (Array.isArray(data)) {
        allPlayers = data;
      } else if (typeof data === "object" && data !== null) {
        const firstArray = Object.values(data).find((val) => Array.isArray(val));
        allPlayers = firstArray || [data];
      }
      // 초기 진입 시 아무 문구도 표시하지 않음
      playerList.innerHTML = "";
    })
    .catch((error) => {
      console.error("데이터 로드 실패:", error);
      // 데이터 로드 실패 시에도 초기 화면에는 문구를 띄우지 않음
      playerList.innerHTML = "";
    });

  // 객체 내 검색어 매칭 함수
  function matchPlayer(player, keyword) {
    if (!player) return false;
    const searchableText = JSON.stringify(player).toLowerCase();
    return searchableText.includes(keyword.toLowerCase());
  }

  // 검색 처리 함수
  function handleSearch() {
    const keyword = searchInput.value.trim();

    // 검색어가 없으면 화면을 깨끗하게 비움
    if (!keyword) {
      playerList.innerHTML = "";
      return;
    }

    const filtered = allPlayers.filter((player) => matchPlayer(player, keyword));
    renderPlayers(filtered);
  }

  // 실시간 입력 및 엔터키 이벤트
  searchInput.addEventListener("input", handleSearch);
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") handleSearch();
  });

  // Property 찾기 헬퍼
  function findProp(obj, keys) {
    for (let key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) return obj[key];
    }
    return null;
  }

  // 카드 렌더링 함수
  function renderPlayers(players) {
    playerList.innerHTML = "";

    // 검색창에 글자를 쳤는데 결과가 없을 때만 중앙에 문구 출력
    if (!players || players.length === 0) {
      playerList.innerHTML = "<p class='no-data'>검색 결과가 없습니다.</p>";
      return;
    }

    players.forEach((player) => {
      const name = findProp(player, ["name", "Name", "선수명", "이름"]) || Object.values(player)[0] || "이름 없음";
      const team = findProp(player, ["team", "Team", "구단", "팀"]) || Object.values(player)[1] || "-";
      const pos = findProp(player, ["position", "Position", "포지션"]) || Object.values(player)[2] || "-";
      const salary = findProp(player, ["salary", "Salary", "연봉", "경력"]) || Object.values(player)[3] || "-";

      const card = document.createElement("div");
      card.className = "player-card";

      card.innerHTML = `
        <h3>${name}</h3>
        <p><strong>구단:</strong> ${team}</p>
        <p><strong>포지션:</strong> ${pos}</p>
        <p><strong>연봉/정보:</strong> ${salary}</p>
      `;

      playerList.appendChild(card);
    });
  }
});
