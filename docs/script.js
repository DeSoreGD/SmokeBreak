const ring = document.getElementById('ringProgress');
const timeText = document.getElementById('timeText');
const stateText = document.getElementById('stateText');
const startPauseBtn = document.getElementById('startPauseBtn');
const resetBtn = document.getElementById('resetBtn');
const finishedPanel = document.getElementById('finishedPanel');
const tookCount = document.getElementById('tookCount');
const skipCount = document.getElementById('skipCount');
const delayCount = document.getElementById('delayCount');
const chips = document.querySelectorAll('.chip');
const circumference = 2 * Math.PI * 92;
ring.style.strokeDasharray = `${circumference}`;

let selectedSeconds = 90 * 60;
let remainingSeconds = selectedSeconds;
let running = false;
let timerId = null;
let stats = { took: 0, skipped: 0, delayed: 0 };

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function render() {
  timeText.textContent = formatTime(remainingSeconds);
  const progress = remainingSeconds / selectedSeconds;
  ring.style.strokeDashoffset = `${circumference * (1 - progress)}`;
  tookCount.textContent = stats.took;
  skipCount.textContent = stats.skipped;
  delayCount.textContent = stats.delayed;
}

function finishTimer() {
  clearInterval(timerId);
  timerId = null;
  running = false;
  remainingSeconds = 0;
  stateText.textContent = 'Ended';
  startPauseBtn.textContent = 'Start';
  ring.style.stroke = 'var(--red)';
  finishedPanel.hidden = false;
  render();
}

function tick() {
  if (remainingSeconds <= 1) {
    finishTimer();
    return;
  }
  remainingSeconds -= 1;
  render();
}

function startTimer() {
  if (remainingSeconds <= 0) remainingSeconds = selectedSeconds;
  running = true;
  stateText.textContent = 'Running';
  startPauseBtn.textContent = 'Pause';
  finishedPanel.hidden = true;
  ring.style.stroke = 'var(--green)';
  clearInterval(timerId);
  timerId = setInterval(tick, 1000);
}

function pauseTimer() {
  running = false;
  stateText.textContent = 'Paused';
  startPauseBtn.textContent = 'Resume';
  clearInterval(timerId);
}

startPauseBtn.addEventListener('click', () => {
  running ? pauseTimer() : startTimer();
});

resetBtn.addEventListener('click', () => {
  clearInterval(timerId);
  timerId = null;
  running = false;
  remainingSeconds = selectedSeconds;
  stateText.textContent = 'Ready';
  startPauseBtn.textContent = 'Start';
  finishedPanel.hidden = true;
  ring.style.stroke = 'var(--green)';
  render();
});

chips.forEach((chip) => {
  chip.addEventListener('click', () => {
    chips.forEach((item) => item.classList.remove('active'));
    chip.classList.add('active');
    selectedSeconds = Number(chip.dataset.minutes) * 60;
    remainingSeconds = selectedSeconds;
    clearInterval(timerId);
    running = false;
    stateText.textContent = 'Ready';
    startPauseBtn.textContent = 'Start';
    finishedPanel.hidden = true;
    ring.style.stroke = 'var(--green)';
    render();
  });
});

finishedPanel.addEventListener('click', (event) => {
  const action = event.target.dataset.action;
  if (!action) return;
  if (action === 'took') stats.took += 1;
  if (action === 'skipped') stats.skipped += 1;
  if (action === 'delay') {
    stats.delayed += 1;
    selectedSeconds = 5 * 60;
  }
  remainingSeconds = selectedSeconds;
  finishedPanel.hidden = true;
  ring.style.stroke = 'var(--green)';
  render();
  if (action === 'delay') startTimer();
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((item) => observer.observe(item));
render();
