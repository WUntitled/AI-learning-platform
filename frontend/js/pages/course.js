/**
 * AI做课助手页面
 *
 * 左面板: 学情画像构建 + 雷达图
 * 中面板: 课程生成 + 课程内容展示
 * 右面板: 多Agent协同流程可视化
 */

// 渲染一道选择题
function renderQuizQuestion(q) {
  const letters = ['A', 'B', 'C', 'D'];
  return `
    <div style="background:rgba(255,255,255,.02);border:1px solid rgba(79,195,247,.08);border-radius:6px;padding:6px 8px">
      <div style="font-size:10px;color:rgba(255,255,255,.65);margin-bottom:4px;line-height:1.4">${q.question}</div>
      <div style="display:flex;flex-direction:column;gap:2px">
        ${q.options.map((opt, oi) => `
          <label style="display:flex;align-items:center;gap:6px;padding:3px 6px;border-radius:4px;cursor:pointer;transition:all .15s;font-size:9px;color:rgba(255,255,255,.45);background:rgba(255,255,255,.015);border:1px solid transparent" onmouseover="this.style.borderColor='rgba(79,195,247,.2)';this.style.background='rgba(79,195,247,.04)'" onmouseout="if(!this.querySelector('input').checked){this.style.borderColor='transparent';this.style.background='rgba(255,255,255,.015)'}">
            <input type="radio" name="quiz_${q.id}" value="${oi}" style="accent-color:#4fc3f7" onchange="document.querySelectorAll('label:has(input[name=&quot;quiz_${q.id}&quot;])').forEach(function(l){l.style.background='rgba(255,255,255,.015)';l.style.borderColor='transparent';l.style.color='rgba(255,255,255,.45)'});this.parentElement.style.background='rgba(79,195,247,.08)';this.parentElement.style.borderColor='rgba(79,195,247,.25)';this.parentElement.style.color='#4fc3f7'">
            <span>${letters[oi]}. ${opt}</span>
          </label>
        `).join('')}
      </div>
    </div>`;
}

// Agent定义（与后端同步）
const COURSE_AGENTS = [
  { idx: 1, cn: '学情诊断 Agent', en: 'Diagnosis Agent', desc: '分析用户输入，判断能力阶段与知识水平',
    inp: ['岗位','经验','AI背景','测试结果'], out: ['学习阶段评估','能力评分','知识缺口','课程方向'] },
  { idx: 2, cn: '画像构建 Agent', en: 'Profile Builder', desc: '生成结构化学习画像与能力标签',
    inp: ['诊断报告','岗位模型','用户信息'], out: ['能力标签体系','知识水平评分','学习目标','画像报告'] },
  { idx: 3, cn: '课程规划 Agent', en: 'Curriculum Planner', desc: '设计课程体系结构与学习路径',
    inp: ['学习画像','能力标签','知识图谱'], out: ['课程结构','章节顺序','学习路径','技能树'] },
  { idx: 4, cn: '内容生成 Agent', en: 'Content Generator', desc: '生成知识点、教程文档、实战任务',
    inp: ['课程规划','知识图谱'], out: ['知识点卡片','教程文档','实战任务','练习题'] },
  { idx: 5, cn: '案例设计 Agent', en: 'Case Designer', desc: '设计符合岗位的真实业务案例',
    inp: ['课程内容','岗位场景','业务数据'], out: ['案例背景','模拟数据','任务清单','评价标准'] },
  { idx: 6, cn: '课程审核 Agent', en: 'Quality Reviewer', desc: '审核课程质量与业务真实性',
    inp: ['课程内容','学习者画像','质量标准'], out: ['审核报告','修改建议','质量评分','课程包'] },
];

let courseGenerated = false;

// ================================================================
// 基础能力测试题目（共8题，每题4选项）
// 4个维度：业务理解、数据分析、AI应用、经营决策
// ================================================================
const QUIZ_QUESTIONS = [
  // 业务理解 (dimension: 'business') - Q1~Q2
  {
    id: 'q1', dimension: 'business', question: 'GMV下降时，以下哪种分析思路最合理？',
    options: ['直接降低售价来提升销量', '从流量、转化率、客单价三个维度拆解分析', '更换所有商品品类', '盲目增加广告投放预算'],
    correct: 1, // 0-indexed
  },
  {
    id: 'q2', dimension: 'business', question: '电商运营中，"漏斗分析"主要用于分析什么？',
    options: ['商品价格变化趋势', '用户从浏览到购买的转化路径', '竞争对手的营销策略', '库存周转率'],
    correct: 1,
  },
  // 数据分析 (dimension: 'dataAnalysis') - Q3~Q4
  {
    id: 'q3', dimension: 'dataAnalysis', question: '同比和环比的区别是什么？',
    options: ['同比是比去年同期，环比是比上个月/周期', '同比是比上个月，环比是比去年同期', '两者含义相同', '同比是比目标值，环比比实际值'],
    correct: 0,
  },
  {
    id: 'q4', dimension: 'dataAnalysis', question: '以下哪个指标最能反映用户粘性？',
    options: ['客单价', '复购率', '转化率', '退款率'],
    correct: 1,
  },
  // AI应用 (dimension: 'aiApplication') - Q5~Q6
  {
    id: 'q5', dimension: 'aiApplication', question: '一个好的Prompt（提示词）应包含哪些核心要素？',
    options: ['角色设定、任务描述、约束条件、输出格式', '只有任务描述', '只有角色设定', '随机关联词组合'],
    correct: 0,
  },
  {
    id: 'q6', dimension: 'aiApplication', question: '在AI辅助数据分析中，以下哪种做法最有效？',
    options: ['完全依赖AI给出结论', '结合业务知识，用AI辅助验证假设', '从不使用AI工具', '直接复制AI的回答'],
    correct: 1,
  },
  // 经营决策 (dimension: 'decision') - Q7~Q8
  {
    id: 'q7', dimension: 'decision', question: '预算有限时，你会如何分配营销预算？',
    options: ['全部投放在单一渠道', '根据历史ROI数据，分配到表现最好的渠道组合', '平均分配到所有渠道', '只投放在最便宜的渠道'],
    correct: 1,
  },
  {
    id: 'q8', dimension: 'decision', question: '某商品A毛利率高但销量低，商品B毛利率低但销量高，最佳策略是？',
    options: ['只卖商品A', '只卖商品B', '组合销售，用A带动利润、B带动流量', '两个都不卖'],
    correct: 2,
  },
];

// 计算测试得分
function calculateQuizSkills() {
  const dims = ['business', 'dataAnalysis', 'aiApplication', 'decision'];
  const results = { business: 0, dataAnalysis: 0, aiApplication: 0, decision: 0 };

  QUIZ_QUESTIONS.forEach(q => {
    const selected = document.querySelector(`input[name="quiz_${q.id}"]:checked`);
    if (selected && parseInt(selected.value) === q.correct) {
      results[q.dimension] = (results[q.dimension] || 0) + 1;
    }
  });

  // 每题正确 +30分，基础分30分
  const skills = {};
  dims.forEach(dim => {
    const correctCount = results[dim] || 0;
    skills[dim] = 30 + correctCount * 30; // 0→30, 1→60, 2→90
  });
  // prompt和continuous保持默认值
  skills.prompt = 50;
  skills.continuous = 50;
  return skills;
}

function renderCoursePage() {
  const main = document.getElementById('appMain');
  main.innerHTML = `
  <div class="page active" id="pageCourse">
    <div class="panel-layout">
      <!-- LEFT: 学情画像 -->
      <aside class="left-panel" id="courseLeft">
        <div class="panel-title">🧑 学习者画像 <span class="badge" id="courseProfileStatus">加载中</span></div>
        <div id="courseProfileContent">
          <div class="loading-center" style="min-height:200px">
            <div class="spinner"></div>
            <div class="lt" style="font-size:11px">加载学情数据...</div>
          </div>
        </div>
      </aside>

      <!-- MIDDLE: 课程内容 -->
      <main class="middle-panel" id="courseMiddle">
        <div class="panel-title">📚 AI个性化课程生成 <span class="badge" id="courseStatus">待生成</span></div>
        <div id="courseContentArea" style="flex:1;display:flex;flex-direction:column"></div>
      </main>

      <!-- RIGHT: Agent流程 -->
      <aside class="right-panel" id="courseRight">
        <div class="panel-title">🤖 协同流程 <span class="badge" id="courseFlowStatus">就绪</span></div>
        <div class="flow-progress">
          <span style="font-size:9px;color:rgba(255,255,255,.25);min-width:32px">进度</span>
          <div class="track"><div class="fill" id="courseProgressFill" style="width:0%"></div></div>
          <span class="pct" id="courseProgressPct">0%</span>
        </div>
        <div class="agent-flow" id="courseAgentFlow"></div>
      </aside>
    </div>
  </div>`;

  renderCourseAgents();
  loadCourseData();
}

function renderCourseAgents() {
  const container = document.getElementById('courseAgentFlow');
  container.innerHTML = COURSE_AGENTS.map((a, i) =>
    renderAgentCard({...a, module: 'course'}, 'idle') +
    (i < COURSE_AGENTS.length - 1 ? renderArrow() : '')
  ).join('');
  // Add click handlers
  container.querySelectorAll('.agent-card').forEach(el => {
    el.addEventListener('click', () => {
      const idx = parseInt(el.dataset.idx);
      openCourseAgentDrawer(idx);
    });
  });
}

async function loadCourseData() {
  try {
    const profile = await store.ensureProfile();
    const contentEl = document.getElementById('courseProfileContent');
    const statusEl = document.getElementById('courseProfileStatus');

    if (!profile) {
      statusEl.textContent = '未创建';
      contentEl.innerHTML = emptyStateHTML('👤', '创建学情画像',
        '请先填写学习者信息，生成个性化培训课程',
        '📝 创建学情画像', 'openCourseProfileModal()');
      const courseArea = document.getElementById('courseContentArea');
      courseArea.innerHTML = emptyStateHTML('📚', '等待学情画像',
        '请先创建学情画像以生成个性化课程',
        '开始创建', 'openCourseProfileModal()');
      return;
    }

    statusEl.textContent = '已构建';
    contentEl.innerHTML = renderProfileContent(profile);

    // 检查是否已有课程
    const courses = await api.getCoursesByProfile(profile.id);
    if (courses.length > 0) {
      renderCourseContent(courses[0]);
    } else {
      const courseArea = document.getElementById('courseContentArea');
      courseArea.innerHTML = emptyStateHTML('📚', '生成个性化培训课程',
        '点击下方按钮，6个智能体将协同为你生成课程',
        '🚀 开始生成课程', 'startCourseGeneration()');
      document.getElementById('courseStatus').textContent = '待生成';
    }
  } catch (e) {
    console.error('Load course error:', e);
  }
}

function renderProfileContent(p) {
  return `
    <div class="profile-card">
      <div class="profile-avatar">
        <span>${p.name?.charAt(0) || '?'}</span>
        <span class="level-badge">${(p.aiLevel_label||'L2').replace('L','')}</span>
      </div>
      <div class="profile-name">${p.name||'学习者'}</div>
      <div class="profile-role">${p.role||'业务分析师'} · ${p.stage||'初级'}</div>
      <div class="profile-stats">
        <div class="stat-item"><div class="label">AI能力</div><div class="value">${p.aiLevel_label||'L2'} <span class="level">${p.aiLabel||'基础'}</span></div></div>
        <div class="stat-item"><div class="label">业务分析</div><div class="value">${p.bizLevel||'L2'} <span class="level">${p.bizLabel||'独立'}</span></div></div>
      </div>
    </div>
    ${p.stage ? `<div class="diag-result"><div class="dc">${renderDiagnosis(p)}</div></div>` : ''}
    <button class="btn-secondary" style="width:100%;padding:5px;font-size:10px" onclick="openCourseProfileModal(true)">✏️ 修改画像</button>
    <div class="radar-section">
      <div class="panel-title" style="border:none;padding-bottom:3px;font-size:9px">📊 能力雷达图</div>
      <div class="radar-container"><canvas id="courseRadar" width="180" height="180"></canvas></div>
      <div class="radar-legend" id="courseRadarLegend"></div>
    </div>
    <div id="courseTrajectoryArea" style="margin-top:4px">
      <div class="panel-title" style="border:none;padding-bottom:4px;font-size:9px">📈 学习轨迹</div>
      <div class="trajectory-timeline" id="courseTrajectory"></div>
    </div>`;
}

async function startCourseGeneration() {
  if (courseGenerated) return;
  const profile = store.profile;
  if (!profile) { alert('请先创建学情画像'); return; }

  const area = document.getElementById('courseContentArea');
  area.innerHTML = loadingHTML('智能体协同生成课程中...', '6个Agent正在协同运作');
  document.getElementById('courseStatus').textContent = '课程生成中';
  document.getElementById('courseFlowStatus').textContent = '运行中...';

  // 运行Agent动画
  animateCourseAgents(async () => {
    try {
      const course = await api.generateCourse(profile.id);
      store.courseId = course.id;
      renderCourseContent(course);
      document.getElementById('courseStatus').textContent = '已生成';
      document.getElementById('courseFlowStatus').textContent = '已完成';
      courseGenerated = true;
    } catch (e) {
      area.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><div class="es-title">生成失败</div><div class="es-sub">${e.message}</div></div>`;
      document.getElementById('courseFlowStatus').textContent = '失败';
    }
  });
}

function renderCourseContent(course) {
  const d = course;
  const area = document.getElementById('courseContentArea');
  if (!area) return;

  let html = '<div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:6px;padding-right:2px">';

  // Skill tree
  if (d.skill_tree) {
    html += `<div class="cc"><div class="ch"><span class="ci">🌳</span><span class="ct">个性化技能树</span><span class="cb">能力图谱</span></div><div class="cbd"><div class="st"><div class="sr">🌿 ${d.skill_tree.root||'能力体系'}</div><div class="sc">`;
    (d.skill_tree.children||[]).forEach(c => {
      html += `<div class="si"><span class="sd"></span><span>${c.name}</span><span class="sl">${c.level||''}</span></div>`;
    });
    html += '</div></div></div></div>';
  }

  // Learning path
  if (d.learning_path && d.learning_path.length) {
    html += `<div class="cc"><div class="ch"><span class="ci">🗺️</span><span class="ct">学习路径规划</span><span class="cb">时间轴</span></div><div class="cbd"><div class="pt">`;
    d.learning_path.forEach((p, i) => {
      html += `<div class="pp"><div class="pn">${i+1}</div><div class="pb"><div class="ptit">${p.phase||'阶段'+(i+1)}：${p.title||''}</div><div class="pdesc">${p.desc||''}</div><div class="psk">${(p.skills||[]).map(s => `<span>${s}</span>`).join('')}</div></div></div>`;
    });
    html += '</div></div></div>';
  }

  // Knowledge cards
  if (d.knowledge_cards && d.knowledge_cards.length) {
    (d.knowledge_cards||[]).forEach(k => {
      html += `<div class="cc"><div class="ch"><span class="ci">📘</span><span class="ct">技能知识卡</span><span class="cb">知识点</span></div><div class="cbd"><div style="font-size:12px;font-weight:600;color:rgba(255,255,255,.65);margin-bottom:6px">${k.title||''}</div><div class="ks">`;
      if (k.concept) html += `<div class="kse"><div class="ksl">概念</div><div class="kst">${k.concept}</div></div>`;
      if (k.formula) html += `<div class="kf">${k.formula}</div>`;
      if (k.bizExp) html += `<div class="kse"><div class="ksl">业务解释</div><div class="kst">${k.bizExp}</div></div>`;
      if (k.mistake) html += `<div class="kse"><div class="ksl">常见错误</div><div class="kst">${k.mistake}</div></div>`;
      html += '</div></div></div>';
    });
  }

  // Tasks
  if (d.tasks && d.tasks.length) {
    (d.tasks||[]).forEach(t => {
      html += `<div class="cc"><div class="ch"><span class="ci">⚔️</span><span class="ct">实战任务</span><span class="cb">项目制学习</span></div><div class="cbd"><div style="margin-bottom:6px"><strong>${t.title||''}</strong></div>`;
      if (t.bg) html += `<div style="font-size:10px;color:rgba(255,255,255,.45);margin-bottom:4px">📋 ${t.bg}</div>`;
      if (t.goal) html += `<div style="font-size:10px;color:rgba(255,255,255,.45);margin-bottom:4px">🎯 ${t.goal}</div>`;
      if (t.steps) html += `<div style="font-size:10px;color:rgba(255,255,255,.35)">步骤：${(t.steps||[]).join(' → ')}</div>`;
      if (t.evaluation) html += `<div style="font-size:9px;color:rgba(79,195,247,.4);margin-top:4px">评分标准：${(t.evaluation||[]).join(' | ')}</div>`;
      html += '</div></div>';
    });
  }

  // Cases
  if (d.cases && d.cases.length) {
    (d.cases||[]).forEach(cs => {
      html += `<div class="cc"><div class="ch"><span class="ci">💼</span><span class="ct">专家案例</span><span class="cb">实战参考</span></div><div class="cbd"><div style="font-size:11px;font-weight:600;color:rgba(79,195,247,.5);margin-bottom:6px">${cs.title||''}</div>`;
      if (cs.steps) {
        const colors = ['#4fc3f7','#7c4dff','#ffab00','#00c853'];
        const icons = ['🔍','📊','💡','✅'];
        html += '<div style="display:flex;flex-direction:column;gap:4px">';
        (cs.steps||[]).forEach((s, i) => {
          html += `<div style="display:flex;gap:8px;padding:5px 8px;background:rgba(255,255,255,.01);border-radius:6px;border-left:2px solid ${colors[i%4]}"><span style="width:18px;height:18px;min-width:18px;border-radius:50%;background:${colors[i%4]};color:#fff;font-size:8px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">${i+1}</span><div><div style="font-size:8px;font-weight:600;color:${colors[i%4]};margin-bottom:1px">${icons[i%4]} ${s.label||''}</div><div style="font-size:10px;color:rgba(255,255,255,.5)">${s.desc||s.c||''}</div></div></div>`;
        });
        html += '</div>';
      }
      html += '</div></div>';
    });
  }

  html += '</div>';

  // Navigation
  html += `<div class="nb">
    <a onclick="navigateTo('learning')">💬 进入AI学习助手</a>
    <a onclick="navigateTo('practice')">⚡ 进入AI陪练助手</a>
    <a onclick="navigateTo('exam')">📝 进入AI考试助手</a>
  </div>`;

  area.innerHTML = html;
}

function animateCourseAgents(callback) {
  const cards = document.querySelectorAll('#courseAgentFlow .agent-card');
  const arrows = document.querySelectorAll('#courseAgentFlow .agent-arrow');
  const total = cards.length;
  let idx = 0;

  function next() {
    if (idx >= total) {
      cards.forEach(c => { c.classList.remove('active','idle'); c.classList.add('completed'); });
      updateCourseProgress(100);
      if (callback) setTimeout(callback, 400);
      return;
    }
    cards.forEach(c => c.classList.remove('active','completed'));
    arrows.forEach(a => a.classList.remove('active','completed'));
    for (let i = 0; i < idx; i++) {
      cards[i].classList.remove('active','idle');
      cards[i].classList.add('completed');
      if (arrows[i]) { arrows[i].classList.remove('active'); arrows[i].classList.add('completed'); }
    }
    cards[idx].classList.remove('idle');
    cards[idx].classList.add('active');
    if (arrows[idx]) arrows[idx].classList.add('active');
    updateCourseProgress(Math.round(((idx + 1) / total) * 100));
    document.getElementById('courseFlowStatus').textContent = `运行中 ${idx+1}/${total}`;

    setTimeout(() => {
      cards[idx].classList.remove('active');
      cards[idx].classList.add('completed');
      if (arrows[idx]) { arrows[idx].classList.remove('active'); arrows[idx].classList.add('completed'); }
      idx++;
      setTimeout(next, 200);
    }, 1000);
  }
  next();
}

function updateCourseProgress(pct) {
  const fill = document.getElementById('courseProgressFill');
  const label = document.getElementById('courseProgressPct');
  if (fill) fill.style.width = pct + '%';
  if (label) label.textContent = pct + '%';
}

// 学情画像弹窗
let profileModalEditing = false;

function openCourseProfileModal(isEdit) {
  profileModalEditing = isEdit === true;
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.id = 'courseProfileModal';
  overlay.onclick = (e) => { if (e.target === overlay) closeCourseProfileModal(); };

  const p = store.profile || {};
  overlay.innerHTML = `
    <div class="modal-box" onclick="event.stopPropagation()">
      <div class="modal-hd">
        <div class="mh-title">${profileModalEditing ? '✏️ 修改学情画像' : '📝 创建学情画像'}</div>
        <button class="mh-close" onclick="closeCourseProfileModal()">✕</button>
      </div>
      <div class="modal-scroll">
        <div class="fg">
          <div class="fgl">👤 姓名</div>
          <input type="text" id="cpName" value="${p.name||''}" placeholder="请输入学习者姓名">
        </div>
        <div class="fg">
          <div class="fgl">📋 岗位类型</div>
          <select id="cpRole">
            <option value="电商运营" ${p.role==='电商运营'?'selected':''}>电商运营</option>
            <option value="业务分析师" ${(!p.role||p.role==='业务分析师')?'selected':''}>业务分析师</option>
            <option value="产品经理" ${p.role==='产品经理'?'selected':''}>产品经理</option>
          </select>
        </div>
        <div class="fg">
          <div class="fgl">⏳ 工作年限</div>
          <div class="rg">
            ${['1年以下','1-3年','3-5年','5年以上'].map(v =>
              `<input type="radio" name="cpExp" id="cpe${v}" value="${v}" ${(p.experience||'1-3年')===v?'checked':''}><label for="cpe${v}">${v}</label>`
            ).join('')}
          </div>
        </div>
        <div class="fg">
          <div class="fgl">🛒 业务经验</div>
          <textarea id="cpBiz" placeholder="如：负责618活动运营2年，熟悉天猫后台数据分析">${p.ecommerce_exp||''}</textarea>
        </div>
        <div class="fg">
          <div class="fgl">🤖 AI使用经验</div>
          <div class="rg">
            ${['未使用','基础使用','熟练使用'].map(v =>
              `<input type="radio" name="cpAi" id="cpa${v}" value="${v}" ${(p.ai_level||'基础使用')===v?'checked':''}><label for="cpa${v}">${v}</label>`
            ).join('')}
          </div>
        </div>
        <div class="fg">
          <div class="fgl">🎯 个人学习目标</div>
          <input type="text" id="cpGoal" value="${p.learning_goal||''}" placeholder="如：系统掌握AI辅助业务分析方法">
        </div>
        <div class="fg">
          <div class="fgl">📊 基础能力测试 <span style="color:rgba(255,255,255,.25);font-weight:400">（共8题，请认真作答）</span></div>
          <div style="font-size:9px;color:rgba(255,171,0,.5);margin-bottom:6px;padding:4px 8px;background:rgba(255,171,0,.04);border-radius:4px">💡 你的答题情况将作为基础能力评判依据，自动生成能力雷达图</div>
          <div style="display:flex;flex-direction:column;gap:8px">
            <div style="font-size:10px;font-weight:600;color:rgba(79,195,247,.5);padding:2px 0">▎业务理解能力</div>
            ${QUIZ_QUESTIONS.slice(0,2).map(q => renderQuizQuestion(q)).join('')}
            <div style="font-size:10px;font-weight:600;color:rgba(79,195,247,.5);padding:2px 0;margin-top:4px">▎数据分析能力</div>
            ${QUIZ_QUESTIONS.slice(2,4).map(q => renderQuizQuestion(q)).join('')}
            <div style="font-size:10px;font-weight:600;color:rgba(79,195,247,.5);padding:2px 0;margin-top:4px">▎AI工具应用能力</div>
            ${QUIZ_QUESTIONS.slice(4,6).map(q => renderQuizQuestion(q)).join('')}
            <div style="font-size:10px;font-weight:600;color:rgba(79,195,247,.5);padding:2px 0;margin-top:4px">▎经营决策能力</div>
            ${QUIZ_QUESTIONS.slice(6,8).map(q => renderQuizQuestion(q)).join('')}
          </div>
        </div>
      </div>
      <div class="modal-ft">
        <button class="btn-primary" style="width:100%;padding:8px" onclick="submitCourseProfile()">${profileModalEditing ? '💾 保存修改' : '🧬 生成学习画像'}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // ESC to close
  document.addEventListener('keydown', _cpEscHandler = (e) => {
    if (e.key === 'Escape') closeCourseProfileModal();
  });
}

function closeCourseProfileModal() {
  const modal = document.getElementById('courseProfileModal');
  if (modal) { modal.classList.remove('active'); setTimeout(() => modal.remove(), 300); }
  if (window._cpEscHandler) {
    document.removeEventListener('keydown', window._cpEscHandler);
    window._cpEscHandler = null;
  }
}

async function submitCourseProfile() {
  const btn = document.querySelector('#courseProfileModal .btn-primary');
  btn.disabled = true; btn.textContent = '⏳ 诊断中...';

  // 检查是否所有题目都已作答
  const unanswered = QUIZ_QUESTIONS.filter(q => !document.querySelector(`input[name="quiz_${q.id}"]:checked`));
  if (unanswered.length > 0) {
    if (!confirm(`还有 ${unanswered.length} 道题未作答，确定提交吗？`)) {
      btn.disabled = false; btn.textContent = profileModalEditing ? '💾 保存修改' : '🧬 生成学习画像';
      return;
    }
  }

  // 根据答题情况计算能力值
  const skills = calculateQuizSkills();

  const data = {
    name: document.getElementById('cpName').value.trim() || '学习者',
    role: document.getElementById('cpRole').value,
    experience: document.querySelector('input[name="cpExp"]:checked')?.value || '1-3年',
    ecommerce_exp: document.getElementById('cpBiz').value.trim() || '',
    ai_level: document.querySelector('input[name="cpAi"]:checked')?.value || '基础使用',
    learning_goal: document.getElementById('cpGoal').value.trim() || '',
    skills: skills,
  };

  if (profileModalEditing && store.profileId) {
    data.profile_id = store.profileId;
  }

  try {
    const profile = await api.diagnoseProfile(data);
    store.profile = profile;
    store.profileId = profile.id;
    closeCourseProfileModal();
    loadCourseData();
  } catch (e) {
    alert('诊断失败: ' + e.message);
  }
  btn.disabled = false; btn.textContent = profileModalEditing ? '💾 保存修改' : '🧬 生成学习画像';
}

// Agent详情抽屉
function openCourseAgentDrawer(idx) {
  const a = COURSE_AGENTS.find(x => x.idx === idx);
  if (!a) return;
  const card = document.querySelector(`#courseAgentFlow .agent-card[data-idx="${idx}"]`);
  const status = card?.classList.contains('completed') ? '已完成' :
                 card?.classList.contains('active') ? '运行中' : '就绪';
  const sc = status === '已完成' ? '#00c853' : status === '运行中' ? '#4fc3f7' : 'rgba(255,255,255,.35)';

  document.getElementById('drIcon').textContent = ['🔬','🧩','📋','✍','💡','✅'][idx-1] || '🤖';
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
