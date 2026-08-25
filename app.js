let allPlayers = [];
let currentTeam = 'ALL';
let currentGroup = 'ALL';

// JSON 데이터 로드
fetch('./data/players.json')
  .then(res => res.json())
  .then(data => {
    allPlayers = data;
    renderCards();
  })
  .catch(err => console.error("데이터 로드 실패:", err));

// 카드 출력 로직
function renderCards() {
  const grid = document.getElementById('cardGrid');
  const searchKeyword = document.getElementById('searchInput').value.toLowerCase();
  grid.innerHTML = '';

  const filtered = allPlayers.filter(item => {
    const matchTeam = (currentTeam === 'ALL' || item.team === currentTeam);
    const matchGroup = (currentGroup === 'ALL' || item.positionGroup === currentGroup);
    const matchSearch = item.name.toLowerCase().includes(searchKeyword);
    return matchTeam && matchGroup && matchSearch;
  });

  if (filtered.length === 0) {
    grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #888;">조건에 해당하는 데이터가 없습니다.</p>';
    return;
  }

  filtered.forEach(p => {
    const card = document.createElement('div');
    card.className = 'player-card';
    card.onclick = () => openModal(p);
    
    // 카드 하단 텍스트 수정: '팀명 + 선수/코치 직책' 표기
    const teamSubText = p.isCoach ? `${p.team} (${p.role || '코치'})` : `${p.team} 베어스/이글스 등`.includes('/') ? `${p.team}` : p.team;
    
    card.innerHTML = `
      <span class="card-badge">${p.positionGroup} ${p.role ? `- ${p.role}` : ''}</span>
      <div class="card-name">${p.name}</div>
      <div class="card-team">${p.isCoach ? `${p.team} ${p.role || '코치'}` : `${p.team} 소속`}</div>
    `;
    grid.appendChild(card);
  });
}

// 이벤트 리스너 설정
document.getElementById('teamButtons').addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON') {
    document.querySelectorAll('.team-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    currentTeam = e.target.dataset.team;
    renderCards();
  }
});

document.getElementById('groupTabs').addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON') {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    currentGroup = e.target.dataset.group;
    renderCards();
  }
});

document.getElementById('searchInput').addEventListener('input', renderCards);

// 모달 열기
function openModal(data) {
  const modal = document.getElementById('detailModal');
  const body = document.getElementById('modalBody');

  let timelineHtml = '';

  if (data.isCoach) {
    // 코치진 (선수 경력 + 지도자 경력)
    timelineHtml = `
      <h2>${data.name} (${data.team} ${data.role || '코치'})</h2>
      <p style="font-size: 0.85rem; color: #666; margin-top: 4px;">입단: ${data.draftInfo || '정보 없음'}</p>
      
      <h4 style="margin-top: 16px;">⚾ 선수 시절 경력</h4>
      <div class="timeline">
        ${(data.playerHistory || []).map(h => `
          <div class="timeline-item">
            <div class="timeline-period">${h.period}</div>
            <div class="timeline-title">${h.team}</div>
            <div class="timeline-sub">${h.note}</div>
          </div>
        `).join('')}
      </div>

      <h4 style="margin-top: 16px;">📋 지도자 경력</h4>
      <div class="timeline">
        ${(data.coachHistory || []).map(h => `
          <div class="timeline-item">
            <div class="timeline-period">${h.period}</div>
            <div class="timeline-title">${h.team}</div>
            <div class="timeline-sub">${h.note}</div>
          </div>
        `).join('')}
      </div>
    `;
  } else {
    // 일반 선수 (입단 연봉 + 연봉 이적 타임라인)
    timelineHtml = `
      <h2>${data.name} (${data.team} / ${data.positionGroup})</h2>
      <p style="font-size: 0.85rem; color: #666; margin-top: 4px;">입단 정보: ${data.draftInfo || '정보 없음'}</p>
      <p style="font-size: 0.85rem; color: #666;">신인 첫 연봉: ${data.firstSalary ? data.firstSalary.toLocaleString() + '만 원' : '정보 없음'}</p>
      
      <h4 style="margin-top: 16px;">💰 연봉 및 구단 이력 히스토리</h4>
      <div class="timeline">
        ${(data.history || []).map(h => `
          <div class="timeline-item">
            <div class="timeline-period">${h.period}</div>
            <div class="timeline-title">${h.team}</div>
            <div class="timeline-sub">연봉: ${h.salary}</div>
            <div style="font-size: 0.8rem; color: #555;">${h.note}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  body.innerHTML = timelineHtml;
  modal.style.display = 'flex';
}

// 모달 닫기
document.getElementById('closeModal').onclick = () => {
  document.getElementById('detailModal').style.display = 'none';
};

window.onclick = (e) => {
  if (e.target === document.getElementById('detailModal')) {
    document.getElementById('detailModal').style.display = 'none';
  }
};
