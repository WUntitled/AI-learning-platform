/**
 * 主面板页面
 */
function renderDashboard() {
  const main = document.getElementById('appMain');
  main.innerHTML = `
    <div class="page active" id="pageDashboard">
      <div style="padding:14px 20px 6px;flex-shrink:0">
        <div style="font-size:16px;font-weight:600;color:#e8edf5">🏠 系统主面板</div>
        <div style="font-size:10px;color:rgba(255,255,255,.3);margin-top:3px">多智能体协同 AI 辅助业务分析培训平台</div>
      </div>
      <div style="flex:1;overflow-y:auto">
        <div class="dashboard-grid">
          <div class="dashboard-card" onclick="navigateTo('course')">
            <div class="dc-badge">多Agent协同</div>
            <div class="dc-icon c1">📚</div>
            <div class="dc-title">AI做课助手</div>
            <div class="dc-desc">学情画像构建 · 个性化课程生成<br>6个Agent协同完成课程设计</div>
            <div class="dc-status"><span style="color:#4fc3f7">●</span> 进入做课</div>
          </div>

          <div class="dashboard-card" onclick="navigateTo('learning')">
            <div class="dc-badge">启发式交互</div>
            <div class="dc-icon c2">💬</div>
            <div class="dc-title">AI学习助手</div>
            <div class="dc-desc">启发式答疑 · 多Agent路由<br>实时学情更新与画像追踪</div>
            <div class="dc-status"><span style="color:#00c853">●</span> 进入学习</div>
          </div>

          <div class="dashboard-card" onclick="navigateTo('practice')">
            <div class="dc-badge">实战演练</div>
            <div class="dc-icon c3">⚡</div>
            <div class="dc-title">AI陪练助手</div>
            <div class="dc-desc">场景化实战演练 · 智能评估<br>4类实战题型覆盖业务全场景</div>
            <div class="dc-status"><span style="color:#7c4dff">●</span> 进入陪练</div>
          </div>

          <div class="dashboard-card" onclick="navigateTo('exam')">
            <div class="dc-badge">能力评估</div>
            <div class="dc-icon c4">📝</div>
            <div class="dc-title">AI考试助手</div>
            <div class="dc-desc">智能出题 · 自动评分<br>多维度学情报告与能力追踪</div>
            <div class="dc-status"><span style="color:#ffab00">●</span> 进入考试</div>
          </div>

          <div class="dashboard-card full" id="dashProfileSection" onclick="navigateTo('report')">
            <div class="dc-title">📊 学情概览</div>
            <div style="display:grid;grid-template-columns:1.2fr 1fr 1.2fr;gap:16px;margin-top:12px" id="dashProfileContent">
              <div style="display:flex;flex-direction:column;gap:4px">
                <div style="font-size:10px;color:rgba(255,255,255,.3)">当前学习者</div>
                <div id="dashName" style="font-size:14px;font-weight:600">—</div>
                <div id="dashRole" style="font-size:10px;color:rgba(255,255,255,.35)">—</div>
              </div>
              <div style="display:flex;flex-direction:column;gap:4px">
                <div style="font-size:10px;color:rgba(255,255,255,.3)">能力评分</div>
                <div id="dashScore" style="font-size:14px;font-weight:600">—</div>
                <div id="dashStage" style="font-size:10px;color:rgba(255,255,255,.35)">—</div>
              </div>
              <div style="display:flex;flex-direction:column;gap:4px">
                <div style="font-size:10px;color:rgba(255,255,255,.3)">学习轨迹</div>
                <div id="dashTrajectory" style="font-size:10px;color:rgba(255,255,255,.35)">
                  <span id="dashTrajCount">0</span> 条学习记录
                </div>
                <div id="dashExamScore" style="font-size:10px;color:rgba(255,255,255,.35)">—</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>`;

  // 加载数据
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    const status = await api.systemStatus();
    document.getElementById('llmBadge').textContent =
      status.llm_provider === 'simulation' ? '模拟模式' : status.llm_provider.toUpperCase();

    const profile = await store.ensureProfile();
    if (profile) {
      document.getElementById('dashName').textContent = profile.name || '—';
      document.getElementById('dashRole').textContent = `${profile.role || '—'} · ${profile.experience || '—'}`;
      document.getElementById('dashScore').textContent = `${profile.score || '—'}/100`;
      document.getElementById('dashStage').textContent = profile.stage || '—';
      const traj = profile.trajectory || [];
      document.getElementById('dashTrajCount').textContent = traj.length;
      if (traj.length > 0) {
        document.getElementById('dashTrajectory').innerHTML = `📅 最近: ${traj[0].content || traj[0].module || '—'}`;
      }
    }
  } catch (e) {
    console.warn('Dashboard load error:', e.message);
  }
}
