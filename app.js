document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const playerList = document.getElementById("player-list");

  let allPlayers = [];

  // JSON 데이터 불러오기 (상대 경로 적용)
  fetch("./data.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error("네트워크 응답 오류");
      }
      return response.json();
    })
    .then((data) => {
      allPlayers = data;
      // 초기에는 아무것도 출력하지 않고 안내 문구만 표시 (원할 경우 renderPlayers(allPlayers)로 전체 표시 가능)
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
    })
    .catch((error) => {
      console.error("데이터 로드 실패:", error);
      // 초기 진입 시 데이터 경로 문제가 있어도 사용자에게 자연스러운 안내 제공
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
    });

  // 검색 처리 함수
  function handleSearch() {
    const keyword = searchInput.value.trim().toLowerCase();

    // 검색어가 비어있을 때는 초기 안내 문구 출력
    if (!keyword) {
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
      return;
    }

    const filtered = allPlayers.filter((player) => {
      const nameMatch = player.name && player.name.toLowerCase().includes(keyword);
      const teamMatch = player.team && player.team.toLowerCase().includes(keyword);
      const posMatch = player.position && player.position.toLowerCase().includes(keyword);
      return nameMatch || teamMatch || posMatch;
    });

    renderPlayers(filtered);
  }

  // 실시간 입력 및 엔터 키 이벤트 등록
  searchInput.addEventListener("input", handleSearch);
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  });

  // 화면 카드 렌더링 함수
  function renderPlayers(players) {
    playerList.innerHTML = "";

    if (!players || players.length === 0) {
      playerList.innerHTML = "<p class='no-data'>검색 결과가 없습니다.</p>";
      return;
    }

    players.forEach((player) => {
      const card = document.createElement("div");
      card.className = "player-card";

      card.innerHTML = `
        <h3>${player.name || "이름 없음"}</h3>
        <p><strong>구단:</strong> ${player.team || "-"}</p>
        <p><strong>포지션:</strong> ${player.position || "-"}</p>
        <p><strong>연봉:</strong> ${player.salary || "-"}</p>
      `;

      playerList.appendChild(card);
    });
  }
});
