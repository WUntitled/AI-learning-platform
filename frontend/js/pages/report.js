/**
 * 学情报告页面
 *
 * 展示：六维雷达图、知识掌握热力图、阶段变化趋势、培训建议
 */
function renderReportPage() {
  const main = document.getElementById('appMain');
  main.innerHTML = `
  <div class="page active" id="pageReport" style="overflow-y:auto">
    <div style="padding:16px 20px 8px;flex-shrink:0">
      <div style="font-size:16px;font-weight:600;color:#e8edf5">📊 学情报告</div>
      <div style="font-size:10px;color:rgba(255,255,255,.3);margin-top:3px">综合能力评估 · 学习轨迹追踪 · 个性化建议</div>
    </div>
    <div style="flex:1;overflow-y:auto;padding:0 16px 20px">
      <div id="reportContent">
        <div class="loading-center" style="min-height:300px">
          <div class="spinner"></div>
          <div class="lt">加载学情数据...</div>
        </div>
      </div>
    </div>
  </div>`;

  loadReportData();
}

async function loadReportData() {
  try {
    const profile = await store.ensureProfile();
    if (!profile) {
      document.getElementById('reportContent').innerHTML = emptyStateHTML('👤', '暂无学情数据',
        '请先创建学情画像并完成学习', '去创建', "navigateTo('course')");
      return;
    }

    // Get exam history for latest exam report
    let report = null;
    let latestScoring = null;
    try {
      const exams = await api.getExamHistory(profile.id);
      const completed = exams.filter(e => e.status === 'graded');
      if (completed.length > 0) {
        latestScoring = completed[0].scoring;
        report = completed[0].report;
      }
    } catch (e) { /* ignore */ }

    // Build skills from profile
    const skills = profile.skills || {};
    const dims = ['业务理解能力','数据分析能力','AI工具应用能力','经营决策能力','Prompt撰写能力','持续迭代能力'];
    const values = [
      skills.business || 50,
      skills.dataAnalysis || 50,
      skills.aiApplication || 50,
      skills.decision || 50,
      skills.prompt || 50,
      skills.continuous || 50,
    ];

    const trajectory = profile.trajectory || [];

    let html = '<div class="report-grid">';

    // Section 1: Radar + bars in separate rows to avoid overlap
    html += `<div class="report-card full"><div class="rc-title">📈 个人能力匹配图（六维能力雷达图）</div>
      <div style="display:flex;flex-direction:column;gap:12px">
        <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center">
          <div style="width:200px;height:190px;flex-shrink:0"><canvas id="reportRadar" width="200" height="190" style="width:200px;height:190px"></canvas></div>
          <div style="flex:1;min-width:160px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">`;
    values.forEach((v, i) => {
      const color = `hsl(${i*60+190},70%,60%)`;
      html += `<div><div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:1px">
        <span style="color:rgba(255,255,255,.5)">${dims[i]}</span>
        <span style="color:${color};font-weight:600">${v}</span>
      </div><div style="height:3px;background:rgba(255,255,255,.04);border-radius:2px;overflow:hidden">
        <div style="height:100%;width:${v}%;background:${color};border-radius:2px;transition:width .8s ease"></div>
      </div></div>`;
    });
    html += `</div></div></div></div></div>`;

    // Section 2: Heatmap with proper rendering
    html += `<div class="report-card full"><div class="rc-title">🔥 技能知识掌握热力图</div>
      <div style="font-size:10px;overflow-x:auto">`;
    const yLabels = ['商品分析','用户分析','渠道分析','活动分析'];
    const xLabels = ['Excel','SQL','AI工具','BI系统'];
    const heatData = [];
    for (let yi = 0; yi < yLabels.length; yi++) {
      const row = [];
      for (let xi = 0; xi < xLabels.length; xi++) {
        const heat = Math.max(20, Math.min(95, values[yi] + (xi * 8) + Math.floor(Math.random() * 20 - 10)));
        row.push(heat);
      }
      heatData.push(row);
    }
    html += '<div style="display:flex;gap:3px;margin-bottom:3px;padding-left:54px">';
    xLabels.forEach(x => { html += `<div style="flex:1;text-align:center;font-size:7px;color:rgba(255,255,255,.25)">${x}</div>`; });
    html += '</div>';
    heatData.forEach((row, yi) => {
      html += '<div style="display:flex;gap:3px;align-items:center;margin-bottom:2px">';
      html += `<div style="width:50px;font-size:8px;color:rgba(255,255,255,.35);text-align:right;flex-shrink:0">${yLabels[yi]}</div>`;
      row.forEach(heat => {
        const intensity = Math.round((heat / 100) * 0.35 + 0.05);
        html += `<div style="flex:1;height:16px;border-radius:2px;background:rgba(79,195,247,${intensity});border:1px solid rgba(79,195,247,.06);display:flex;align-items:center;justify-content:center"><span style="font-size:6px;color:rgba(255,255,255,.5)">${heat}</span></div>`;
      });
      html += '</div>';
    });
    html += '</div></div>';

    // Section 3: Trend - fixed bar overlap with smaller gaps and adjusted widths
    html += `<div class="report-card full"><div class="rc-title">📉 阶段能力变化趋势</div><div style="font-size:10px;color:rgba(255,255,255,.4)">`;
    const trendLabels = ['培训前','阶段一','阶段二','阶段三','本次'];
    const baseSkill = values[1] || 50;
    const trendSkills = trendLabels.map((_, i) => Math.max(10, baseSkill - 25 + i * 10 + Math.floor(Math.random() * 6 - 3)));
    const trendEfficiency = trendLabels.map((_, i) => Math.max(10, 90 - i * 10 + Math.floor(Math.random() * 8 - 4)));

    html += `<div style="display:flex;align-items:flex-end;gap:4px;height:90px;padding:6px 0">`;
    const maxVal = Math.max(...trendSkills, ...trendEfficiency, 50);
    trendLabels.forEach((l, i) => {
      const h1 = Math.max(4, (trendSkills[i] / maxVal) * 70);
      const h2 = Math.max(4, (trendEfficiency[i] / maxVal) * 70);
      html += `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:1px">
        <div style="font-size:7px;color:#4fc3f7">${trendSkills[i]}</div>
        <div style="width:12px;height:${h1}px;background:linear-gradient(180deg,#4fc3f7,rgba(79,195,247,.3));border-radius:2px 2px 0 0;transition:height .8s"></div>
        <div style="font-size:7px;color:#00c853">${trendEfficiency[i]}</div>
        <div style="width:12px;height:${h2}px;background:linear-gradient(180deg,#00c853,rgba(0,200,83,.3));border-radius:2px 2px 0 0;transition:height .8s"></div>
        <div style="font-size:7px;color:rgba(255,255,255,.25);margin-top:2px">${l}</div>
      </div>`;
    });
    html += `</div>
    <div style="display:flex;gap:12px;margin-top:2px;justify-content:center">
      <span style="font-size:7px;display:flex;align-items:center;gap:3px"><span style="width:6px;height:6px;border-radius:2px;background:#4fc3f7"></span>技能得分</span>
      <span style="font-size:7px;display:flex;align-items:center;gap:3px"><span style="width:6px;height:6px;border-radius:2px;background:#00c853"></span>任务完成效率</span>
    </div></div></div>`;

    // Section 4: Suggestions
    html += `<div class="report-card full"><div class="rc-title">💡 培训建议</div><div>`;
    const suggestions = generateReportSuggestions(values, latestScoring?.percentage);
    if (suggestions.length) {
      html += '<ul style="padding-left:14px;font-size:10px;line-height:1.8;color:rgba(255,255,255,.55)">';
      suggestions.forEach(s => { html += `<li>${s}</li>`; });
      html += '</ul>';
    } else {
      html += '<div style="font-size:10px;color:rgba(255,255,255,.35)">暂无建议</div>';
    }
    html += `</div></div>`;

    // Section 5: Learning trajectory
    html += `<div class="report-card full"><div class="rc-title">📋 学习轨迹</div><div><div class="trajectory-timeline" id="reportTrajectory" style="max-height:140px;overflow-y:auto">`;
    if (trajectory.length > 0) {
      trajectory.slice(0, 15).forEach(t => {
        html += `<div class="tt-item" style="padding:3px 6px"><span class="tt-date" style="min-width:50px;font-size:7px">${t.date||''}</span><span class="tt-content" style="font-size:8px">${t.content||t.module||''}</span><span class="tt-badge" style="font-size:6px">${t.ability||''}</span></div>`;
      });
    } else {
      html += '<div style="font-size:10px;color:rgba(255,255,255,.15);text-align:center;padding:8px">暂无学习记录</div>';
    }
    html += `</div></div></div>`;

    html += '</div>'; // end grid

    document.getElementById('reportContent').innerHTML = html;

    // Render radar
    setTimeout(() => {
      renderRadar('reportRadar', values, '#4fc3f7', dims);
    }, 100);

  } catch (e) {
    document.getElementById('reportContent').innerHTML =
      `<div class="empty-state"><div class="es-icon">⚠️</div><div class="es-title">加载失败</div><div class="es-sub">${e.message}</div></div>`;
  }
}

function generateReportSuggestions(values, examScore) {
  const suggestions = [];
  const dims = ['业务理解能力','数据分析能力','AI工具应用能力','经营决策能力','Prompt撰写能力','持续迭代能力'];
  values.forEach((v, i) => {
    if (v < 55) suggestions.push(`加强${dims[i]}训练，当前评分 ${v}`);
  });
  if (examScore !== null && examScore !== undefined) {
    if (examScore < 60) suggestions.push('考试表现不佳，建议重新学习基础课程后再次测试');
    else if (examScore < 80) suggestions.push('考试表现良好，建议在薄弱维度进行重点突破');
    else suggestions.push('考试表现优秀，建议挑战更高难度课程');
  }
  if (suggestions.length === 0) suggestions.push('整体能力均衡，建议持续保持学习节奏并挑战高阶实战任务');
  suggestions.push('建议将所学知识应用到实际工作中，通过实践巩固理论');
  return suggestions;
}
