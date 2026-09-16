// JARVIS Futuristic Arc Reactor HUD Visualizer

const canvas = document.getElementById('hud-canvas');
const ctx = canvas.getContext('2d');
const width = canvas.width;
const height = canvas.height;
const centerX = width / 2;
const centerY = height / 2;

let currentState = 'idle'; // idle, listening, thinking, speaking
let audioLevel = 0.2; // Normalized 0.0 - 1.0
let rotationAngle = 0;
let pulseFactor = 0;

// Colors
const colors = {
  idle: { primary: '#00f3ff', secondary: '#0077ff', core: '#e0f2fe' },
  listening: { primary: '#00f3ff', secondary: '#00e1ff', core: '#ffffff' },
  thinking: { primary: '#a855f7', secondary: '#c084fc', core: '#f3e8ff' },
  speaking: { primary: '#ffb700', secondary: '#ff8800', core: '#fff7ed' }
};

function setHudState(state, transcriptText = '', responseText = '') {
  currentState = state;
  document.body.className = `state-${state}`;
  
  const modeTitle = document.getElementById('mode-title');
  const modeSub = document.getElementById('mode-sub');
  
  if (state === 'listening') {
    modeTitle.innerText = 'LISTENING';
    modeSub.innerText = 'ESHITMOQDA...';
  } else if (state === 'thinking') {
    modeTitle.innerText = 'THINKING';
    modeSub.innerText = 'TAHLIL QILINMOQDA...';
  } else if (state === 'speaking') {
    modeTitle.innerText = 'SPEAKING';
    modeSub.innerText = 'GAPIRMOQDA...';
  } else {
    modeTitle.innerText = 'IDLE';
    modeSub.innerText = 'TAYYOR';
  }

  if (transcriptText) {
    document.getElementById('transcript-text').innerText = transcriptText;
  }
  if (responseText) {
    document.getElementById('response-text').innerText = responseText;
  }
}

function updateAudioLevel(level) {
  audioLevel = Math.max(0.15, Math.min(1.0, level));
}

function handleMicClick() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.trigger_listen();
  } else {
    console.log("PyWebView API not ready");
  }
}

function drawHUD() {
  ctx.clearRect(0, 0, width, height);

  const scheme = colors[currentState] || colors.idle;
  rotationAngle += (currentState === 'thinking' ? 0.06 : 0.02);
  pulseFactor += 0.06;

  // Dynamic Audio Intensity Level
  const currentLevel = (currentState === 'listening' || currentState === 'speaking') 
    ? audioLevel 
    : 0.15 + Math.sin(pulseFactor) * 0.08;

  // 1. Outer Rotating Segmented HUD Ring (Expands 2-ways radially)
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(rotationAngle);
  ctx.strokeStyle = scheme.primary;
  ctx.lineWidth = 2.5;
  ctx.shadowColor = scheme.primary;
  ctx.shadowBlur = 15;

  const segments = 12;
  const outerRadius = 145 + currentLevel * 30; // 2-direction outward expansion
  for (let i = 0; i < segments; i++) {
    const startAngle = (i * 2 * Math.PI) / segments;
    const endAngle = startAngle + Math.PI / (segments * 1.5);
    ctx.beginPath();
    ctx.arc(0, 0, outerRadius, startAngle, endAngle);
    ctx.stroke();
  }
  ctx.restore();

  // 2. Counter-Rotating Inner Reticle
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(-rotationAngle * 1.4);
  ctx.strokeStyle = scheme.secondary;
  ctx.lineWidth = 1.8;
  ctx.shadowColor = scheme.secondary;
  ctx.shadowBlur = 10;

  const innerRadius = 110 + currentLevel * 10;
  for (let i = 0; i < 4; i++) {
    const angle = (i * Math.PI) / 2;
    ctx.beginPath();
    ctx.arc(0, 0, innerRadius, angle, angle + Math.PI / 4);
    ctx.stroke();
  }
  ctx.restore();

  // 3. Dynamic 2-Way Horizontal & Vertical Equalizer Bars (Reacting to Voice)
  ctx.save();
  ctx.translate(centerX, centerY);
  const barsCount = 48;
  const baseRadius = 75;

  for (let i = 0; i < barsCount; i++) {
    const angle = (i * 2 * Math.PI) / barsCount;
    
    // Create 2-way symmetrical wave motion (left/right & top/bottom expansion)
    const symmetryFactor = Math.abs(Math.sin(angle * 2));
    const noise = Math.sin(i * 0.6 + pulseFactor * 2.5) * 0.5 + 0.5;
    const barHeight = 8 + (noise * currentLevel * 55 * (0.6 + 0.4 * symmetryFactor));

    // Expand in both inward and outward directions (2-way movement)
    const innerX = Math.cos(angle) * (baseRadius - barHeight * 0.3);
    const innerY = Math.sin(angle) * (baseRadius - barHeight * 0.3);
    const outerX = Math.cos(angle) * (baseRadius + barHeight);
    const outerY = Math.sin(angle) * (baseRadius + barHeight);

    ctx.strokeStyle = scheme.primary;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = scheme.primary;
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.moveTo(innerX, innerY);
    ctx.lineTo(outerX, outerY);
    ctx.stroke();
  }
  ctx.restore();

  // 4. Glowing Arc Reactor Core Orb
  ctx.save();
  ctx.translate(centerX, centerY);
  const coreRadius = 38 + currentLevel * 20; // Core expands dynamically with voice
  const gradient = ctx.createRadialGradient(0, 0, 5, 0, 0, coreRadius);
  gradient.addColorStop(0, scheme.core);
  gradient.addColorStop(0.5, scheme.primary);
  gradient.addColorStop(1, 'transparent');

  ctx.fillStyle = gradient;
  ctx.shadowColor = scheme.primary;
  ctx.shadowBlur = 30;
  ctx.beginPath();
  ctx.arc(0, 0, coreRadius, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  requestAnimationFrame(drawHUD);
}

// Start Animation Loop
drawHUD();

// Expose API for PyWebView Python integration
window.jarvisUI = {
  setState: setHudState,
  setAudioLevel: updateAudioLevel
};
