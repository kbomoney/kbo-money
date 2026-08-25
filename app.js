document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const playerList = document.getElementById("player-list");

  let allPlayers = [];

  // data/players.json 경로 지정
  const jsonUrl = new URL("data/players.json", window.location.href).href;

  fetch(jsonUrl)
    .then((response) => {
      if (!response.ok) throw new Error("HTTP 에러 상태: " + response.status);
      return response.json();
    })
    .then((data) => {
      console.log("불러온 원본 데이터:", data);

      // 데이터 형태 유연하게 배열화
      if (Array.isArray(data)) {
        allPlayers = data;
      } else if (typeof data === "object" && data !== null) {
        // 객체 내부에서 배열 찾기
        const possibleArray = Object.values(data).find((val) => Array.isArray(val));
        allPlayers = possibleArray || [data];
      }

      console.log("변환된 선수 배열:", allPlayers);
      playerList.innerHTML = "";
    })
    .catch((error) => {
      console.error("데이터 로드 중 에러 발생:", error);
      playerList.innerHTML = "";
    });

  // 검색 처리
  function handleSearch() {
    const keyword = searchInput.value.trim().toLowerCase().replace(/\s+/g, "");

    if (!keyword) {
      playerList.innerHTML = "";
      return;
    }

    // 선수 데이터 전체 텍스트에서 검색어 포함 여부 확인
    const filtered = allPlayers.filter((player) => {
      if (!player) return false;
      const jsonString = JSON.stringify(player).toLowerCase().replace(/\s+/g, "");
      return jsonString.includes(keyword);
    });

    renderPlayers(filtered);
  }

  searchInput.addEventListener("input", handleSearch);
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") handleSearch();
  });

  // 카드 출력
  function renderPlayers(players) {
    playerList.innerHTML = "";

    if (!players || players.length === 0) {
      playerList.innerHTML = "<p class='no-data'>검색 결과가 없습니다.</p>";
      return;
    }

    players.forEach((player) => {
      // 객체의 첫 번째~네 번째 값을 순서대로 추출 (키 이름이 달라도 표시 가능)
      const values = Object.values(player);
      const name = player.name || player.Name || player.선수명 || player.이름 || values[0] || "이름 없음";
      const team = player.team || player.Team || player.구단 || player.팀 || values[1] || "-";
      const pos = player.position || player.Position || player.포지션 || values[2] || "-";
      const salary = player.salary || player.Salary || player.연봉 || player.경력 || values[3] || "-";

      const card = document.createElement("div");
      card.className = "player-card";

      card.innerHTML = `
        <h3>${name}</h3>
        <p><strong>구단:</strong> ${team}</p>
        <p><strong>포지션:</strong> ${pos}</p>
        <p><strong>연봉/경력:</strong> ${salary}</p>
      `;

      playerList.appendChild(card);
    });
  }
});
