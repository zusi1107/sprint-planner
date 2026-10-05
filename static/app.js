const $ = (selector) => document.querySelector(selector);
let backlog = [];
let history = [];
let busy = false;
let sortColumn = 'key';
let sortDirection = 'asc';

function resources() {
  const members = Number($('#members').value);
  const availability = Number($('#availability').value) / 100;
  const velocity = Number($('#velocity').value);
  if (!Number.isInteger(members) || members < 1 || members > 30 || availability < 0.1 || availability > 1 || !Number.isInteger(velocity) || velocity < 1 || velocity > 300) {
    throw new Error('チーム人数・稼働率・ベロシティの値を確認してください。');
  }
  return { members, availability, velocity };
}

function updateCapacity() {
  $('#plan-card').classList.add('hidden');
  try {
    const { members, availability, velocity } = resources();
    $('#capacity').innerHTML = `${Math.min(velocity, Math.floor(members * 10 * availability))} <small>SP</small>`;
  } catch { $('#capacity').textContent = '— SP'; }
}

function addMessage(role, content) {
  const row = document.createElement('div');
  row.className = `message ${role}`;
  if (role === 'assistant') {
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '✦';
    row.append(avatar);
  }
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;
  row.append(bubble);
  $('#messages').append(row);
  $('#messages').scrollTop = $('#messages').scrollHeight;
  return row;
}

function renderBacklog() {
  const search = $('#search').value.toLowerCase().trim();
  const priority = $('#priority').value;
  const visible = backlog.filter((issue) => (!priority || issue.priority === priority) && `${issue.key} ${issue.summary}`.toLowerCase().includes(search));
  const priorityOrder = { Highest: 0, High: 1, Medium: 2, Low: 3 };
  visible.sort((a, b) => {
    let comparison = 0;
    if (sortColumn === 'key') comparison = a.key.localeCompare(b.key);
    if (sortColumn === 'priority') comparison = priorityOrder[a.priority] - priorityOrder[b.priority];
    if (sortColumn === 'sp') comparison = a.story_points - b.story_points;
    return (sortDirection === 'asc' ? comparison : -comparison) || a.key.localeCompare(b.key);
  });
  for (const button of document.querySelectorAll('.sort-header')) {
    const active = button.dataset.sort === sortColumn;
    button.closest('th').setAttribute('aria-sort', active ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none');
    button.querySelector('.sort-arrow').textContent = active ? (sortDirection === 'asc' ? '↑' : '↓') : '↕';
  }
  $('#issue-count').textContent = visible.length;
  const body = $('#backlog-body');
  body.replaceChildren();
  for (const issue of visible) {
    const tr = document.createElement('tr');
    const name = document.createElement('td');
    const key = document.createElement('span');
    key.textContent = issue.key;
    name.append(key, document.createTextNode(issue.summary));
    const priorityCell = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = `priority ${issue.priority}`;
    badge.textContent = issue.priority;
    priorityCell.append(badge);
    const sp = document.createElement('td');
    sp.textContent = issue.story_points;
    tr.append(name, priorityCell, sp);
    body.append(tr);
  }
  if (!visible.length) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 3;
    td.className = 'empty';
    td.textContent = '該当するタスクはありません';
    tr.append(td); body.append(tr);
  }
}

function renderPlan(plan) {
  $('#plan-card').classList.remove('hidden');
  $('#plan-total').textContent = `${plan.selected_sp} / ${plan.capacity_sp} SP`;
  $('#plan-summary').textContent = `${plan.issues.length}件を選定 · 対象 ${plan.candidate_count}件${plan.focus ? ` · テーマ「${plan.focus}」` : ''}`;
  const list = $('#plan-list');
  list.replaceChildren();
  for (const issue of plan.issues) {
    const row = document.createElement('div');
    row.className = 'plan-item';
    for (const [name, content] of [['key', issue.key], ['title', issue.summary], ['sp', `${issue.story_points} SP`]]) {
      const span = document.createElement('span'); span.className = name; span.textContent = content; row.append(span);
    }
    list.append(row);
  }
  if (!plan.issues.length) list.textContent = '該当する候補はありません。テーマを変えてお試しください。';
}

async function send(message) {
  if (busy || !message.trim()) return;
  let team;
  try { team = resources(); } catch (error) { addMessage('assistant', error.message); return; }
  busy = true;
  $('#send-button').disabled = true;
  $('#plan-button').disabled = true;
  addMessage('user', message);
  $('#prompt').value = '';
  const pending = addMessage('assistant', '考えています…');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, history: history.slice(-12), ...team }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '応答を取得できませんでした。');
    pending.querySelector('.bubble').textContent = data.reply || '回答が空でした。';
    history.push({ role: 'user', content: message }, { role: 'assistant', content: data.reply || '' });
    if (data.plan) renderPlan(data.plan);
  } catch (error) {
    pending.querySelector('.bubble').textContent = error.message;
  } finally {
    busy = false;
    $('#send-button').disabled = false;
    $('#plan-button').disabled = false;
    $('#messages').scrollTop = $('#messages').scrollHeight;
  }
}

for (const id of ['members', 'availability', 'velocity']) $(`#${id}`).addEventListener('input', updateCapacity);
$('#search').addEventListener('input', renderBacklog);
$('#priority').addEventListener('change', renderBacklog);
for (const button of document.querySelectorAll('.sort-header')) {
  button.addEventListener('click', () => {
    if (sortColumn === button.dataset.sort) sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    else { sortColumn = button.dataset.sort; sortDirection = 'asc'; }
    renderBacklog();
  });
}
$('#plan-button').addEventListener('click', () => send('現在のチームリソースと優先度を考慮して、次の2週間スプリント案を作成してください。'));
$('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); send($('#prompt').value); });
$('#prompt').addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); $('#chat-form').requestSubmit(); } });

updateCapacity();
fetch('/api/bootstrap').then((response) => response.json()).then((data) => {
  backlog = data.backlog;
  renderBacklog();
  const status = $('#api-status');
  status.className = `status ${data.key_configured ? 'ready' : 'error'}`;
  status.innerHTML = `<span></span>${data.key_configured ? 'AI 接続準備完了' : 'APIキー未設定'}`;
}).catch(() => { $('#api-status').textContent = 'データ取得エラー'; });
