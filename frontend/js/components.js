/**
 * 共享组件 — 可复用的UI模块
 */

// 格式化日期
function fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

// 截取文本
function truncate(str, len = 60) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '...' : str;
}

// Agent状态图标
function agentStatusIcon(status) {
  const icons = { idle: '○', running: '⟳', completed: '✓', failed: '✕', debating: '⚖' };
  return icons[status] || '○';
}

// 能力条渲染
function renderSkillBar(label, value, color) {
  const hue = color || `hsl(${value * 1.2 + 190}, 60%, 50%)`;
  return `
    <div class="ar">
      <span class="arn">${label}</span>
      <div class="art"><div class="arf" style="width:${value}%;background:${hue}"></div>
      <input type="range" min="0" max="100" value="${value}" onchange="window._updSkill && window._updSkill('${label}',this.value)"></div>
      <span class="arv">${value}</span>
    </div>`;
}

// Agent卡片渲染
function renderAgentCard(a, status = 'idle') {
  return `
    <div class="agent-card ${status}" onclick="openAgentDrawer(${a.idx},'${a.module||'course'}')" data-idx="${a.idx}">
      <div class="index">${String(a.idx).padStart(2,'0')}</div>
      <div class="info">
        <div class="cn">${a.cn||a.name}</div>
        <div class="en">${a.en||a.name}</div>
        <div class="desc">${a.desc||a.description||''}</div>
      </div>
      <div class="status-icon">${agentStatusIcon(status)}</div>
    </div>`;
}

// Agent箭头
function renderArrow(status = 'idle') {
  return `<div class="agent-arrow ${status}"><span class="chevron">▼</span></div>`;
}

// 诊断结果显示
function renderDiagnosis(p) {
  if (!p) return '';
  return `
    <div class="dc">
      <div class="dt">✦ 学情诊断报告</div>
      <div class="dr"><span class="dl">阶段</span><span class="dv">${p.stage||'未评估'}</span></div>
      <div class="dr"><span class="dl">评分</span><span class="dv">${p.score||0}</span></div>
      <div class="dr"><span class="dl">知识缺口</span><span class="dv">${p.gaps||'暂无'}</span></div>
      <div class="dr"><span class="dl">推荐方向</span><span class="dv">${p.direction||'待定'}</span></div>
      <div class="dtags">
        ${p.skills ? Object.entries(p.skills).slice(0,3).map(([k,v]) =>
          `<span class="dtag">▸ ${k} L${Math.floor(v/25)+1}</span>`
        ).join('') : ''}
      </div>
    </div>`;
}

// 加载动画
function loadingHTML(text = '处理中...', sub = '请稍候') {
  return `
    <div class="loading-center">
      <div class="spinner"></div>
      <div class="lt">${text}</div>
      <div class="ls">${sub}</div>
    </div>`;
}

// 空状态
function emptyStateHTML(icon, title, sub, btnText, btnAction) {
  return `
    <div class="empty-state">
      <div class="es-icon">${icon}</div>
      <div class="es-title">${title}</div>
      <div class="es-sub">${sub}</div>
      ${btnText ? `<button class="es-btn" onclick="${btnAction}">${btnText}</button>` : ''}
    </div>`;
}

// 学习轨迹渲染
function renderTrajectory(trajectory, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!trajectory || trajectory.length === 0) {
    el.innerHTML = '<div style="font-size:10px;color:rgba(255,255,255,.15);text-align:center;padding:6px">暂无学习记录</div>';
    return;
  }
  el.innerHTML = trajectory.slice(0, 10).map(t =>
    `<div class="tt-item">
      <span class="tt-date">${t.date||''}</span>
      <span class="tt-content">${t.content||t.module||''}</span>
      <span class="tt-badge">${t.ability||''}</span>
    </div>`
  ).join('');
}
