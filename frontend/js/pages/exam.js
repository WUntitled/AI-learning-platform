/**
 * AI考试助手页面
 *
 * 智能出题 → 在线作答 → 自动评分 → 学情报告
 */
let currentExam = null;
let examAnswers = {};

function renderExamPage() {
  const main = document.getElementById('appMain');
  main.innerHTML = `
  <div class="page active" id="pageExam">
    <div class="panel-layout">
      <aside class="left-panel">
        <div class="panel-title">📝 考试管理 <span class="badge" id="examBadge">0</span></div>
        <button class="btn-primary" style="width:100%;padding:7px;font-size:11px" onclick="createNewExam()">📝 开始新考试</button>
        <div class="panel-title" style="margin-top:10px">📜 考试历史</div>
        <div id="examHistory" style="flex:1;overflow-y:auto;font-size:10px;display:flex;flex-direction:column;gap:3px">
          <div style="color:rgba(255,255,255,.15);text-align:center;padding:12px">暂无记录</div>
        </div>
      </aside>

      <main class="middle-panel">
        <div class="panel-title">📝 AI考试 <span class="badge" id="examStatus">准备就绪</span></div>
        <div id="examContent" style="flex:1;overflow-y:auto;display:flex;flex-direction:column">
          ${emptyStateHTML('📝', 'AI智能考试系统', '系统将根据你的学情画像，自动生成匹配的考试题目', '开始考试', 'createNewExam()')}
        </div>
      </main>

      <aside class="right-panel">
        <div class="panel-title">🤖 出题Agent <span class="badge">5个</span></div>
        <div id="examAgentFlow" style="display:flex;flex-direction:column;gap:2px">
          ${['考试蓝图','出题','答案评分','个性化组卷','质量审核'].map((n, i) =>
            `<div class="agent-card idle"><div class="index">${String(i+1).padStart(2,'0')}</div><div class="info"><div class="cn">${n} Agent</div></div><div class="status-icon">○</div></div>`
            + (i < 4 ? '<div class="agent-arrow"><span class="chevron">▼</span></div>' : '')
          ).join('')}
        </div>
      </aside>
    </div>
  </div>`;

  loadExamHistory();
}

async function createNewExam() {
  const profile = await store.ensureProfile();
  if (!profile) { alert('请先创建学情画像'); return; }

  const content = document.getElementById('examContent');
  content.innerHTML = loadingHTML('AI智能出题中...', '5个出题Agent协同工作');
  document.getElementById('examStatus').textContent = '出题中';

  // Animate exam agents
  animateExamAgents(async () => {
    try {
      const exam = await api.createExam(profile.id);
      currentExam = exam;
      examAnswers = {};
      renderExamQuestions(exam);
      document.getElementById('examStatus').textContent = `${exam.questions.length}题 · ${exam.blueprint?.duration_minutes||60}分钟`;
    } catch (e) {
      content.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><div class="es-title">出题失败</div><div class="es-sub">${e.message}</div></div>`;
      document.getElementById('examStatus').textContent = '失败';
    }
  });
}

function renderExamQuestions(exam) {
  const content = document.getElementById('examContent');
  if (!content) return;
  let html = '<div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:6px">';

  // Blueprint info
  const bp = exam.blueprint || {};
  html += `<div class="cc"><div class="ch"><span class="ci">📋</span><span class="ct">考试说明</span><span class="cb">${exam.questions.length}题</span></div><div class="cbd">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:10px;color:rgba(255,255,255,.5)">
      <div>目标: ${bp.objective||'—'}</div>
      <div>难度: ${bp.difficulty||'medium'}</div>
      <div>题量: ${bp.total_questions||exam.questions.length}题</div>
      <div>时长: ${bp.duration_minutes||60}分钟</div>
    </div>
  </div></div>`;

  // Questions
  (exam.questions||[]).forEach((q, i) => {
    html += `<div class="question-card">
      <div class="q-header">
        <span class="q-num">${i+1}</span>
        <span class="q-type">${q.type||'题'}</span>
        <span style="font-size:8px;padding:1px 6px;border-radius:4px;background:rgba(0,200,83,.06);color:#00c853">${q.difficulty||'medium'}</span>
        <span class="q-score">${q.score||10}分</span>
      </div>
      <div class="q-stem">${q.stem||''}</div>
      <div class="q-options">`;
    (q.options||[]).forEach((opt, oi) => {
      const optLetter = String.fromCharCode(65 + oi);
      const checked = examAnswers[q.id] === optLetter;
      html += `<input type="radio" name="q_${q.id}" id="q_${q.id}_${optLetter}" value="${optLetter}" ${checked?'checked':''} onchange="examAnswers['${q.id}']='${optLetter}'">
        <label for="q_${q.id}_${optLetter}">${opt}</label>`;
    });
    html += `</div></div>`;
  });

  html += '</div>';

  // Submit button
  html += `<div style="padding:8px 0"><button class="btn-primary" style="width:100%;padding:10px;font-size:13px" onclick="submitExamAnswers()">📤 提交答卷</button></div>`;

  content.innerHTML = html;
}

async function submitExamAnswers() {
  if (!currentExam) return;
  const unanswered = (currentExam.questions||[]).filter(q => !examAnswers[q.id]);
  if (unanswered.length > 0) {
    if (!confirm(`${unanswered.length}题尚未作答，确定提交吗？`)) return;
  }

  const content = document.getElementById('examContent');
  content.innerHTML = loadingHTML('AI评卷中...', '正在分析你的作答');
  document.getElementById('examStatus').textContent = '评卷中';

  try {
    const answers = (currentExam.questions||[]).map(q => ({
      question_id: q.id,
      answer: examAnswers[q.id] || '',
    }));

    const result = await api.submitExam(currentExam.id, answers);
    renderExamResult(result);
    document.getElementById('examStatus').textContent = '已完成';
    loadExamHistory();
  } catch (e) {
    content.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><div class="es-title">评卷失败</div><div class="es-sub">${e.message}</div></div>`;
  }
}

function renderExamResult(result) {
  const content = document.getElementById('examContent');
  if (!content) return;
  const scoring = result.scoring || {};
  const report = result.report || {};
  let html = '<div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:8px">';

  // Score card
  html += `<div class="cc"><div class="ch"><span class="ci">📊</span><span class="ct">考试成绩</span></div><div class="cbd" style="text-align:center;padding:16px">`;
  const passed = scoring.passed;
  html += `<div style="font-size:36px;font-weight:700;color:${passed?'#00c853':'#ff5252'}">${scoring.percentage||0}%</div>`;
  html += `<div style="font-size:13px;color:${passed?'rgba(0,200,83,.6)':'rgba(255,82,82,.6)'};margin-top:4px">${passed?'✅ 合格':'❌ 未合格'}</div>`;
  html += `<div style="font-size:11px;color:rgba(255,255,255,.35);margin-top:8px">${scoring.total_score||0}/${scoring.max_score||0} 分</div>`;
  html += '</div></div>';

  // Score details
  if (scoring.details && scoring.details.length) {
    html += `<div class="cc"><div class="ch"><span class="ci">🔍</span><span class="ct">答题详情</span></div><div class="cbd">`;
    scoring.details.forEach(d => {
      const correct = d.is_correct;
      html += `<div style="display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:10px">
        <span style="color:${correct?'#00c853':'#ff5252'};font-weight:700">${correct?'✓':'✕'}</span>
        <span style="flex:1;color:rgba(255,255,255,.5)">${truncate(d.question||d.question_id||'', 30)}</span>
        <span style="color:rgba(255,255,255,.3)">${d.score||0}/${d.max_score||0}</span>
      </div>`;
    });
    html += '</div></div>';
  }

  // Radar chart
  if (report.radar) {
    html += `<div class="cc"><div class="ch"><span class="ci">📈</span><span class="ct">能力雷达图</span></div><div class="cbd"><div><canvas id="examReportRadar" width="280" height="200"></canvas></div></div></div>`;
  }

  // Report suggestions
  if (report.suggestions && report.suggestions.length) {
    html += `<div class="cc"><div class="ch"><span class="ci">💡</span><span class="ct">培训建议</span></div><div class="cbd"><ul style="padding-left:16px;font-size:10px;line-height:1.8;color:rgba(255,255,255,.55)">`;
    report.suggestions.forEach(s => { html += `<li>${s}</li>`; });
    html += '</ul></div></div>';
  }

  // View full report
  html += `<div class="nb">
    <button class="btn-secondary" style="flex:1" onclick="navigateTo('report')">📊 查看完整学情报告</button>
    <button class="btn-secondary" style="flex:1" onclick="createNewExam()">🔄 重新考试</button>
  </div>`;
  html += '</div>';
  content.innerHTML = html;

  // Render radar
  setTimeout(() => {
    if (report.radar) {
      renderRadar('examReportRadar', report.radar.scores, '#4fc3f7', report.radar.dimensions);
    }
  }, 100);
}

function animateExamAgents(callback) {
  const cards = document.querySelectorAll('#examAgentFlow .agent-card');
  let idx = 0;
  function next() {
    if (idx >= cards.length) {
      cards.forEach(c => { c.classList.remove('active','idle'); c.classList.add('completed'); });
      if (callback) setTimeout(callback, 300);
      return;
    }
    cards.forEach(c => c.classList.remove('active','completed'));
    for (let i = 0; i < idx; i++) {
      cards[i].classList.remove('active','idle');
      cards[i].classList.add('completed');
    }
    if (idx < cards.length) {
      cards[idx].classList.remove('idle');
      cards[idx].classList.add('active');
    }
    setTimeout(() => {
      if (idx < cards.length) {
        cards[idx].classList.remove('active');
        cards[idx].classList.add('completed');
      }
      idx++;
      setTimeout(next, 300);
    }, 700);
  }
  next();
}

async function loadExamHistory() {
  try {
    const profile = await store.ensureProfile();
    if (!profile) return;
    const exams = await api.getExamHistory(profile.id);
    const el = document.getElementById('examHistory');
    const badge = document.getElementById('examBadge');
    if (!el) return;
    if (exams.length === 0) {
      el.innerHTML = '<div style="color:rgba(255,255,255,.15);text-align:center;padding:8px">暂无记录</div>';
      if (badge) badge.textContent = '0';
      return;
    }
    if (badge) badge.textContent = exams.length;
    el.innerHTML = exams.slice(0, 8).map(e =>
      `<div class="tt-item" style="cursor:pointer" onclick="viewExamReport('${e.id}')">
        <span class="tt-date">${fmtDate(e.created_at).slice(5,10)}</span>
        <span class="tt-content">${e.status||'完成'}</span>
        <span class="tt-badge">${e.scoring?.percentage||'?'}%</span>
      </div>`
    ).join('');
  } catch (e) { /* ignore */ }
}

async function viewExamReport(examId) {
  try {
    const exam = await api.getExam(examId);
    if (exam.status === 'graded') {
      renderExamResult({ scoring: exam.scoring, report: exam.report });
    } else {
      alert('该考试尚未完成评分');
    }
  } catch (e) {
    alert('加载失败: ' + e.message);
  }
}
