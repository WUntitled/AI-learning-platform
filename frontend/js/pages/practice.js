/**
 * AI陪练助手页面
 *
 * 场景化实战演练：数据理解类、AI分析类、Prompt设计类、业务决策类
 */
let practiceSessionId = null;

const PRACTICE_AGENTS = [
  { idx: 1, cn: '训练规划 Agent', en: 'Training Planner', desc: '根据学习者画像和实战目标，制定个性化的训练计划',
    inp: ['学习者画像','实战目标','历史表现'], out: ['训练计划','评估指标','难度建议'] },
  { idx: 2, cn: '场景生成 Agent', en: 'Scenario Generator', desc: '根据训练计划生成真实的业务实战场景',
    inp: ['训练计划','业务知识库'], out: ['实战场景','背景数据','任务描述'] },
  { idx: 3, cn: '过程评估 Agent', en: 'Process Evaluator', desc: '实时评估学习者的回答质量和分析能力',
    inp: ['用户回答','场景答案','评分标准'], out: ['能力评分','维度分析','改进建议'] },
  { idx: 4, cn: '反馈优化 Agent', en: 'Feedback Optimizer', desc: '根据评估结果生成针对性的优化反馈',
    inp: ['评估结果','用户画像'], out: ['优化建议','学习资源推荐','练习调整'] },
  { idx: 5, cn: '学情更新 Agent', en: 'Profile Updater', desc: '根据实战表现更新学习者的能力画像',
    inp: ['实战表现','评估报告'], out: ['画像更新','能力变化','新学习路径'] },
];

function renderPracticePage() {
  const main = document.getElementById('appMain');
  main.innerHTML = `
  <div class="page active" id="pagePractice">
    <div class="panel-layout">
      <aside class="left-panel">
        <div class="panel-title">⚡ 实战类型 <span class="badge">4种</span></div>
        <div id="practiceTypeList" style="display:flex;flex-direction:column;gap:4px">
          ${['数据理解类','AI分析类','Prompt设计类','业务决策类'].map((t, i) =>
            `<button class="btn-secondary" style="text-align:left;padding:8px 10px;font-size:11px;width:100%" onclick="startPractice('${t}')">
              ${['📊','🤖','✍','🎯'][i]} ${t}
            </button>`
          ).join('')}
        </div>
        <div class="panel-title" style="margin-top:12px">📜 练习历史</div>
        <div id="practiceHistory" style="flex:1;overflow-y:auto;font-size:10px;display:flex;flex-direction:column;gap:3px">
          <div style="color:rgba(255,255,255,.15);text-align:center;padding:12px">暂无记录</div>
        </div>
      </aside>

      <main class="middle-panel">
        <div class="panel-title">⚡ AI陪练 <span class="badge" id="practiceStatus">选择场景</span></div>
        <div id="practiceContent" style="flex:1;overflow-y:auto;display:flex;flex-direction:column">
          ${emptyStateHTML('⚡', '选择实战类型', '从左侧选择一种实战类型开始演练', '开始练习', "startPractice('数据理解类')")}
        </div>
      </main>

      <aside class="right-panel">
        <div class="panel-title">🤖 陪练Agent <span class="badge">模拟</span></div>
        <div id="practiceAgentFlow" style="display:flex;flex-direction:column;gap:2px">
          ${PRACTICE_AGENTS.map((a, i) =>
            `<div class="agent-card idle" data-idx="${a.idx}" data-module="practice"><div class="index">${String(a.idx).padStart(2,'0')}</div><div class="info"><div class="cn">${a.cn}</div><div class="en">${a.en}</div></div><div class="status-icon">○</div></div>`
            + (i < PRACTICE_AGENTS.length - 1 ? '<div class="agent-arrow"><span class="chevron">▼</span></div>' : '')
          ).join('')}
        </div>
      </aside>
    </div>
  </div>`;

  // Add click handlers for agent cards
  document.querySelectorAll('#practiceAgentFlow .agent-card').forEach(el => {
    el.addEventListener('click', () => openPracticeAgentDrawer(parseInt(el.dataset.idx)));
  });

  loadPracticeHistory();
}

function openPracticeAgentDrawer(idx) {
  const a = PRACTICE_AGENTS.find(x => x.idx === idx);
  if (!a) return;
  const card = document.querySelector(`#practiceAgentFlow .agent-card[data-idx="${idx}"]`);
  const status = card?.classList.contains('completed') ? '已完成' :
                 card?.classList.contains('active') ? '运行中' : '就绪';
  const sc = status === '已完成' ? '#00c853' : status === '运行中' ? '#4fc3f7' : 'rgba(255,255,255,.35)';

  document.getElementById('drIcon').textContent = ['📋','🎯','📊','💡','🔄'][idx-1] || '🤖';
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

async function startPractice(type) {
  const profile = await store.ensureProfile();
  if (!profile) { alert('请先创建学情画像'); return; }

  const content = document.getElementById('practiceContent');
  content.innerHTML = loadingHTML('正在生成实战场景...', type);
  document.getElementById('practiceStatus').textContent = '生成中';

  try {
    const resp = await api.generateScenario(profile.id, type);
    practiceSessionId = resp.session_id;
    renderPracticeScenario(resp.scenario);
    document.getElementById('practiceStatus').textContent = type;
  } catch (e) {
    content.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><div class="es-title">生成失败</div><div class="es-sub">${e.message}</div></div>`;
  }
}

function renderPracticeScenario(scenario) {
  const content = document.getElementById('practiceContent');
  if (!content) return;
  let html = '<div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:8px">';

  // Title section
  html += `<div class="cc"><div class="ch"><span class="ci">🎯</span><span class="ct">${scenario.title||'实战题目'}</span><span class="cb">场景</span></div><div class="cbd"><div style="font-size:11px;line-height:1.7;color:rgba(255,255,255,.65)">${scenario.description||''}</div></div></div>`;

  // Questions
  if (scenario.questions && scenario.questions.length) {
    html += `<div class="cc"><div class="ch"><span class="ci">❓</span><span class="ct">问题</span><span class="cb">${scenario.questions.length}题</span></div><div class="cbd">`;
    scenario.questions.forEach((q, i) => {
      html += `<div style="font-size:10px;color:rgba(255,255,255,.65);padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04)">
        <strong>Q${i+1}.</strong> ${q}
      </div>`;
    });
    html += '</div></div>';
  }

  // Answer area - ensure submit button is clearly visible
  html += `<div class="cc" style="flex-shrink:0"><div class="ch"><span class="ci">✍</span><span class="ct">你的回答</span></div><div class="cbd">
    <textarea id="practiceAnswer" placeholder="在此输入你的分析和回答..." style="width:100%;min-height:120px;padding:8px;border:1px solid rgba(79,195,247,.12);border-radius:6px;background:rgba(255,255,255,.03);color:#e8edf5;font-family:inherit;font-size:11px;resize:vertical;outline:none"></textarea>
    <button class="btn-primary" style="margin-top:6px;width:100%" onclick="submitPractice()">📤 提交回答</button>
  </div></div>`;

  html += '</div>';
  content.innerHTML = html;
}

async function submitPractice() {
  const answer = document.getElementById('practiceAnswer')?.value?.trim();
  if (!answer) { alert('请先输入你的回答'); return; }
  if (!practiceSessionId) { alert('请先开始一个实战场景'); return; }

  const content = document.getElementById('practiceContent');
  content.innerHTML = loadingHTML('AI评估中...', '正在分析你的回答');

  try {
    const resp = await api.submitPractice(practiceSessionId, [{ question_index: 0, answer: answer }]);
    renderPracticeResult(resp.evaluation, resp.score);
  } catch (e) {
    content.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><div class="es-title">评估失败</div><div class="es-sub">${e.message}</div></div>`;
  }
}

function renderPracticeResult(evaluation, score) {
  const content = document.getElementById('practiceContent');
  if (!content) return;
  let html = '<div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:8px">';

  html += `<div class="cc"><div class="ch"><span class="ci">📊</span><span class="ct">评估结果</span><span class="cb">${score||evaluation?.score||0}分</span></div><div class="cbd">`;
  html += `<div style="font-size:14px;font-weight:700;margin-bottom:8px">总得分: <span style="color:${(score||0)>=60?'#00c853':'#ffab00'}">${score||evaluation?.score||0}</span></div>`;
  html += `<div style="font-size:11px;color:rgba(255,255,255,.6);line-height:1.7">${evaluation?.feedback||'评估完成'}</div>`;
  html += '</div></div>';

  if (evaluation?.dimensions) {
    html += `<div class="cc"><div class="ch"><span class="ci">📈</span><span class="ct">维度评分</span></div><div class="cbd">`;
    evaluation.dimensions.forEach(d => {
      html += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
        <span style="font-size:10px;color:rgba(255,255,255,.5);min-width:64px">${d.name}</span>
        <div style="flex:1;height:4px;background:rgba(255,255,255,.04);border-radius:2px;overflow:hidden">
          <div style="height:100%;width:${d.score}%;background:${d.score>=60?'#4fc3f7':'#ffab00'};border-radius:2px"></div>
        </div>
        <span style="font-size:10px;color:${d.score>=60?'#4fc3f7':'#ffab00'};min-width:20px;text-align:right">${d.score}</span>
      </div>`;
    });
    html += '</div></div>';
  }

  if (evaluation?.suggestions?.length) {
    html += `<div class="cc"><div class="ch"><span class="ci">💡</span><span class="ct">改进建议</span></div><div class="cbd"><ul style="padding-left:16px;font-size:10px;line-height:1.8;color:rgba(255,255,255,.55)">`;
    evaluation.suggestions.forEach(s => { html += `<li>${s}</li>`; });
    html += '</ul></div></div>';
  }

  html += `<div class="nb"><button class="btn-secondary" style="flex:1" onclick="startPractice('${document.getElementById('practiceStatus')?.textContent||'数据理解类'}')">🔄 再练一次</button>
    <button class="btn-secondary" style="flex:1" onclick="renderPracticePage()">📋 返回列表</button></div>`;
  html += '</div>';
  content.innerHTML = html;

  loadPracticeHistory();
}

async function loadPracticeHistory() {
  try {
    const profile = await store.ensureProfile();
    if (!profile) return;
    const history = await api.getPracticeHistory(profile.id);
    const el = document.getElementById('practiceHistory');
    if (!el) return;
    if (history.length === 0) {
      el.innerHTML = '<div style="color:rgba(255,255,255,.15);text-align:center;padding:8px">暂无记录</div>';
      return;
    }
    el.innerHTML = history.slice(0, 8).map(h =>
      `<div class="tt-item" style="cursor:pointer" onclick="showPracticeDetail('${h.id}')">
        <span class="tt-date">${fmtDate(h.created_at).slice(5,10)}</span>
        <span class="tt-content">${truncate(h.scenario_title||h.scenario_type, 14)}</span>
        <span class="tt-badge">${h.score||'?'}分</span>
      </div>`
    ).join('');
  } catch (e) { /* ignore */ }
}

async function showPracticeDetail(sessionId) {
  // Simple: reload the page and try to view
  alert('查看详情功能待完善');
}
