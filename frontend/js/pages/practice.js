/**
 * AI陪练助手页面
 *
 * 场景化实战演练：数据理解类、AI分析类、Prompt设计类、业务决策类
 */
let practiceSessionId = null;

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
          ${['训练规划','场景生成','过程评估','反馈优化','学情更新'].map((n, i) =>
            `<div class="agent-card idle"><div class="index">${String(i+1).padStart(2,'0')}</div><div class="info"><div class="cn">${n} Agent</div></div><div class="status-icon">○</div></div>`
            + (i < 4 ? '<div class="agent-arrow"><span class="chevron">▼</span></div>' : '')
          ).join('')}
        </div>
      </aside>
    </div>
  </div>`;

  loadPracticeHistory();
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

  html += `<div class="cc"><div class="ch"><span class="ci">🎯</span><span class="ct">${scenario.title||'实战题目'}</span><span class="cb">场景</span></div><div class="cbd"><div style="font-size:11px;line-height:1.7;color:rgba(255,255,255,.65)">${scenario.description||''}</div></div></div>`;

  // Data display
  if (scenario.data) {
    html += `<div class="cc"><div class="ch"><span class="ci">📊</span><span class="ct">参考数据</span><span class="cb">分析素材</span></div><div class="cbd">`;
    if (typeof scenario.data === 'object') {
      html += '<div style="font-size:10px;line-height:1.6;color:rgba(255,255,255,.5)"><pre style="font-family:inherit;white-space:pre-wrap">' +
        JSON.stringify(scenario.data, null, 2).replace(/\n/g,'<br>').replace(/ /g,'&nbsp;') +
        '</pre></div>';
    }
    html += '</div></div>';
  }

  // Questions
  if (scenario.questions && scenario.questions.length) {
    html += `<div class="cc"><div class="ch"><span class="ci">❓</span><span class="ct">问题</span><span class="cb">${scenario.questions.length}题</span></div><div class="cbd">`;
    scenario.questions.forEach((q, i) => {
      html += `<div style="font-size:10px;color:rgba(255,255,255,.65);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04)">
        <strong>Q${i+1}.</strong> ${q}
      </div>`;
    });
    html += '</div></div>';
  }

  // Answer area
  html += `<div class="cc"><div class="ch"><span class="ci">✍</span><span class="ct">你的回答</span></div><div class="cbd">
    <textarea id="practiceAnswer" placeholder="在此输入你的分析和回答..." style="width:100%;min-height:120px;padding:8px;border:1px solid rgba(79,195,247,.12);border-radius:6px;background:rgba(255,255,255,.03);color:#e8edf5;font-family:inherit;font-size:11px;resize:vertical;outline:none"></textarea>
    <button class="btn-primary" style="margin-top:6px" onclick="submitPractice()">📤 提交回答</button>
  </div></div>`;

  html += '</div>';
  content.innerHTML = html;
}

async function submitPractice() {
  const answer = document.getElementById('practiceAnswer')?.value?.trim();
  if (!answer || answer.length < 5) { alert('请先输入你的回答'); return; }
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
