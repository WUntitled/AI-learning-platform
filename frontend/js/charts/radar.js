/**
 * 雷达图绘制
 */
function renderRadar(canvasId, data, color = '#4fc3f7', labels) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const w = rect.width * dpr, h = rect.height * dpr;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const cw = rect.width, ch = rect.height;
  const cx = cw / 2, cy = ch / 2;
  const margin = Math.min(cx, cy) * 0.25;
  const radius = Math.min(cx, cy) - margin;
  const labelOffset = Math.max(12, radius * 0.18);
  const fontSize = Math.max(7, Math.min(9, radius * 0.075));

  const N = data.length;
  const angles = data.map((_, i) => (Math.PI * 2 * i) / N - Math.PI / 2);

  ctx.clearRect(0, 0, cw, ch);

  // Grid rings
  for (let l = 1; l <= 5; l++) {
    const r = (radius / 5) * l;
    ctx.beginPath();
    angles.forEach((a, i) => {
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.strokeStyle = `rgba(255,255,255,${0.03 + l * 0.015})`;
    ctx.lineWidth = 0.5;
    ctx.stroke();
  }

  // Axes
  angles.forEach(a => {
    const x = cx + radius * Math.cos(a);
    const y = cy + radius * Math.sin(a);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(x, y);
    ctx.strokeStyle = 'rgba(255,255,255,.04)';
    ctx.lineWidth = 0.5;
    ctx.stroke();
  });

  // Data polygon
  ctx.beginPath();
  data.forEach((v, i) => {
    const r = (Math.max(0, Math.min(100, v)) / 100) * radius;
    const x = cx + r * Math.cos(angles[i]);
    const y = cy + r * Math.sin(angles[i]);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
  grad.addColorStop(0, toRgba(color, 0.12));
  grad.addColorStop(1, toRgba(color, 0.01));
  ctx.fillStyle = grad;
  ctx.fill();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Data points
  data.forEach((v, i) => {
    const r = (Math.max(0, Math.min(100, v)) / 100) * radius;
    const x = cx + r * Math.cos(angles[i]);
    const y = cy + r * Math.sin(angles[i]);
    ctx.beginPath();
    ctx.arc(x, y, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.3)';
    ctx.lineWidth = 0.5;
    ctx.stroke();
  });

  // Labels
  if (labels) {
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    labels.forEach((label, i) => {
      const lr = radius + labelOffset;
      let x = cx + lr * Math.cos(angles[i]);
      let y = cy + lr * Math.sin(angles[i]);
      const tw = ctx.measureText(label).width;
      const hw = tw / 2 + 3;
      const hh = fontSize / 2 + 2;
      if (x - hw < 0) x = hw;
      if (x + hw > cw) x = cw - hw;
      if (y - hh < 0) y = hh;
      if (y + hh > ch) y = ch - hh;
      ctx.fillStyle = 'rgba(255,255,255,.5)';
      ctx.fillText(label, x, y);
    });
  }

  // Center score
  const avg = Math.round(data.reduce((s, v) => s + v, 0) / data.length);
  ctx.fillStyle = color;
  ctx.font = `bold ${Math.min(18, radius * 0.25)}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(avg, cx, cy - 3);
  ctx.fillStyle = 'rgba(255,255,255,.2)';
  ctx.font = `${Math.max(6, Math.min(8, radius * 0.08))}px sans-serif`;
  ctx.fillText('综合', cx, cy + 12);
}

function renderRadarLegend(containerId, dims) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = dims.map((d, i) =>
    `<span><span class="dot" style="background:hsl(${i * 60 + 190},70%,60%)"></span>${d}</span>`
  ).join('');
}

function toRgba(c, a) {
  if (c.startsWith('#')) {
    const r = parseInt(c.slice(1, 3), 16);
    const g = parseInt(c.slice(3, 5), 16);
    const b = parseInt(c.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${a})`;
  }
  const m = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  return m ? `rgba(${m[1]},${m[2]},${m[3]},${a})` : c;
}
