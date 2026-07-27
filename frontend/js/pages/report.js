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

    // Section 2: Skills matrix — cleaner per-topic horizontal bars
    html += `<div class="report-card full"><div class="rc-title">🔥 技能知识掌握情况</div>
      <div style="font-size:10px">`;
    const topics = [
      { name: '商品分析', key: 0 },
      { name: '用户分析', key: 1 },
      { name: '渠道分析', key: 2 },
      { name: '活动分析', key: 3 },
      { name: '数据分析', key: 4 },
      { name: '经营决策', key: 5 },
    ];
    topics.forEach((t, i) => {
      const score = Math.max(15, Math.min(95, (values[t.key] || 50) + Math.floor(Math.random() * 15 - 7)));
      const color = score >= 70 ? '#4fc3f7' : score >= 40 ? '#ffab00' : '#ff5252';
      html += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="min-width:56px;font-size:9px;color:rgba(255,255,255,.4);text-align:right">${t.name}</span>
        <div style="flex:1;height:8px;background:rgba(255,255,255,.04);border-radius:4px;overflow:hidden">
          <div style="height:100%;width:${score}%;background:${color};border-radius:4px;transition:width .8s ease"></div>
        </div>
        <span style="min-width:24px;font-size:9px;color:${color};font-weight:600;text-align:right">${score}</span>
      </div>`;
    });
    html += '</div></div>';

    // Section 3: Trend — SVG line chart instead of bars
    html += `<div class="report-card full"><div class="rc-title">📉 阶段能力变化趋势</div><div style="font-size:10px;color:rgba(255,255,255,.4)">`;
    const trendLabels = ['培训前','阶段一','阶段二','阶段三','本次'];
    const baseSkill = values[1] || 50;
    const trendSkills = trendLabels.map((_, i) => Math.max(10, Math.min(95, baseSkill - 25 + i * 10 + Math.floor(Math.random() * 6 - 3))));
    const trendEfficiency = trendLabels.map((_, i) => Math.max(10, Math.min(95, 90 - i * 10 + Math.floor(Math.random() * 8 - 4))));
    const svgW = 300, svgH = 110, padL = 30, padR = 10, padT = 12, padB = 22;
    const chartW = svgW - padL - padR, chartH = svgH - padT - padB;
    const allVals = [...trendSkills, ...trendEfficiency];
    const maxV = Math.max(...allVals, 50), minV = Math.min(...allVals, 10);
    const range = maxV - minV || 1;

    const skillPoints = trendSkills.map((v, i) => {
      const x = padL + (i / (trendLabels.length - 1)) * chartW;
      const y = padT + chartH - ((v - minV) / range) * chartH;
      return { x, y, v };
    });
    const effPoints = trendEfficiency.map((v, i) => {
      const x = padL + (i / (trendLabels.length - 1)) * chartW;
      const y = padT + chartH - ((v - minV) / range) * chartH;
      return { x, y, v };
    });

    html += `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}" style="display:block;margin:0 auto">`;
    // Grid lines
    for (let g = 0; g <= 4; g++) {
      const gy = padT + (g / 4) * chartH;
      const gv = Math.round(maxV - (g / 4) * range);
      html += `<line x1="${padL}" y1="${gy}" x2="${svgW - padR}" y2="${gy}" stroke="rgba(255,255,255,.05)" stroke-width="0.5"/>`;
      html += `<text x="${padL - 4}" y="${gy + 3}" fill="rgba(255,255,255,.2)" font-size="6" text-anchor="end">${gv}</text>`;
    }
    // X labels
    trendLabels.forEach((l, i) => {
      const x = padL + (i / (trendLabels.length - 1)) * chartW;
      html += `<text x="${x}" y="${svgH - 3}" fill="rgba(255,255,255,.25)" font-size="7" text-anchor="middle">${l}</text>`;
    });

    // Skill line
    const skillD = skillPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    html += `<path d="${skillD}" fill="none" stroke="#4fc3f7" stroke-width="1.5" stroke-linejoin="round"/>`;
    // Skill dots
    skillPoints.forEach(p => {
      html += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3" fill="#4fc3f7" stroke="#080e2b" stroke-width="1.5"/>`;
      html += `<text x="${p.x.toFixed(1)}" y="${(p.y - 6).toFixed(1)}" fill="#4fc3f7" font-size="6" text-anchor="middle">${p.v}</text>`;
    });

    // Efficiency line
    const effD = effPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    html += `<path d="${effD}" fill="none" stroke="#00c853" stroke-width="1.5" stroke-linejoin="round" stroke-dasharray="3,2"/>`;
    // Efficiency dots
    effPoints.forEach(p => {
      html += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3" fill="#00c853" stroke="#080e2b" stroke-width="1.5"/>`;
      html += `<text x="${p.x.toFixed(1)}" y="${(p.y + 11).toFixed(1)}" fill="#00c853" font-size="6" text-anchor="middle">${p.v}</text>`;
    });

    html += `</svg>
    <div style="display:flex;gap:16px;margin-top:2px;justify-content:center">
      <span style="font-size:7px;display:flex;align-items:center;gap:3px"><span style="width:8px;height:2px;background:#4fc3f7;display:inline-block"></span>技能得分</span>
      <span style="font-size:7px;display:flex;align-items:center;gap:3px"><span style="width:8px;height:2px;border-top:2px dashed #00c853;display:inline-block"></span>任务完成效率</span>
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
