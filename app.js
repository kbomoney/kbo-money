document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const playerList = document.getElementById("player-list");

  let allPlayers = [];

  // JSON 데이터 불러오기 및 예외 처리
  fetch("./data.json")
    .then((response) => {
      if (!response.ok) throw new Error("HTTP error " + response.status);
      return response.json();
    })
    .then((data) => {
      // JSON이 어떤 형태로 들어오든 배열로 가공
      if (Array.isArray(data)) {
        allPlayers = data;
      } else if (typeof data === "object" && data !== null) {
        // 객체 내부의 첫 번째 배열을 찾아내거나 객체 자체를 배열로 변환
        const firstArray = Object.values(data).find((val) => Array.isArray(val));
        allPlayers = firstArray || [data];
      }
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
    })
    .catch((error) => {
      console.error("데이터 로드 실패:", error);
      playerList.innerHTML = "<p class='no-data'>데이터(data.json)를 불러올 수 없습니다. 파일명을 확인해 주세요.</p>";
    });

  // 객체 안의 모든 텍스트 값을 하나로 합쳐서 검색어로 검사하는 함수
  function matchPlayer(player, keyword) {
    if (!player) return false;
    // 객체 전체 값을 문자열로 변환하여 검색어 포함 여부 확인
    const searchableText = JSON.stringify(player).toLowerCase();
    return searchableText.includes(keyword.toLowerCase());
  }

  // 검색 처리 함수
  function handleSearch() {
    const keyword = searchInput.value.trim();

    if (!keyword) {
      playerList.innerHTML = "<p class='no-data'>검색어를 입력하시면 결과가 표시됩니다.</p>";
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

  // 객체에서 적절한 값을 찾아내는 헬퍼
  function findProp(obj, keys) {
    for (let key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) return obj[key];
    }
    // 정확한 키가 없으면 객체의 첫 3개 항목 중 순서대로 할당
    return null;
  }

  // 카드 렌더링 함수
  function renderPlayers(players) {
    playerList.innerHTML = "";

    if (!players || players.length === 0) {
      playerList.innerHTML = "<p class='no-data'>검색 결과가 없습니다.</p>";
      return;
    }

    players.forEach((player) => {
      // 다양한 키 이름 대응 (이름, 구단, 포지션, 연봉)
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
