/**
 * AI学习助手页面
 *
 * 启发式交互答疑，多Agent路由
 */
const LEARNING_AGENTS = [
  { idx: 1, cn: '问题路由 Agent', en: 'Question Router', desc: '分析问题类型，路由到最合适的Agent',
    inp: ['用户问题','会话上下文'], out: ['路由决策','问题分类'] },
  { idx: 2, cn: '导学追问 Agent', en: 'Tutoring Agent', desc: '通过追问引导用户深入思考',
    inp: ['路由决策','用户画像'], out: ['追问问题','引导策略'] },
  { idx: 3, cn: '知识答疑 Agent', en: 'QA Agent', desc: '解答具体的知识点疑问',
    inp: ['用户问题','知识库'], out: ['详细解答','参考资料'] },
  { idx: 4, cn: '案例讲解 Agent', en: 'Case Study Agent', desc: '通过案例辅助解释知识点',
    inp: ['知识点','业务场景'], out: ['案例演示','场景分析'] },
  { idx: 5, cn: '学情诊断 Agent', en: 'Diagnosis Agent', desc: '从对话中提取学情信息',
    inp: ['对话记录','交互行为'], out: ['能力推测','知识缺口'] },
  { idx: 6, cn: '画像更新 Agent', en: 'Profile Updater', desc: '根据新学情更新学习画像',
    inp: ['诊断结果','当前画像'], out: ['画像更新','学习建议'] },
];

let chatSessionId = null;

function renderLearningPage() {
  const main = document.getElementById('appMain');
  main.innerHTML = `
  <div class="page active" id="pageLearning">
    <div class="panel-layout">
      <aside class="left-panel">
        <div class="panel-title">💬 会话列表 <span class="badge" id="chatSessionCount">0</span></div>
        <div id="chatSessionList" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:4px">
          <div style="font-size:10px;color:rgba(255,255,255,.15);text-align:center;padding:16px">暂无会话</div>
        </div>
        <button class="btn-secondary" style="width:100%;padding:5px;font-size:10px" onclick="startNewChat()">+ 新会话</button>
      </aside>

      <main class="middle-panel">
        <div class="panel-title" style="margin-bottom:6px">💬 AI学习助手 <span class="badge" id="chatAgentLabel">启发式交互</span></div>
        <div class="chat-area" id="chatArea">
          ${emptyStateHTML('💬', '开始对话', '向AI学习助手提问，开始启发式学习之旅', '开始对话', 'startNewChat()')}
        </div>
        <div class="chat-input-area" id="chatInputArea" style="display:none">
          <input type="text" id="chatInput" placeholder="请输入你的问题..." onkeydown="if(event.key==='Enter')sendMessage()">
          <button onclick="sendMessage()">发送</button>
        </div>
      </main>

      <aside class="right-panel">
        <div class="panel-title">🤖 Agent路由 <span class="badge">实时</span></div>
        <div class="agent-flow" id="learningAgentFlow"></div>
      </aside>
    </div>
  </div>`;

  renderLearningAgents();
  loadChatData();
}

function renderLearningAgents() {
  const container = document.getElementById('learningAgentFlow');
  if (!container) return;
  container.innerHTML = LEARNING_AGENTS.map((a, i) =>
    `<div class="agent-card idle" data-idx="${a.idx}" data-module="learning">
      <div class="index">${String(a.idx).padStart(2,'0')}</div>
      <div class="info"><div class="cn">${a.cn}</div><div class="en">${a.en}</div><div class="desc">${a.desc}</div></div>
      <div class="status-icon">○</div>
    </div>` + (i < LEARNING_AGENTS.length - 1 ? '<div class="agent-arrow"><span class="chevron">▼</span></div>' : '')
  ).join('');
  container.querySelectorAll('.agent-card').forEach(el => {
    el.addEventListener('click', () => openLearningAgentDrawer(parseInt(el.dataset.idx)));
  });
}

function highlightLearningAgent(idx) {
  const cards = document.querySelectorAll('#learningAgentFlow .agent-card');
  cards.forEach(c => c.classList.remove('active','completed'));
  for (let i = 1; i <= idx && i <= cards.length; i++) {
    cards[i-1].classList.remove('active','idle');
    cards[i-1].classList.add('completed');
  }
  if (idx < cards.length) {
    cards[idx].classList.remove('idle');
    cards[idx].classList.add('active');
  }
  const arrows = document.querySelectorAll('#learningAgentFlow .agent-arrow');
  arrows.forEach((a, i) => {
    a.classList.remove('active','completed');
    if (i < idx) a.classList.add('completed');
    if (i === idx) a.classList.add('active');
  });
}

async function loadChatData() {
  try {
    const profile = await store.ensureProfile();
    if (!profile) {
      document.getElementById('chatArea').innerHTML = emptyStateHTML('👤', '请先创建学情画像',
        '前往AI做课助手创建画像后即可使用学习助手', '去创建', "navigateTo('course')");
      return;
    }

    // Load sessions
    const sessions = await api.listSessions(profile.id);
    const listEl = document.getElementById('chatSessionList');
    if (sessions.length > 0) {
      document.getElementById('chatSessionCount').textContent = sessions.length;
      listEl.innerHTML = sessions.map(s =>
        `<div class="tt-item" style="cursor:pointer" onclick="loadChatSession('${s.id}','${s.topic||''}')">
          <span class="tt-date">${fmtDate(s.created_at).slice(5,10)||''}</span>
          <span class="tt-content">${truncate(s.topic||'新会话', 20)}</span>
          <span class="tt-badge">${s.message_count||0}条</span>
        </div>`
      ).join('');
    }
  } catch (e) { /* ignore */ }
}

async function startNewChat() {
  chatSessionId = null;
  document.getElementById('chatArea').innerHTML = '<div style="text-align:center;padding:20px;color:rgba(255,255,255,.2);font-size:11px">新会话已创建，开始提问吧</div>';
  document.getElementById('chatInputArea').style.display = 'flex';
  document.getElementById('chatInput').focus();
  highlightLearningAgent(-1);
}

async function loadChatSession(sessionId, topic) {
  chatSessionId = sessionId;
  try {
    const session = await api.getSession(sessionId);
    const area = document.getElementById('chatArea');
    area.innerHTML = '';
    (session.messages || []).forEach(m => {
      area.innerHTML += `<div class="msg ${m.role}"><div>${marked.parse ? marked.parse(m.content) : m.content}</div><div class="msg-info">${m.agent ? 'Agent: '+m.agent : ''}${m.timestamp ? ' · '+fmtDate(m.timestamp) : ''}</div></div>`;
    });
    document.getElementById('chatInputArea').style.display = 'flex';
    area.scrollTop = area.scrollHeight;
    highlightLearningAgent(-1);
  } catch (e) {
    alert('加载会话失败: ' + e.message);
  }
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  const profile = store.profile;
  if (!profile) { alert('请先创建学情画像'); return; }

  const area = document.getElementById('chatArea');

  // Clear empty state, show input
  document.getElementById('chatInputArea').style.display = 'flex';

  // Add user message
  area.innerHTML += `<div class="msg user"><div>${escapeHtml(msg)}</div><div class="msg-info">你 · 刚刚</div></div>`;
  input.value = '';
  area.scrollTop = area.scrollHeight;

  // Show loading
  area.innerHTML += `<div class="msg assistant" id="chatLoadingMsg"><div>🤔 思考中...</div></div>`;
  area.scrollTop = area.scrollHeight;

  // Highlight routing agent
  highlightLearningAgent(0);

  try {
    const resp = await api.chat(profile.id, msg, chatSessionId);
    chatSessionId = resp.session_id;

    // Route based on agent
    const agentIdx = getLearningAgentIndex(resp.agent_route);

    // Simulate agent processing steps
    for (let i = 1; i <= agentIdx && i < LEARNING_AGENTS.length; i++) {
      await sleep(300);
      highlightLearningAgent(i);
    }

    // Remove loading
    const loadingMsg = document.getElementById('chatLoadingMsg');
    if (loadingMsg) loadingMsg.remove();

    // Add reply
    const replyHtml = marked.parse ? marked.parse(resp.reply) : resp.reply;
    area.innerHTML += `<div class="msg assistant"><div>${replyHtml}</div><div class="msg-info">${resp.agent_route||'知识答疑Agent'} · 刚刚</div></div>`;
    area.scrollTop = area.scrollHeight;

    // Complete agent flow
    highlightLearningAgent(LEARNING_AGENTS.length);

    // Refresh session list
    loadChatData();

  } catch (e) {
    const loadingMsg = document.getElementById('chatLoadingMsg');
    if (loadingMsg) loadingMsg.remove();
    area.innerHTML += `<div class="msg assistant"><div style="color:#ff5252">⚠️ ${e.message}</div></div>`;
    highlightLearningAgent(-1);
  }
}

function getLearningAgentIndex(agentName) {
  const map = {
    '问题路由Agent': 1, '导学追问Agent': 2, '知识答疑Agent': 3,
    '案例讲解Agent': 4, '学情诊断Agent': 5, '画像更新Agent': 6,
  };
  return map[agentName] || 3;
}

function openLearningAgentDrawer(idx) {
  const a = LEARNING_AGENTS.find(x => x.idx === idx);
  if (!a) return;
  const card = document.querySelector(`#learningAgentFlow .agent-card[data-idx="${idx}"]`);
  const status = card?.classList.contains('completed') ? '已完成' :
                 card?.classList.contains('active') ? '运行中' : '就绪';
  const sc = status === '已完成' ? '#00c853' : status === '运行中' ? '#4fc3f7' : 'rgba(255,255,255,.35)';

  document.getElementById('drIcon').textContent = ['🔀','🎓','📖','💼','🔬','🔄'][idx-1] || '🤖';
  document.getElementById('drNumber').textContent = String(idx).padStart(2,'0');
  document.getElementById('drCn').textContent = a.cn;
  document.getElementById('drEn').textContent = a.en;
  document.getElementById('drStatus').innerHTML = `<span style="color:${sc}">●</span> ${status}`;
  document.getElementById('drawerBody').innerHTML = `
    <div class="d-section"><div class="ds-title">🎯 职责</div><div class="ds-desc">${a.desc||'—'}</div></div>
    <div class="d-section"><div class="ds-title">📥 输入</div><div class="ds-tags">${(a.inp||[]).map(i => `<span class="ds-tag"><span class="tb">▹</span>${i}</span>`).join('')}</div></div>
    <div class="d-section"><div class="ds-title">📤 输出</div><div class="ds-tags">${(a.out||[]).map(o => `<span class="ds-tag"><span class="tb">▹</span>${o}</span>`).join('')}</div></div>`;
  document.getElementById('drawerOverlay').classList.add('active');
}
