document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const playerList = document.getElementById("player-list");

  let allPlayers = [];

  // data/players.json 경로로 완벽하게 지정
  const jsonUrl = new URL("data/players.json", window.location.href).href;

  fetch(jsonUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error("HTTP error " + response.status);
      }
      return response.json();
    })
    .then((data) => {
      if (Array.isArray(data)) {
        allPlayers = data;
      } else if (typeof data === "object" && data !== null) {
        const firstArray = Object.values(data).find((val) => Array.isArray(val));
        allPlayers = firstArray || [data];
      }
      playerList.innerHTML = "";
    })
    .catch((error) => {
      console.error("데이터 로드 실패:", error);
      playerList.innerHTML = "";
    });

  // 한글 자음/모음 유연 분리 (오타 보정)
  function disassembleHangul(str) {
    if (!str) return "";
    const CHO = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];
    const JOONG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"];
    const JONG = ["", "ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];

    let result = "";
    for (let i = 0; i < str.length; i++) {
      const code = str.charCodeAt(i) - 44032;
      if (code >= 0 && code <= 11172) {
        const cho = Math.floor(code / 588);
        const joong = Math.floor((code - cho * 588) / 28);
        const jong = code % 28;
        
        let normalizedJoong = JOONG[joong];
        if (normalizedJoong === "ㅠ") normalizedJoong = "ㅜ";
        if (normalizedJoong === "ㅕ") normalizedJoong = "ㅓ";
        if (normalizedJoong === "ㅛ") normalizedJoong = "ㅗ";

        result += CHO[cho] + normalizedJoong + JONG[jong];
      } else {
        result += str[i];
      }
    }
    return result;
  }

  function matchPlayer(player, keyword) {
    if (!player) return false;
    const rawText = JSON.stringify(player).toLowerCase().replace(/\s+/g, "");
    const cleanKeyword = keyword.toLowerCase().replace(/\s+/g, "");
    if (rawText.includes(cleanKeyword)) return true;

    const disText = disassembleHangul(rawText);
    const disKeyword = disassembleHangul(cleanKeyword);
    return disText.includes(disKeyword);
  }

  function handleSearch() {
    const keyword = searchInput.value.trim();

    if (!keyword) {
      playerList.innerHTML = "";
      return;
    }

    const filtered = allPlayers.filter((player) => matchPlayer(player, keyword));
    renderPlayers(filtered);
  }

  searchInput.addEventListener("input", handleSearch);
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") handleSearch();
  });

  function findProp(obj, keys) {
    for (let key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) return obj[key];
    }
    return null;
  }

  function renderPlayers(players) {
    playerList.innerHTML = "";

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
