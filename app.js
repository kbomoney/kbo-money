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
      allPlayers = Array.isArray(data) ? data : (data.players || []);
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
    })
    .catch((error) => {
      console.error("데이터 로드 실패:", error);
      playerList.innerHTML = "<p class='no-data'>데이터를 불러오는 중 오류가 발생했습니다.</p>";
    });

  // 다국어/다양한 JSON Key값을 유연하게 가져오는 함수
  function getValue(obj, keys) {
    if (!obj) return "";
    for (let key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) {
        return String(obj[key]);
      }
    }
    return "";
  }

  // 검색 처리 함수
  function handleSearch() {
    const keyword = searchInput.value.trim().toLowerCase();

    if (!keyword) {
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
      return;
    }

    const filtered = allPlayers.filter((player) => {
      const name = getValue(player, ["name", "Name", "선수명", "이름"]);
      const team = getValue(player, ["team", "Team", "구단", "팀"]);
      const pos = getValue(player, ["position", "Position", "포지션"]);

      return (
        name.toLowerCase().includes(keyword) ||
        team.toLowerCase().includes(keyword) ||
        pos.toLowerCase().includes(keyword)
      );
    });

    renderPlayers(filtered);
  }

  // 실시간 및 엔터키 이벤트 listener
  searchInput.addEventListener("input", handleSearch);
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") handleSearch();
  });

  // 카드 렌더링 함수
  function renderPlayers(players) {
    playerList.innerHTML = "";

    if (!players || players.length === 0) {
      playerList.innerHTML = "<p class='no-data'>검색 결과가 없습니다.</p>";
      return;
    }

    players.forEach((player) => {
      const name = getValue(player, ["name", "Name", "선수명", "이름"]) || "이름 없음";
      const team = getValue(player, ["team", "Team", "구단", "팀"]) || "-";
      const pos = getValue(player, ["position", "Position", "포지션"]) || "-";
      const salary = getValue(player, ["salary", "Salary", "연봉"]) || "-";

      const card = document.createElement("div");
      card.className = "player-card";

      card.innerHTML = `
        <h3>${name}</h3>
        <p><strong>구단:</strong> ${team}</p>
        <p><strong>포지션:</strong> ${pos}</p>
        <p><strong>연봉:</strong> ${salary}</p>
      `;

      playerList.appendChild(card);
    });
  }
});
