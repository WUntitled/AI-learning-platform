/**
 * SPA 路由 & 应用主逻辑
 *
 * 使用 hash 路由： #/dashboard, #/course, #/learning, #/practice, #/exam, #/report
 */

// ================================================================
// 路由表
// ================================================================
const ROUTES = {
  dashboard: { title: '主面板', render: renderDashboard },
  course:    { title: 'AI做课', render: renderCoursePage },
  learning:  { title: 'AI学习', render: renderLearningPage },
  practice:  { title: 'AI陪练', render: renderPracticePage },
  exam:      { title: 'AI考试', render: renderExamPage },
  report:    { title: '学情报告', render: renderReportPage },
};

function navigateTo(page) {
  if (!ROUTES[page]) page = 'dashboard';
  window.location.hash = `#/${page}`;
}

function handleRoute() {
  const hash = window.location.hash.slice(2) || 'dashboard';
  const route = ROUTES[hash] || ROUTES.dashboard;

  // Update nav
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === hash);
  });

  // Render page
  route.render();
}

// ================================================================
// 共享工具函数
// ================================================================

function closeDrawer(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('drawerOverlay')?.classList.remove('active');
}

function openAgentDrawer(idx, module = 'course') {
  // Dispatch to page-specific drawer
  if (module === 'learning') {
    if (typeof openLearningAgentDrawer === 'function') openLearningAgentDrawer(idx);
  } else if (module === 'practice') {
    if (typeof openPracticeAgentDrawer === 'function') openPracticeAgentDrawer(idx);
  } else if (module === 'exam') {
    if (typeof openExamAgentDrawer === 'function') openExamAgentDrawer(idx);
  } else {
    if (typeof openCourseAgentDrawer === 'function') openCourseAgentDrawer(idx);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ================================================================
// 初始化
// ================================================================

document.addEventListener('DOMContentLoaded', async () => {
  // 初始加载 profile
  await store.loadProfile();

  // 设置路由监听
  window.addEventListener('hashchange', handleRoute);

  // 处理初始路由
  if (!window.location.hash) {
    window.location.hash = '#/dashboard';
  } else {
    handleRoute();
  }

  // 更新系统状态
  updateSystemStatus();
});

async function updateSystemStatus() {
  try {
    const status = await api.systemStatus();
    const badge = document.getElementById('llmBadge');
    if (badge) {
      badge.textContent = status.llm_provider === 'simulation' ? '模拟模式' : status.llm_provider.toUpperCase();
    }
  } catch (e) {
    document.getElementById('sysStatus').textContent = '无法连接';
  }
}
