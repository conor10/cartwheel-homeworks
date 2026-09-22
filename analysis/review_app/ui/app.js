'use strict';
const $ = (q, root = document) => root.querySelector(q);
const $$ = (q, root = document) => [...root.querySelectorAll(q)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const json = v => JSON.stringify(v, null, 2) ?? 'null';
const short = v => String(v || '').slice(0, 8);
const badge = (text, cls = '') => `<span class="badge ${cls}">${esc(text)}</span>`;
const button = (text, action, attrs = '', cls = '') => `<button class="${cls}" data-action="${action}" ${attrs}>${text}</button>`;
let state, traces = [], session = [], source, spec, view = 'review', current, busy = false, observer, loadToken = 0;
let activeSpan, selection = null, editingNote = null, pendingNoteId = null, queueHidden = false, navHidden = false;
let filters = {q:'', role:'', intent:'', group:'', status:''}, navFilter = '', modeName = '', labelMode = '';
let mapData = null, searchResults = [], depthIds = new Set();
let labelLayout = 'category', categoryMode = '', categoryFilter = 'all';
const sidebarScroll = {'.queue':0, '.span-pane':0};

function rememberSidebarScroll() {
  for (const selector of Object.keys(sidebarScroll)) {
    const pane = $(selector);
    if (pane?.clientHeight) sidebarScroll[selector] = pane.scrollTop;
  }
}
function revealCurrentItem(pane) {
  const item = $('.current', pane);
  if (!item || !pane.clientHeight) return;
  // Scroll only this panel, never the conversation or the surrounding page.
  const bounds = pane.getBoundingClientRect(), row = item.getBoundingClientRect();
  const top = bounds.top + pane.clientTop + 8, bottom = top + pane.clientHeight - 16;
  if (row.top < top) pane.scrollTop += Math.floor(row.top - top);
  else if (row.bottom > bottom) pane.scrollTop += Math.ceil(Math.min(row.bottom - bottom, row.top - top));
}
function restoreSidebarScroll() {
  for (const [selector, top] of Object.entries(sidebarScroll)) {
    const pane = $(selector);
    if (!pane) continue;
    pane.scrollTop = top;
    revealCurrentItem(pane);
  }
}
let depthQuery = '', depthReason = '', depthFeedback = '', depthError = false;
function saveDepthDraft() {
  localStorage.setItem('cartwheel-hw4-depth-draft',json({ids:[...depthIds],query:depthQuery,reason:depthReason,results:searchResults}));
}
function depthStatus(message, error = false) {
  depthFeedback=message;depthError=error;
  const el=$('#depth-feedback');
  if(el){el.textContent=message;el.dataset.error=String(error);}
}
const byId = id => traces.find(t => t.id === id);
const currentTrace = () => session.find(t => t.id === current);
const notesFor = tid => state.annotations.filter(a => a.trace_id === tid);
const reviewed = tid => state.reviews[tid] && state.reviews[tid].status !== 'unreviewed';
const finalModes = () => state.modes.filter(m => m.status === 'final');
const sampled = () => new Set(state.manifest.picks.map(p => p.trace_id));
const initialPicks = () => state.manifest.picks.filter(p => ['initial_random','initial_cluster'].includes(p.batch));
const reviewSet = () => state.manifest.picks.filter(p => reviewed(p.trace_id)).map(p => p.trace_id);
const labelFor = (tid, mode) => state.labels[`${tid}:${mode.name}`];
const currentLabel = (tid, mode) => {const l = labelFor(tid, mode); return l?.mode_version === mode.version ? l : null;};

function notice(message, error = false) {
  $('#notice').hidden = !message;
  $('#notice').innerHTML = message ? `${esc(message)} ${button('Dismiss', 'dismiss', '', 'quiet')}` : '';
  $('#notice').dataset.error = String(error);
}
async function api(path, body) {
  const res = await fetch('/api/' + path, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || `Request failed (${res.status})`);
  return result;
}
function status() {
  const pending = Object.values(state.outbox).filter(o => o.status !== 'synced').length;
  $('#connection').textContent = `${source === 'langfuse' ? '● Live Langfuse' : '◌ Offline · local only'}  /  ${traces.length} traces  /  ${new Set(traces.map(t => t.session_id)).size} conversations`;
  $('#sync-status').innerHTML = pending ? `<span class="sync-pending">${pending} save${pending === 1 ? '' : 's'} pending sync</span> ${button('Retry sync', 'sync', '', 'quiet')}` : '<span class="sync-ok">No pending saves</span>';
}
async function mutate(action, body) {
  if (busy) throw new Error('A save is already in progress. Please wait.');
  busy = true;
  const locked = $$('button,input,textarea,select').filter(el => !el.disabled);
  locked.forEach(el => {el.disabled=true;});
  $('#sync-status').textContent = 'Saving…';
  try {
    state = await api(action, {...body, revision:state.revision});
    const failures = Object.values(state.outbox).filter(o => o.error && o.status !== 'synced');
    if (failures.length) notice('Saved locally. Langfuse has not confirmed every save. Use Retry sync; your work is retained.', true);
    return state;
  } finally {busy = false; locked.forEach(el => {el.disabled=false;}); status();}
}

function highlightedEvidence(text, tid, oid, field) {
  const candidates = notesFor(tid).map(n => ({...n, draft:false}));
  if (selection?.trace_id === tid) candidates.push({...selection, draft:true, note:'Selected evidence · unsaved draft'});
  const ranges = candidates.filter(n => (n.observation_id || '') === (oid || '') && n.field === field && n.quote).map(n => {
    let start = n.start;
    if (!Number.isInteger(start) || text.slice(start, start + n.quote.length) !== n.quote) {
      start = text.indexOf(n.quote);
      if (start !== text.lastIndexOf(n.quote)) return null;
    }
    return start < 0 ? null : {start, end:start + n.quote.length, note:n};
  }).filter(Boolean);
  // Split overlapping ranges so draft selections never hide saved evidence.
  const boundaries = [...new Set([0, text.length, ...ranges.flatMap(r => [r.start, r.end])])].sort((a,b) => a-b);
  let html = '';
  for (let i = 1; i < boundaries.length; i++) {
    const start = boundaries[i-1], end = boundaries[i];
    const covering = ranges.filter(r => r.start <= start && r.end >= end);
    const content = esc(text.slice(start,end));
    html += covering.length ? `<mark class="${covering.some(r => r.note.draft) ? 'draft-highlight' : ''}" title="${esc(covering.map(r => r.note.note).join('\n'))}">${content}</mark>` : content;
  }
  return html;
}
function evidence(text, tid, oid, field, cls = 'prose') {
  return `<div class="${cls}" data-evidence data-trace="${esc(tid)}" data-obs="${esc(oid || '')}" data-field="${esc(field)}">${highlightedEvidence(String(text ?? ''),tid,oid,field)}</div>`;
}
function refreshEvidenceHighlights() {
  for (const el of $$('#conversation [data-evidence]')) {
    el.innerHTML = highlightedEvidence(el.textContent,el.dataset.trace,el.dataset.obs,el.dataset.field);
  }
}

function toolResult(value, tid, oid) {
  if (!value || typeof value !== 'object') return evidence(json(value), tid, oid, 'output');
  let html = '';
  if ('ok' in value) html += badge(value.ok ? 'Tool returned ok' : `Tool returned ${value.error || 'error'}`, value.ok ? '' : 'error');
  if (value.reason) html += evidence(value.reason, tid, oid, 'output.reason');
  if (value.status) html += ' ' + badge(value.status);
  const list = value.orders || value.products || (value.order ? [value.order] : null);
  if (list) {
    if (!list.length) html += '<p class="muted">No matching records.</p>';
    else {
      const keys = [...new Set(list.flatMap(Object.keys))];
      const base = value.orders ? 'orders' : value.products ? 'products' : 'order';
      html += `<table class="data-table"><thead><tr>${keys.map(k => `<th>${esc(k)}</th>`).join('')}</tr></thead><tbody>`;
      html += list.map((row,i) => `<tr>${keys.map(k => `<td>${evidence(row[k] === null ? 'null' : row[k] ?? '—', tid, oid, `output.${base}${base === 'order' ? '' : '.'+i}.${k}`)}</td>`).join('')}</tr>`).join('') + '</tbody></table>';
    }
  }
  if (Array.isArray(value.results)) html += value.results.map((p,i) => `<div class="policy"><strong>${esc(p.policy_id)}</strong> · ${esc(p.title)} <small>score ${esc(p.score)}</small>${evidence(p.snippet,tid,oid,`output.results.${i}.snippet`)}</div>`).join('');
  if (value.policy_id && value.body) html += `<div class="policy"><strong>${esc(value.policy_id)}</strong> · ${esc(value.title)}${evidence(value.body,tid,oid,'output.body')}</div>`;
  const formatted = list || value.results || value.body;
  if (formatted) html += `<details><summary>Complete result JSON</summary>${evidence(json(value),tid,oid,'output','prose raw')}</details>`;
  else html += evidence(json(value),tid,oid,'output','prose raw');
  return html;
}

function spanCard(s, trace) {
  const wrapper = ['SPAN','AGENT'].includes(s.type);
  const error = s.level === 'ERROR' || s.output?.ok === false;
  const meta = [s.type, s.model, s.start ? new Date(s.start).toLocaleTimeString() : ''].filter(Boolean).join(' · ');
  let content = '';
  if (wrapper) content = `<details><summary>${esc(s.name)} · ${esc(s.type)} ${s.level === 'ERROR' ? badge('Execution error','error') : ''}</summary>${s.error ? evidence(typeof s.error === 'string' ? s.error : json(s.error),trace.id,s.id,'error') : ''}<p>Observation ${esc(s.id)}</p><p>Parent ${esc(s.parent_id || 'root')}</p></details>`;
  else {
    content = `<div class="card-head"><strong>${esc(s.type === 'GENERATION' ? 'Assistant · model call' : s.name)}</strong><small>${esc(meta)}</small></div>`;
    if (s.type === 'TOOL') {
      content += `<div class="tool-input"><div class="eyebrow">Arguments</div>${evidence(json(s.input),trace.id,s.id,'input','prose raw')}</div><div class="eyebrow">Result</div>${toolResult(s.output,trace.id,s.id)}`;
    } else if (s.type === 'GENERATION') {
      content += s.messages.map((m,i) => evidence(m,trace.id,s.id,`messages.${i}`)).join('');
      if (s.calls.length) content += `<p class="status-line">Calls ${s.calls.length > 1 ? '(parallel group)' : ''}: ${s.calls.map(c => `<code>${esc(c.name)}</code>`).join(' · ')}</p>`;
      content += `<details><summary>Full model request, response & usage</summary><div class="eyebrow">Input · includes repeated history</div>${evidence(json(s.input),trace.id,s.id,'input','prose raw')}<div class="eyebrow">Output</div>${evidence(json(s.output),trace.id,s.id,'output','prose raw')}<pre>${esc(json(s.usage))}</pre></details>`;
    } else content += evidence(json(s.output),trace.id,s.id,'output','prose raw');
    if (s.error) content += `<p class="badge error">${esc(typeof s.error === 'string' ? s.error : json(s.error))}</p>`;
  }
  return `<article class="evidence-card ${wrapper ? 'wrapper' : s.type.toLowerCase()} ${error ? 'error' : ''}" id="span-${esc(s.id)}" data-span="${esc(s.id)}" data-trace-id="${esc(trace.id)}">${content}</article>`;
}

function conversationHTML() {
  return session.map((t,i) => `<section id="turn-${esc(t.id)}"><div class="turn-header ${t.id === current ? 'selected' : ''}" data-turn="${esc(t.id)}"><div class="toolbar-row"><strong>Turn ${i+1}</strong>${button('Review this trace','focus-trace',`data-id="${esc(t.id)}"`)}<a href="${esc(t.url)}" target="_blank" rel="noopener noreferrer">Langfuse ↗</a></div><small>${esc(new Date(t.timestamp).toLocaleString())} · ${esc(t.id)}</small><div>${sampled().has(t.id) ? badge('In review sample') : badge('Context / exploration')}${reviewed(t.id) ? ' '+badge(state.reviews[t.id].status.replaceAll('_',' '),state.reviews[t.id].status === 'first_failure' ? 'pending' : 'good') : ''}</div></div>
    <article class="evidence-card user"><div class="eyebrow">User · ${esc(t.role)}</div>${evidence(t.input,t.id,null,'input')}</article>
    ${t.spans.map(s => spanCard(s,t)).join('')}
    ${t.extra_output ? `<article class="evidence-card generation"><div class="eyebrow">Assistant · final response</div>${evidence(t.extra_output,t.id,null,'output')}</article>` : ''}
    ${t.missing_output ? '<div class="evidence-card error"><strong>No final response was recorded.</strong><p>Inspect the execution details above. A missing response is not an assigned human failure label.</p></div>' : ''}</section>`).join('');
}

function queueRows() {
  const ids = sampled();
  return traces.filter(t => (!filters.q || `${t.scenario_id} ${t.id} ${t.preview}`.toLowerCase().includes(filters.q.toLowerCase())) &&
    (!filters.role || t.role === filters.role) && (!filters.intent || t.intent === filters.intent) && (!filters.group || t.group === filters.group) &&
    (!filters.status || (filters.status === 'sample' ? ids.has(t.id) : filters.status === 'initial' ? initialPicks().some(p => p.trace_id === t.id) : ['dimension','depth','final'].includes(filters.status) ? state.manifest.picks.some(p => p.batch === filters.status && p.trace_id === t.id) : filters.status === 'unreviewed' ? !reviewed(t.id) : reviewed(t.id))));
}
function queueList(revealCurrent = false) {
  const pane = $('.queue'), previousTop = pane.scrollTop;
  const rows = queueRows();
  $('#queue-count').textContent = `${rows.filter(t => reviewed(t.id)).length} / ${rows.length} reviewed`;
  $('#queue-list').innerHTML = rows.map(t => {
    const outcome = state.reviews[t.id]?.status;
    const statusBadge = outcome === 'first_failure' ? badge('Reviewed · failure','pending') : outcome === 'no_failure_observed' ? badge('Reviewed · no failure','good') : badge('Unreviewed');
    return `<button class="queue-item ${t.id === current ? 'current' : ''}" data-action="open" data-id="${esc(t.id)}"><strong>${esc(t.scenario_id)}</strong> ${badge(t.role,t.role)}<div class="preview">${esc(t.preview)}</div><small>${esc(t.intent.replaceAll('_',' '))} · ${short(t.id)}</small><div class="queue-review-status">${statusBadge}</div></button>`;
  }).join('');
  pane.scrollTop = previousTop;
  if (revealCurrent) revealCurrentItem(pane);
}
function options(field, label) {return `<option value="">${label}</option>` + [...new Set(traces.map(t => t[field]))].sort().map(v => `<option value="${esc(v)}" ${filters[field] === v ? 'selected' : ''}>${esc(v.replaceAll('_',' '))}</option>`).join('');}

function navigation() {
  if (!$('#span-list')) return;
  const pane = $('.span-pane'), previousTop = pane.scrollTop;
  const t = currentTrace();
  const notes = notesFor(current);
  $('#span-count').textContent = `${t?.spans.length || 0} spans · trace ${short(current)}`;
  $('#span-list').innerHTML = (t?.spans || []).filter(s => `${s.name} ${s.type}`.toLowerCase().includes(navFilter.toLowerCase())).map(s => {
    const count = notes.filter(n => n.observation_id === s.id).length;
    return `<button class="span-item ${s.type.toLowerCase()} ${s.id === activeSpan ? 'current' : ''}" style="padding-left:${Math.min(s.depth,3)*9+4}px" data-action="jump" data-id="${esc(s.id)}" title="${esc(s.name)}"><span class="dot"></span><span class="span-name">${esc(s.name)}<br><small>${esc(s.type)}</small></span><span>${s.level === 'ERROR' || s.output?.ok === false ? '⚠' : ''}${count ? ' ◇'+count : ''}</span></button>`;
  }).join('');
  pane.scrollTop = previousTop;
  revealCurrentItem(pane);
}

function renderReview() {
  rememberSidebarScroll();
  const previousTop = $('#conversation')?.scrollTop;
  const previousNotesTop = $('#notes-pane')?.scrollTop;
  const expanded = $$('#conversation details').map((el,i)=>el.open ? i : -1).filter(i=>i>=0);
  const t = currentTrace() || byId(current);
  if (!t) {$('#app').innerHTML = '<div class="empty">Select a trace to begin.</div>'; return;}
  const retries = traces.filter(x => x.scenario_id === t.scenario_id && x.session_id !== t.session_id);
  $('#app').innerHTML = `<div class="review-layout ${queueHidden ? 'queue-hidden' : ''} ${navHidden ? 'nav-hidden' : ''}">
    ${queueHidden ? '' : `<aside class="queue"><div class="pane-heading"><strong>Review queue</strong><small id="queue-count"></small></div><div class="queue-filters"><input id="queue-search" placeholder="Search scenarios or messages" aria-label="Search review queue" value="${esc(filters.q)}"><select data-filter="role" aria-label="Filter role">${options('role','All roles')}</select><select data-filter="group" aria-label="Filter scenario group">${options('group','All groups')}</select><select data-filter="intent" aria-label="Filter intent">${options('intent','All intents')}</select><select data-filter="status" aria-label="Filter review status"><option value="">All traces</option><option value="sample" ${filters.status === 'sample' ? 'selected' : ''}>Selected sample</option><option value="initial" ${filters.status === 'initial' ? 'selected' : ''}>Initial 30 traces</option><option value="dimension" ${filters.status === 'dimension' ? 'selected' : ''}>Dimension traces</option><option value="depth" ${filters.status === 'depth' ? 'selected' : ''}>Depth traces</option><option value="final" ${filters.status === 'final' ? 'selected' : ''}>Final 15 traces</option><option value="unreviewed" ${filters.status === 'unreviewed' ? 'selected' : ''}>Unreviewed</option><option value="reviewed" ${filters.status === 'reviewed' ? 'selected' : ''}>Reviewed</option></select></div><div class="queue-list" id="queue-list"></div></aside>`}
    ${navHidden ? '' : `<aside class="span-pane"><div class="pane-heading"><strong>Trace outline</strong></div><small id="span-count"></small><label for="turn-select">Conversation turn</label><select id="turn-select">${session.map((x,i) => `<option value="${esc(x.id)}" ${x.id === current ? 'selected' : ''}>Turn ${i+1} · ${short(x.id)}</option>`).join('')}</select><div class="span-controls">${button('↑ Previous','previous-span')}${button('Next ↓','next-span')}</div><input id="span-search" placeholder="Find a span…" aria-label="Find a span" value="${esc(navFilter)}"><p class="tiny muted">J / K to move · ◇ note · ⚠ execution error</p><div id="span-list"></div></aside>`}
    <div class="conversation-wrap"><div class="conversation-toolbar"><div class="toolbar-row"><span class="eyebrow">Conversation</span><span class="grow"></span>${button(queueHidden ? 'Show queue' : 'Hide queue','toggle-queue','','quiet')}${button(navHidden ? 'Show outline' : 'Hide outline','toggle-nav','','quiet')}</div><h1>${esc(t.scenario_id)} ${badge(t.role,t.role)}</h1><div class="toolbar-row"><small>${esc(t.intent.replaceAll('_',' '))} · ${session.length} turn${session.length === 1 ? '' : 's'} · ${esc(t.group)}</small><span class="grow"></span>${button('Next unreviewed →','next-trace','','quiet')}</div><details><summary>Session and model details${retries.length ? ' · another attempt exists' : ''}</summary><div class="tiny">Session ${esc(t.session_id)}<br>User ${esc(t.user_id)} · prompt ${esc(t.prompt_version)}<br>Models ${esc(session.flatMap(x=>x.models || []).filter((v,i,a)=>a.indexOf(v)===i).join(', '))}</div>${retries.length ? button('Open other attempt','open',`data-id="${esc(retries[0].id)}"`) : ''}</details></div><div id="conversation" class="conversation">${conversationHTML()}</div></div>
    <aside class="notes-pane" id="notes-pane"></aside></div>`;
  if (!queueHidden) queueList();
  updateReviewButtons(); navigation(); renderNotes(); attachObserver();
  restoreSidebarScroll();
  if (previousNotesTop != null) $('#notes-pane').scrollTop = previousNotesTop;
  expanded.forEach(i=>{const el=$$('#conversation details')[i];if(el)el.open=true;});
  if (previousTop != null) $('#conversation').scrollTo({top:previousTop,behavior:'instant'});
  else if (session[0]?.id !== current) document.getElementById('turn-'+current)?.scrollIntoView({block:'start'});
}

function draftKey() {return 'cartwheel-hw4-draft:'+current;}
function readDraft() {try {return JSON.parse(localStorage.getItem(draftKey()) || '{}');} catch {return {};}}
function saveDraft() {
  saveCategoryDraft();
  if ($('#note-text')) localStorage.setItem(draftKey(),json({note:$('#note-text').value, requirement:$('#note-requirement').value, selection, editingNote, noteId:pendingNoteId}));
  for (const form of $$('form[data-draft-key]')) {
    // Closed suggestion editors have not been selected for editing. Do not
    // turn their saved responses into drafts when another form is submitted.
    const editor = form.closest('.suggestion-editor');
    if (editor && !editor.open) continue;
    const values = {};
    for (const el of $$('input,textarea,select',form)) if (el.id) values[el.id] = el.multiple ? [...el.selectedOptions].map(o=>o.value) : el.type === 'checkbox' ? el.checked : el.value;
    localStorage.setItem('cartwheel-hw4-form:'+form.dataset.draftKey,json(values));
  }
}
function restoreForm(form, key) {
  if (!form) return;
  form.dataset.draftKey = key;
  let values = {};
  try {values = JSON.parse(localStorage.getItem('cartwheel-hw4-form:'+key) || '{}');} catch {return;}
  for (const el of $$('input,textarea,select',form)) {
    if (!(el.id in values)) continue;
    if (el.multiple) [...el.options].forEach(o=>o.selected=values[el.id].includes(o.value));
    else if (el.type === 'checkbox') el.checked=values[el.id];
    else el.value=values[el.id];
  }
}
function renderNotes() {
  const draft = readDraft();
  selection = draft.selection || null; editingNote = draft.editingNote || null;
  pendingNoteId = draft.noteId || null;
  refreshEvidenceHighlights();
  const notes = notesFor(current), review = state.reviews[current];
  const completed = reviewed(current);
  const outcome = review?.status === 'first_failure' ? 'First failure recorded' : 'No failure observed';
  const syncMessage = state.outbox['review:'+current]?.status === 'synced' ? 'Saved locally and synced to Langfuse.' : 'Saved locally · Langfuse sync pending.';
  $('#notes-pane').innerHTML = `<div class="pane-heading"><strong>Evidence & notes</strong>${badge(short(current))}</div><p class="muted tiny">Read until the first consequential failure. Select evidence and describe what happened in your own words.</p>
    <div class="active-review" role="status">Reviewing turn ${session.findIndex(t => t.id === current)+1} of ${session.length} · ${esc(short(current))}<small>Your notes and review outcome apply to this trace.</small></div>
    <div id="selection-preview">${selection?.trace_id === current && selection.quote ? `<div class="selection"><strong>Selected evidence</strong><br>${esc(selection.quote)}<div>${button('Clear selected evidence','clear-evidence')}</div><small>Keeps your note text.${editingNote ? ' Save revision to remove the saved highlight.' : ''}</small></div>` : '<p class="tiny muted">Select text in the conversation, or write a trace-level note.</p>'}</div>
    <form id="note-form"><label for="note-text">${editingNote ? 'Revise your note' : 'Your observation'}</label><textarea id="note-text" required placeholder="What did you notice?">${esc(draft.note || '')}</textarea><label for="note-requirement">Requirement reference (optional)</label><input id="note-requirement" placeholder="e.g. RESP-2, or an ambiguous requirement" value="${esc(draft.requirement || '')}"><button class="primary" type="submit">${editingNote ? 'Save revision' : 'Save note'}</button><div class="tiny muted">Draft stays in this browser. Save writes to the local mirror and Langfuse.</div>${editingNote ? button('Cancel edit','cancel-note') : ''}</form>
    <div class="review-outcome"><strong>Open coding · this trace</strong>${completed ? `<div class="review-confirmation ${review.status === 'first_failure' ? 'failure-recorded' : 'no-failure-recorded'}" role="status"><strong>${review.status === 'first_failure' ? '⚠' : '✓'} ${outcome}</strong><span>Review complete</span></div><p class="review-save-status">${syncMessage}</p>${button('Next unreviewed →','next-trace','','primary')}` : '<p>Not reviewed yet</p>'}${button('No failure observed','no-failure')}<label for="first-note">Note describing the first failure</label><select id="first-note"><option value="">Select a saved note</option>${notes.map(n => `<option value="${esc(n.id)}" ${review?.annotation_id === n.id ? 'selected' : ''}>${esc(n.note.slice(0,95))}</option>`).join('')}</select>${button('Mark first failure','first-failure')}${reviewed(current) ? button('Reopen review','reopen','','quiet') : ''}</div>
    <hr><strong>Saved notes · ${notes.length}</strong>${notes.map(n => `<div class="note"><div class="prose">${esc(n.note)}</div>${n.quote ? `<blockquote>“${esc(n.quote)}”</blockquote>` : ''}<small>${esc(n.requirement || '')}</small><small>${esc(n.id)} · ${n.history?.length || 0} revisions</small><small>${state.outbox['note:'+n.id]?.status === 'synced' ? 'Synced to Langfuse' : 'Local / pending sync'}</small>${button('Edit','edit-note',`data-id="${esc(n.id)}"`)} ${n.observation_id ? button('Jump to evidence','jump',`data-id="${esc(n.observation_id)}"`) : ''}${n.history?.length ? `<details><summary>Previous versions</summary>${n.history.map(h=>`<p>${esc(h.note)}</p>`).join('')}</details>` : ''}</div>`).join('')}`;
}

function attachObserver() {
  observer?.disconnect();
  const root = $('#conversation');
  observer = new IntersectionObserver(entries => {
    const candidates = entries.filter(e=>e.isIntersecting && e.target.dataset.traceId === current);
    if (!candidates.length) return;
    const nearest = candidates.sort((a,b)=>Math.abs(a.boundingClientRect.top-root.getBoundingClientRect().top)-Math.abs(b.boundingClientRect.top-root.getBoundingClientRect().top))[0];
    activeSpan = nearest.target.dataset.span;
    $$('.span-item').forEach(el=>el.classList.toggle('current',el.dataset.id === activeSpan));
    const pane = $('.span-pane');
    if (pane) revealCurrentItem(pane);
  }, {root, rootMargin:'-5% 0px -65% 0px', threshold:0});
  $$('[data-span]',root).forEach(el=>observer.observe(el));
}
function focusTrace(tid) {
  saveDraft(); current = tid; selection = null; editingNote = null; pendingNoteId = null; activeSpan = null;
  localStorage.setItem('cartwheel-hw4-current',tid);
  if ($('#turn-select')) $('#turn-select').value = tid;
  $$('.turn-header').forEach(el=>el.classList.toggle('selected',el.dataset.turn === tid));
  updateReviewButtons();
  if (!queueHidden) queueList(true); navigation(); renderNotes();
}
function updateReviewButtons() {
  $$('[data-action="focus-trace"]').forEach(el => {
    const active = el.dataset.id === current;
    el.textContent = active ? 'Reviewing this trace' : 'Review this trace';
    el.classList.toggle('active',active);
    el.setAttribute('aria-pressed',String(active));
  });
}
function jump(id) {
  const target = document.getElementById('span-'+id);
  if (!target) return;
  if (target.dataset.traceId !== current) focusTrace(target.dataset.traceId);
  activeSpan = id; navigation();
  $$('.evidence-card.focused').forEach(el=>el.classList.remove('focused'));
  target.classList.add('focused');
  if (target.classList.contains('wrapper')) $('details',target).open = true;
  target.scrollIntoView({behavior:'smooth',block:'start'});
}
function stepSpan(delta) {
  const spans = currentTrace()?.spans || [];
  const index = spans.findIndex(s=>s.id === activeSpan);
  const next = spans[Math.max(0,Math.min(spans.length-1,index+delta))];
  if (next) jump(next.id);
}
async function openTrace(tid) {
  rememberSidebarScroll();
  observer?.disconnect();
  saveDraft(); selection = null; editingNote = null; pendingNoteId = null; current = tid; activeSpan = null;
  view = 'review'; updateTabs();
  const token = ++loadToken;
  $('#app').innerHTML = '<div class="loading">Loading the complete conversation from Langfuse…</div>';
  const loaded = await api('session?trace_id='+encodeURIComponent(tid));
  if (token !== loadToken) return;
  session = loaded; localStorage.setItem('cartwheel-hw4-current',tid); renderReview();
}
function updateTabs() {$$('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view === view));}
function switchView(next) {
  rememberSidebarScroll();
  saveDraft(); view = next; ++loadToken; observer?.disconnect(); updateTabs();
  if (next === 'review' && !session.some(t => t.id === current)) {
    openTrace(current).catch(e => notice(e.message,true));
  } else render();
}
function render() {
  status();
  ({review:renderReview,explore:renderExplore,taxonomy:renderTaxonomy,labels:renderLabels,progress:renderProgress,suggestions:renderSuggestions,hw5:renderHW5}[view])();
}

function renderExplore() {
  const picks = state.manifest.picks;
  const dimensionPicks = picks.filter(p => p.batch === 'dimension');
  $('#app').innerHTML = `<div class="page"><div class="page-intro"><div class="eyebrow">Breadth & depth</div><h1>Explore the collection</h1><p>Sample traces without selecting only predicted failures. Every selection keeps its method and reason. Companion turns are context, not additional reviewed traces.</p></div>
    <div class="cards"><div class="panel"><h3>1 · Start with 30</h3><p>15 uniform random traces + 15 representatives across clusters of trace features.</p><label for="dimension">Choose the later product dimension now</label><select id="dimension" ${picks.length ? 'disabled' : ''}>${['role','intent','group'].map(d=>`<option value="${d}" ${state.manifest.dimension === d ? 'selected' : ''}>${d}</option>`).join('')}</select><p class="tiny">Recorded before sample review. Seed 41 makes selection reproducible.</p>${initialPicks().length ? `<p class="sample-created">✓ Initial sample created · ${initialPicks().length} traces · ${initialPicks().filter(p => reviewed(p.trace_id)).length} reviewed</p>${button('Review initial 30 traces','review-initial','','primary')}` : button('Create initial sample','sample-initial','','primary')}</div>
    <div class="panel"><h3>2 · Cover the dimension</h3><p>30 additional traces distributed across ${esc(state.manifest.dimension || 'your chosen dimension')}. Previously selected traces are excluded.</p>${dimensionPicks.length ? `<p>✓ Dimension sample created · ${dimensionPicks.length} traces · ${dimensionPicks.filter(p => reviewed(p.trace_id)).length} reviewed</p>${button('Review dimension traces','review-dimension','','primary')}` : button('Add 30 dimension traces','sample-dimension',initialPicks().length ? '' : 'disabled')}</div>
    <div class="panel"><h3>3 · Search in depth</h3><p>Select 25 candidates and close negatives through searches. Record why you selected them below.</p><strong>${picks.filter(p=>p.batch === 'depth').length} / 25 selected</strong>${picks.some(p=>p.batch==='depth') ? button('Review depth traces','review-depth') : ''}</div>
    <div class="panel"><h3>4 · Check the taxonomy</h3><p>After reviewing the first 85 and drafting modes, add 15 fresh uniform traces.</p>${picks.some(p=>p.batch==='final') ? `<p>✓ Final sample saved · ${picks.filter(p=>p.batch==='final').length} traces · ${picks.filter(p=>p.batch==='final' && reviewed(p.trace_id)).length} reviewed</p><p>Check whether the failures fit existing categories or reveal a new consequential mode. Your previous notes are preserved.</p>${button('Review final 15 traces','review-final','','primary')}` : button('Add final 15 random traces','sample-final')}</div></div>
    ${depthEditorHTML(picks.filter(p=>p.batch==='depth'))}
    <div class="split"><div class="panel"><div class="pane-heading"><h2>Trace map</h2>${button(mapData ? 'Reload map' : 'Load live trace map','map')}</div><p>Clusters use recorded message counts, tool calls, retrieval and tokens. No model calls. Position shows tool calls against recorded messages; colour identifies a cluster.</p><div id="map-slot">${mapData ? mapHTML() : '<div class="empty">Load full observations to explore clusters.</div>'}</div></div>
    <div class="panel"><h2>Search the evidence</h2><p>Lexical similarity across complete traces. Results are retrieval suggestions, not judgments.</p><form id="search-form"><input id="depth-query" value="${esc(depthQuery)}" aria-label="Search complete trace content" placeholder="Policy claim, tool name or example wording…"><button class="primary" type="submit">Search live traces</button></form><div class="search-results">${searchResults.map(r=>{const t=byId(r.trace_id);return `<div class="search-row"><input type="checkbox" aria-label="Select ${esc(t.scenario_id)} ${short(t.id)} for depth review" data-depth="${esc(t.id)}" ${depthIds.has(t.id) ? 'checked' : ''} ${sampled().has(t.id) ? 'disabled' : ''}>${button(`${esc(t.scenario_id)} · ${short(t.id)}<br><small>${esc(t.preview.slice(0,150))}</small>`,'open',`data-id="${esc(t.id)}"`)}<small>${r.similarity.toFixed(2)}</small></div>`;}).join('')}</div><label for="depth-reason">Search purpose / selection reason (required)</label><textarea id="depth-reason" required aria-describedby="depth-feedback" placeholder="Candidate mode, search terms, and why these are candidates or close negatives">${esc(depthReason)}</textarea>${button(`Add selected traces to depth batch (${depthIds.size})`,'sample-depth','','primary')}<p id="depth-feedback" class="depth-feedback" role="status" data-error="${depthError}">${esc(depthFeedback)}</p></div></div></div>`;
}
function depthEditorHTML(picks) {
  if (!picks.length) return '';
  return `<details class="panel" id="depth-editor"><summary>Edit depth selection · ${picks.length} traces</summary>
    <p>Tick the traces you added by mistake, then remove them from this batch. Notes, reviews and labels are retained. Removed traces can be selected again through search.</p>
    <div class="actions">${button('Select all for removal','depth-remove-all')}${button('Clear removal selection','depth-remove-none')}</div>
    <div class="depth-edit-list">${picks.map(p=>{const t=byId(p.trace_id);return `<label class="depth-edit-row"><input type="checkbox" data-depth-remove="${esc(p.trace_id)}"><span><strong>${esc(t?.scenario_id || short(p.trace_id))} · ${short(p.trace_id)}</strong> ${badge(t?.role || '')}<br>${esc(t?.preview || '')}<small>Selected because: ${esc(p.reason)}</small><small>${reviewed(p.trace_id) ? 'Reviewed — saved work will be kept' : 'Unreviewed'}</small></span></label>`;}).join('')}</div>
    <label for="depth-remove-reason">Reason for changing the batch</label><input id="depth-remove-reason" value="Accidental selection">
    ${button('Remove selected from depth batch (0)','depth-remove','','primary')}
    <p id="depth-remove-feedback" role="status"></p></details>`;
}

function mapHTML() {
  const maxX=Math.max(1,...mapData.map(d=>d.x)), maxY=Math.max(1,...mapData.map(d=>d.y));
  return `<svg class="map" viewBox="0 0 620 340" role="img" aria-label="Trace feature map: tool calls and recorded messages"><path d="M40 15V305H600" stroke="#aebfb6" fill="none"/><text x="270" y="333">Tool calls (0–${maxX})</text><text x="45" y="15">Recorded messages (0–${maxY})</text>${mapData.map(d=>{const jitter=[...d.id].reduce((a,c)=>a+c.charCodeAt(0),0)%13-6;const t=byId(d.id);return `<a href="#${esc(d.id)}" data-action="open" data-id="${esc(d.id)}" aria-label="Open ${esc(t.scenario_id)} trace ${short(d.id)}"><circle cx="${45+d.x/maxX*540+jitter}" cy="${296-d.y/maxY*265+jitter}" r="5" fill="hsl(${d.cluster*137.5%360} 40% 43%)" stroke="${reviewed(d.id)?'#173d32':'white'}"><title>${esc(t.scenario_id)} · ${short(d.id)} · cluster ${d.cluster} · ${d.x} tools · ${d.y} messages</title></circle></a>`;}).join('')}</svg>`;
}
function renderTaxonomy() {
  const mode=state.modes.find(m=>m.name===modeName);
  const sources=new Set(mode?.created_from || []);
  const related = mode ? Object.values(state.labels).filter(l=>l.mode===mode.name && l.mode_version===mode.version) : [];
  $('#app').innerHTML = `<div class="page"><div class="page-intro"><div class="eyebrow">From observations to definitions</div><h1>Your failure taxonomy</h1><p>Group observations only after open coding. Keep a binary definition, its boundary, its requirement source and the human notes it came from. Definition revisions make earlier judgments visibly out of date.</p></div><div class="split"><div><div class="mode-list">${state.modes.map(m=>button(`<strong>${esc(m.name)}</strong>${badge(m.status)} <small>version ${m.version}</small><p>${esc(m.definition)}</p>`,'edit-mode',`data-id="${esc(m.name)}"`,m.name===modeName?'active':'')).join('')}</div>${button('+ Draft a mode','new-mode')}${!state.modes.length?'<div class="empty">No categories yet. Start by reviewing traces and writing observations.</div>':''}</div><div class="panel"><form id="mode-form" class="mode-form"><h2>${mode?'Revise mode':'Draft mode'}</h2><label for="mode-name">Name · snake_case</label><input id="mode-name" required pattern="[a-z][a-z0-9_]*" value="${esc(mode?.name)}" ${mode?'readonly':''}><label for="mode-definition">Binary definition</label><textarea id="mode-definition" required>${esc(mode?.definition)}</textarea><label for="mode-boundary">Boundary with the nearest mode</label><textarea id="mode-boundary">${esc(mode?.boundary)}</textarea><label for="mode-requirement">Requirement source</label><input id="mode-requirement" placeholder="SPEC.md requirement ID, or a recorded specification revision" value="${esc(mode?.requirement)}"><label for="mode-evaluator">Likely evaluator</label><select id="mode-evaluator"><option value="">Choose…</option><option value="code" ${mode?.evaluator_type==='code'?'selected':''}>Code check</option><option value="llm_judge" ${mode?.evaluator_type==='llm_judge'?'selected':''}>LLM judge</option></select><label for="mode-sources">Supporting human annotations · select one or more</label><select id="mode-sources" multiple>${state.annotations.map(n=>`<option value="${esc(n.id)}" ${sources.has(n.id)?'selected':''}>${esc(byId(n.trace_id)?.scenario_id || short(n.trace_id))} · ${esc(n.note.slice(0,110))}</option>`).join('')}</select><label for="mode-status">Status</label><select id="mode-status">${['draft','final','retired'].map(s=>`<option ${mode?.status===s?'selected':''}>${s}</option>`).join('')}</select>${mode?'<label for="revision-reason">Why is this definition changing?</label><textarea id="revision-reason" required></textarea>':''}<button class="primary" type="submit">${mode?'Save revision':'Save draft'}</button></form>
    ${mode?`<hr><h3>Evidence for version ${mode.version}</h3><p>${related.filter(l=>l.label===1).length} confirmed positive · ${related.filter(l=>l.close_negative).length} close negative. Aim for at least three of each where the data permits.</p>${related.map(l=>`<p>${badge(l.label?'Present':l.close_negative?'Close negative':'Absent')}${button(esc(byId(l.trace_id)?.scenario_id || l.trace_id),'open',`data-id="${esc(l.trace_id)}"`)} ${esc(l.note)}</p>`).join('')}<h3>Supporting observations</h3>${state.annotations.filter(n=>sources.has(n.id)).map(n=>`<div class="note">${esc(n.note)}<br>${button('Read evidence','open',`data-id="${esc(n.trace_id)}"`)}<small>${esc(n.id)}</small></div>`).join('')}<details><summary>Definition history · ${mode.history?.length || 0} earlier versions</summary>${(mode.history||[]).map(h=>`<p><strong>v${h.version}</strong> ${esc(h.definition)}<br>${esc(h.revision_reason)}</p>`).join('')}</details>`:''}</div></div></div>`;
  restoreForm($('#mode-form'),'mode:'+(mode?.name || 'new'));
}
function proposalFor(tid, mode) {
  const p=state.label_proposals?.[`${tid}:${mode.name}`];
  return p?.mode_version===mode.version?p:null;
}
function categoryDraftKey(mode) {return `cartwheel-hw4-category:${mode.name}:${mode.version}`;}
function categoryDraft(mode) {
  try {return JSON.parse(localStorage.getItem(categoryDraftKey(mode)) || '{}');} catch {return {};}
}
function saveCategoryDraft() {
  const form=$('#category-label-form'), mode=finalModes().find(m=>m.name===form?.dataset.mode);
  if(!mode)return;
  const draft=categoryDraft(mode);
  for(const row of $$('[data-category-trace]',form))draft[row.dataset.categoryTrace]={
    label:$('[data-category-value]',row).value,note:$('[data-category-note]',row).value,
    selected:$('[data-category-select]',row).checked,close_negative:$('[data-category-negative]',row).checked,
  };
  localStorage.setItem(categoryDraftKey(mode),json(draft));
}
function categorySelectionStatus() {
  const form=$('#category-label-form');if(!form)return;
  for(const row of $$('[data-category-trace]',form)){
    const select=$('[data-category-select]',row);
    select.disabled=!['0','1'].includes($('[data-category-value]',row).value) || !$('[data-category-note]',row).value.trim();
    if(select.disabled)select.checked=false;
  }
  const count=$$('[data-category-select]:checked',form).length;
  const submit=$('#confirm-category');submit.textContent=`Confirm selected judgments (${count})`;submit.disabled=!count;
}
function renderCategoryLabels() {
  const modes=finalModes(),ids=reviewSet();
  if(!modes.some(m=>m.name===categoryMode))categoryMode=modes[0]?.name;
  const mode=modes.find(m=>m.name===categoryMode);
  if(!mode)return;
  const draft=categoryDraft(mode), pending=ids.filter(id=>!currentLabel(id,mode));
  const values=new Map(pending.map(id=>{const p=proposalFor(id,mode);return [id,{label:p?.label,note:p?.note || '',close_negative:p?.close_negative,...draft[id]}];}));
  const idsShown=pending.filter(id=>{const v=values.get(id).label;return categoryFilter==='all' || (categoryFilter==='needs' ? !['0','1'].includes(String(v)) : String(v)===(categoryFilter==='present'?'1':'0'));});
  const confirmed=ids.reduce((n,id)=>n+modes.filter(m=>currentLabel(id,m)).length,0);
  $('#app').innerHTML=`<div class="page"><div class="page-intro"><div class="eyebrow">Structured judgments</div><h1>Review judgments by category</h1><p>${confirmed} / ${ids.length*modes.length} confirmed. Review the reasons together, open a conversation when needed, and select the judgments you agree with. Saving confirms only the selected rows.</p><div class="actions">${button('Review by category','labels-category','','active')}${button('Review by trace','labels-trace')}</div></div>
    <div class="panel"><label for="category-mode">Failure category</label><select id="category-mode">${modes.map(m=>`<option value="${esc(m.name)}" ${m.name===mode.name?'selected':''}>${esc(m.name)} · ${ids.filter(id=>!currentLabel(id,m)).length} remaining</option>`).join('')}</select><p>${esc(mode.definition)}</p><details><summary>Boundary and requirement</summary><p>${esc(mode.boundary)}</p><p>${esc(mode.requirement)}</p></details><label for="category-filter">Show remaining judgments</label><select id="category-filter">${[['all','All remaining'],['needs','Needs your decision'],['present','Proposed present'],['absent','Proposed absent']].map(([v,t])=>`<option value="${v}" ${v===categoryFilter?'selected':''}>${t}</option>`).join('')}</select><p>${idsShown.length} shown · ${pending.length} remaining for this category. Previously confirmed judgments can be edited in Review by trace.</p></div>
    <form id="category-label-form" data-mode="${esc(mode.name)}"><div class="panel category-actions"><div class="actions">${button('Select all shown with a decision','category-select-all')}${button('Clear selection','category-select-none')}<button id="confirm-category" class="primary" type="submit" disabled>Confirm selected judgments (0)</button></div><p>Unresolved rows cannot be selected until you choose Present or Absent and supply a reason. Other categories and hidden rows are not saved.</p></div>
    ${idsShown.map(id=>{const v=values.get(id),p=proposalFor(id,mode),valid=['0','1'].includes(String(v.label));return `<section class="panel" data-category-trace="${esc(id)}"><div class="actions"><h2>${esc(byId(id)?.scenario_id)} · ${short(id)}</h2>${button('Read conversation','open',`data-id="${esc(id)}"`)}</div><p>${esc(byId(id)?.preview)}</p><p><strong>Proposed evidence:</strong> ${esc(p?.note || 'No proposal available; inspect the conversation.')}</p><p class="tiny">${esc((p?.evidence_span_ids || []).join(' · '))}</p><label for="category-value-${id}">Your judgment</label><select id="category-value-${id}" data-category-value><option value="">Needs your decision</option><option value="1" ${String(v.label)==='1'?'selected':''}>Present · Fail · 1</option><option value="0" ${String(v.label)==='0'?'selected':''}>Absent · Pass · 0</option></select><details><summary>Edit evidence / reason</summary><textarea aria-label="Evidence for ${esc(byId(id)?.scenario_id)} ${short(id)}" data-category-note>${esc(v.note)}</textarea><label><input type="checkbox" data-category-negative ${v.close_negative?'checked':''}>Close negative example (absent only)</label></details><label><input type="checkbox" data-category-select ${valid && v.selected?'checked':''} ${valid?'':'disabled'}>Include this judgment in confirmation</label></section>`;}).join('') || '<div class="panel empty">No remaining judgments in this filter. Choose another category or filter.</div>'}</form></div>`;
  categorySelectionStatus();
}
function renderLabels() {
  if(labelLayout==='category' && finalModes().length && reviewSet().length)return renderCategoryLabels();
  const modes=finalModes(), ids=reviewSet();
  if (!ids.includes(current) && ids.length) current=ids[0];
  const pending=ids.filter(id=>modes.some(m=>!currentLabel(id,m)));
  const confirmed=ids.reduce((n,id)=>n+modes.filter(m=>currentLabel(id,m)).length,0);
  $('#app').innerHTML = `<div class="page"><div class="page-intro"><div class="eyebrow">Structured judgments</div><h1>Apply the final modes</h1><p>Review every category for each trace. Proposed judgments are AI suggestions, not saved human labels. Check the evidence, correct any proposal, then confirm the trace. “Needs your decision” is never counted as absent.</p><p>${ids.length*modes.length} trace/category pairs · ${confirmed} confirmed · ${ids.length*modes.length-confirmed} remaining across ${pending.length} traces.</p></div>${!modes.length || !ids.length?'<div class="panel empty">The taxonomy needs to be finalized before judgments can be confirmed. Prepared proposals are preserved separately.</div>':`
    <div class="panel"><div class="actions">${button('Review by category','labels-category')}${button('Review by trace','labels-trace','','active')}</div><label for="label-trace">Reviewed trace</label><select id="label-trace">${ids.map(id=>`<option value="${esc(id)}" ${id===current?'selected':''}>${esc(byId(id)?.scenario_id)} · ${short(id)}${modes.every(m=>currentLabel(id,m))?' · confirmed':''}</option>`).join('')}</select><div class="actions">${button('Open complete conversation','open',`data-id="${esc(current)}"`)}${button('Next trace needing judgments','next-label-trace')}</div></div>
    <form id="trace-label-form" class="panel"><h2>Judgments for ${esc(byId(current)?.scenario_id)} · ${short(current)}</h2>
    ${modes.map((m,i)=>{
      const old=currentLabel(current,m),p=proposalFor(current,m), value=old || p;
      return `<section class="label-mode-row" data-mode="${esc(m.name)}"><h3>${esc(m.name)} ${badge(old?'Confirmed':p?'Proposed · needs confirmation':'Needs your decision',old?(old.label?'error':'good'):'pending')}</h3><p>${esc(m.definition)}</p><details><summary>Boundary and requirement</summary><p>${esc(m.boundary)}</p><p>${esc(m.requirement)}</p></details>
      ${p?`<p><strong>Proposed evidence:</strong> ${esc(p.note)}</p><p class="tiny">${esc((p.evidence_span_ids || []).join(' · '))}</p>`:''}
      <label for="trace-label-${i}">Is this failure present?</label><select id="trace-label-${i}" data-label required><option value="">Needs your decision</option><option value="1" ${value?.label===1?'selected':''}>Present · Fail · 1</option><option value="0" ${value?.label===0?'selected':''}>Absent · Pass · 0</option></select>
      <label for="trace-reason-${i}">Evidence / reason</label><textarea id="trace-reason-${i}" data-reason required>${esc(value?.note || '')}</textarea><label><input id="trace-negative-${i}" data-negative type="checkbox" ${value?.close_negative?'checked':''}>Close negative example (absent only)</label><hr></section>`;
    }).join('')}<button type="submit" class="primary">Confirm ${modes.length} judgments for this trace</button><p class="tiny">Saves your judgments to Langfuse and the per-mode label files. Previous judgments remain in history.</p></form>
    <div class="panel matrix"><h2>Review matrix</h2><p>Proposed values remain unconfirmed until you save them above. Click any cell to review that trace.</p><table class="wide-table"><thead><tr><th>Trace</th>${modes.map(m=>`<th>${esc(m.name)}</th>`).join('')}</tr></thead><tbody>${ids.map(id=>`<tr><td>${esc(byId(id)?.scenario_id)}<br><small>${short(id)}</small></td>${modes.map(m=>{const l=currentLabel(id,m),p=proposalFor(id,m);return `<td>${button(l?(l.label?'Present':'Absent'):p?.label===1?'Proposed present':p?.label===0?'Proposed absent':'Needs decision','label-cell',`data-id="${esc(id)}" data-mode="${esc(m.name)}"`,l?'active':'')}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`}</div>`;
  if(modes.length)restoreForm($('#trace-label-form'),`trace-labels:${current}:${modes.map(m=>m.name+':'+m.version).join(',')}`);
}

function renderProgress() {
  const picks=state.manifest.picks, ids=reviewSet(), modes=finalModes();
  const filled=ids.reduce((n,id)=>n+modes.filter(m=>currentLabel(id,m)).length,0);
  const batches=[['initial_random','Initial · uniform',15],['initial_cluster','Initial · clusters',15],['dimension','Product dimension',30],['depth','Depth search',25],['final','Final uniform',15]];
  $('#app').innerHTML = `<div class="page"><div class="eyebrow">Coverage & completion</div><h1>Review progress</h1><p>Counts are distinct traces, not conversations. Browsing a companion turn does not mark it reviewed.</p><div class="metrics"><div class="metric"><strong>${ids.length} / 100</strong><span>Selected traces reviewed</span></div><div class="metric"><strong>${picks.length}</strong><span>Distinct traces selected</span></div><div class="metric"><strong>${modes.length}</strong><span>Final modes · target 5–8</span></div><div class="metric"><strong>${ids.length*modes.length-filled}</strong><span>Incomplete or stale judgments</span></div></div><div class="split"><div class="panel"><h2>Sampling batches</h2><table class="wide-table"><thead><tr><th>Batch</th><th>Selected</th><th>Reviewed</th></tr></thead><tbody>${batches.map(([key,title,n])=>{const ps=picks.filter(p=>p.batch===key);return `<tr><td>${title}</td><td>${ps.length} / ${n}</td><td>${ps.filter(p=>reviewed(p.trace_id)).length}</td></tr>`;}).join('')}</tbody></table><p>Chosen dimension: ${esc(state.manifest.dimension || 'not selected yet')}</p><h3>Reviewed sample composition</h3>${['role','group','intent'].map(field=>`<p><strong>${field}:</strong> ${[...new Set(ids.map(id=>byId(id)?.[field]))].map(value=>`${esc(value)} ${ids.filter(id=>byId(id)?.[field]===value).length}`).join(' · ') || 'None yet'}</p>`).join('')}</div><div class="panel"><h2>Sample fractions</h2><p>These describe the reviewed sample, not population prevalence. Only judgments for the current mode version count.</p><table class="wide-table"><thead><tr><th>Mode</th><th>Present / reviewed</th><th>Judged</th><th>Close negatives</th></tr></thead><tbody>${modes.map(m=>{const ls=ids.map(id=>currentLabel(id,m)).filter(Boolean),pos=ls.filter(l=>l.label===1).length;return `<tr><td>${esc(m.name)}</td><td>${pos} / ${ids.length}${ls.length===ids.length&&ids.length?' ('+(100*pos/ids.length).toFixed(1)+'%)':' · incomplete'}</td><td>${ls.length} / ${ids.length}</td><td>${ls.filter(l=>l.close_negative).length}</td></tr>`;}).join('')}</tbody></table><p>${state.suggestions.filter(s=>s.status==='rejected').length} rejected suggestions retained · ${state.modes.reduce((n,m)=>n+(m.history?.length||0),0)} taxonomy revisions.</p></div></div><div class="panel"><h2>Still to document</h2><p>The final-batch assessment of newly discovered consequential modes, Workshop findings, specification decisions and your video remain human review work. This screen does not certify those deliverables.</p></div></div>`;
}
function renderSuggestions() {
  const scroll = $('.page')?.scrollTop || 0;
  $('#app').innerHTML=`<div class="page"><div class="page-intro"><div class="eyebrow">Hypotheses, separate from human notes</div><h1>Suggestions for your review</h1><p>Read the evidence before accepting a suggestion. Acceptance saves your wording as a human-confirmed note. It does not mark the trace reviewed or assign a binary label. Use Edit decision to revise a saved response; previous versions stay in the history.</p></div>${state.suggestions.length?'':'<div class="panel empty">No suggestions yet. Later searches and Workshop hypotheses will appear here.</div>'}${state.suggestions.map((s,i)=>{
    const decided=s.status!=='pending', reasonId=`suggestion-reason-${i}`, decisionId=`suggestion-decision-${i}`;
    const form=`<form data-suggestion="${esc(s.id)}" data-revise="${decided}">
      ${decided?`<label for="${decisionId}">Decision</label><select id="${decisionId}" name="decision"><option value="accepted" ${s.status==='accepted'?'selected':''}>Accept as a note</option><option value="rejected" ${s.status==='rejected'?'selected':''}>Reject suggestion</option></select>`:''}
      <label for="${reasonId}">Your decision / revised observation</label><textarea id="${reasonId}" required placeholder="Accept in your own words, or explain why this suggestion does not apply">${esc(s.decision_reason || '')}</textarea>
      <div class="actions">${decided?'<button type="submit" class="primary">Save changes</button>':'<button type="submit" name="decision" value="accepted" class="primary">Accept as a note</button><button type="submit" name="decision" value="rejected">Reject suggestion</button>'}</div>
      ${decided?'<p class="tiny">Updates the linked note if one exists. Previous decisions are retained; trace reviews and binary labels are unchanged.</p>':''}</form>`;
    return `<div class="panel suggestion"><div class="pane-heading"><h3>${esc(byId(s.trace_id)?.scenario_id || short(s.trace_id))}</h3>${badge(s.status || 'pending')}</div><p>${esc(s.text)}</p>${s.quote?`<blockquote>${esc(s.quote)}</blockquote>`:''}<p class="tiny">Source: ${esc(s.source)} · ${esc(s.id)}</p>${button('Read complete conversation','open',`data-id="${esc(s.trace_id)}"`)}${decided?`<p><strong>Your decision:</strong> ${esc(s.decision_reason)}</p><details class="suggestion-editor"><summary>Edit decision</summary>${form}</details>`:form}
      ${s.history?.length?`<details><summary>Previous decisions (${s.history.length})</summary>${s.history.map(h=>`<p>${badge(h.status)} · ${esc(h.decided_at)}<br>${esc(h.decision_reason)}</p>`).join('')}</details>`:''}</div>`;
  }).join('')}</div>`;
  for (const form of $$('form[data-suggestion]')) {
    const s=state.suggestions.find(s=>s.id===form.dataset.suggestion);
    const key=`suggestion:${s.id}:${s.decided_at || 'pending'}`;
    restoreForm(form,key);
    // Restore draft text without opening an editor. Editing always starts
    // with the reviewer's explicit click, including after another card saves.
  }
  $('.page').scrollTop=scroll;
}

document.addEventListener('click', async event => {
  const tab=event.target.closest('[data-view]');
  if(tab){switchView(tab.dataset.view);return;}
  const el=event.target.closest('[data-action]'); if(!el)return;
  event.preventDefault();
  const action=el.dataset.action,id=el.dataset.id;
  if(action.startsWith('hw5-'))return;
  const originalContent=el.innerHTML, originalDisabled=el.disabled;
  try {
    if(action==='dismiss')return notice('');
    if(action==='labels-category' || action==='labels-trace'){
      saveDraft();labelLayout=action==='labels-category'?'category':'trace';renderLabels();return;
    }
    if(action==='category-select-all' || action==='category-select-none'){
      $$('[data-category-select]:not(:disabled)').forEach(c=>{c.checked=action==='category-select-all';});
      categorySelectionStatus();saveCategoryDraft();return;
    }
    if(action==='depth-remove-all' || action==='depth-remove-none'){
      $$('[data-depth-remove]').forEach(c=>{c.checked=action==='depth-remove-all';});
      $('[data-action="depth-remove"]').textContent=`Remove selected from depth batch (${$$('[data-depth-remove]:checked').length})`;
      return;
    }
    if(action==='depth-remove'){
      const ids=$$('[data-depth-remove]:checked').map(c=>c.dataset.depthRemove);
      const reason=$('#depth-remove-reason').value.trim();
      if(!ids.length || !reason){$('#depth-remove-feedback').textContent=!ids.length?'Select the traces to remove.':'Enter a reason for the change.';return;}
      el.textContent='Updating depth batch…';
      await mutate('sample',{stage:'depth_remove',trace_ids:ids,reason});
      renderExplore();
      notice(`Removed ${ids.length} traces from the depth batch. ${state.manifest.picks.filter(p=>p.batch==='depth').length} / 25 remain. Notes and reviews were kept; you can now select replacements.`);
      return;
    }
    if(action==='open')return await openTrace(id);
    if(action==='jump')return jump(id);
    if(['review-initial','review-dimension','review-depth','review-final'].includes(action)){
      const batch=action.replace('review-','');
      const picks=batch==='initial' ? initialPicks() : state.manifest.picks.filter(p=>p.batch===batch), next=picks.find(p=>!reviewed(p.trace_id)) || picks[0];
      if(!next)return notice('Create this sample first.');
      filters={q:'',role:'',intent:'',group:'',status:batch};queueHidden=false;
      await openTrace(next.trace_id);
      notice(batch==='final' ? 'Showing the saved final 15. Use the left queue to revisit each trace and its notes; check for new failure types, not another full labeling pass.' : `Showing the ${batch} ${picks.length} traces in the review queue. Next unreviewed stays within this batch.`);
      return;
    }
    if(action==='focus-trace'){
      focusTrace(id);document.getElementById('turn-'+id)?.scrollIntoView({block:'start'});
      notice(`Turn ${session.findIndex(t => t.id === id)+1} selected for review. The outline and notes now refer to trace ${short(id)}. Choose a review outcome when you finish.`);
      return;
    }
    if(action==='previous-span')return stepSpan(-1);
    if(action==='next-span')return stepSpan(1);
    if(action==='toggle-queue'){saveDraft();queueHidden=!queueHidden;renderReview();return;}
    if(action==='toggle-nav'){saveDraft();navHidden=!navHidden;renderReview();return;}
    if(action==='next-trace'){
      const pool=queueRows(),at=pool.findIndex(t=>t.id===current),rotated=[...pool.slice(at+1),...pool.slice(0,at+1)];
      const next=rotated.find(t=>!reviewed(t.id));
      return next?await openTrace(next.id):notice('No unreviewed traces remain in this queue filter.');
    }
    if(action==='cancel-note'){localStorage.removeItem(draftKey());selection=null;editingNote=null;pendingNoteId=null;renderNotes();return;}
    if(action==='clear-evidence'){
      selection=null;window.getSelection()?.removeAllRanges();saveDraft();renderNotes();
      $('#note-text').focus();return;
    }
    if(action==='edit-note'){
      const n=state.annotations.find(n=>n.id===id);selection=n;editingNote=n.id;
      localStorage.setItem(draftKey(),json({note:n.note,requirement:n.requirement,selection,editingNote}));renderNotes();return;
    }
    if(action==='edit-mode'){saveDraft();modeName=id;renderTaxonomy();return;}
    if(action==='new-mode'){saveDraft();modeName='';renderTaxonomy();return;}
    if(action==='label-cell'){saveDraft();labelLayout='trace';current=id;labelMode=el.dataset.mode;renderLabels();$(`section[data-mode="${CSS.escape(labelMode)}"]`)?.scrollIntoView({block:'start'});return;}
    if(action==='next-label-trace'){
      saveDraft();const ids=reviewSet(),at=ids.indexOf(current),pool=[...ids.slice(at+1),...ids.slice(0,at+1)];
      const next=pool.find(id=>finalModes().some(m=>!currentLabel(id,m)));
      if(next){current=next;renderLabels();}else notice('All traces have current judgments.');return;
    }
    if(action==='map'){
      el.disabled=true;el.textContent='Loading full observations…';
      mapData=await api('map');if(view==='explore')renderExplore();return;
    }
    el.disabled=true;
    if(action==='sync')await mutate('sync',{});
    else if(action==='no-failure')await mutate('review',{trace_id:current,status:'no_failure_observed'});
    else if(action==='first-failure')await mutate('review',{trace_id:current,status:'first_failure',annotation_id:$('#first-note').value});
    else if(action==='reopen')await mutate('review',{trace_id:current,status:'unreviewed'});
    else if(action.startsWith('sample-')){
      const stage=action.replace('sample-','');
      if(stage==='depth'){
        depthReason=$('#depth-reason').value;saveDepthDraft();
        if(!depthIds.size){depthStatus('Select at least one new trace before adding to the depth batch.',true);el.disabled=false;return;}
        if(!depthReason.trim()){
          depthStatus('Enter a search purpose / selection reason above. Your selected traces have been kept.',true);
          $('#depth-reason').focus();el.disabled=false;return;
        }
        depthStatus(`Saving ${depthIds.size} selected traces…`);
      }
      const payload={stage,dimension:$('#dimension')?.value,trace_ids:[...depthIds],reason:$('#depth-reason')?.value};
      el.textContent=stage==='depth' ? 'Saving selected traces…' : 'Selecting from live traces…';
      await mutate('sample',payload);
      if(stage==='depth'){
        depthStatus(`Added ${payload.trace_ids.length} traces to the depth batch. ${state.manifest.picks.filter(p=>p.batch==='depth').length} / 25 selected. Open Review depth traces to continue.`);
        depthIds.clear();depthReason='';saveDepthDraft();
      }
    }
    saveDraft();render();
    if(['first-failure','no-failure','reopen'].includes(action)){
      const message = action === 'reopen' ? 'Review reopened.' : action === 'first-failure' ? 'Review complete — first failure recorded.' : 'Review complete — no failure observed.';
      const synced = state.outbox['review:'+current]?.status === 'synced';
      notice(message + (synced ? ' Saved locally and synced to Langfuse.' : ' Saved locally; Langfuse sync is pending. Use Retry sync.'),!synced);
    }
  }catch(error){notice(error.message,true);if(action==='depth-remove' && $('#depth-remove-feedback'))$('#depth-remove-feedback').textContent=error.message;if(action==='sample-depth')depthStatus(error.message+' Your selection and reason have been kept.',true);el.innerHTML=originalContent;el.disabled=originalDisabled;}
});

document.addEventListener('submit',async event=>{
  if(event.target.id==='hw5-form' || event.target.matches('[data-hw5-disagreement]'))return;
  event.preventDefault();const form=event.target,submit=event.submitter;
  if(submit)submit.disabled=true;
  try{
    if(form.id==='note-form'){
      pendingNoteId ||= crypto.randomUUID();
      saveDraft();await mutate('note',{...(selection?.trace_id===current?selection:{}),id:editingNote || pendingNoteId,trace_id:current,note:$('#note-text').value,requirement:$('#note-requirement').value});
      localStorage.removeItem(draftKey());selection=null;editingNote=null;pendingNoteId=null;renderReview();
    }else if(form.id==='mode-form'){
      const payload={name:$('#mode-name').value,definition:$('#mode-definition').value,boundary:$('#mode-boundary').value,requirement:$('#mode-requirement').value,evaluator_type:$('#mode-evaluator').value,status:$('#mode-status').value,created_from:[...$('#mode-sources').selectedOptions].map(o=>o.value),revision_reason:$('#revision-reason')?.value};
      await mutate('mode',payload);localStorage.removeItem('cartwheel-hw4-form:'+form.dataset.draftKey);modeName=payload.name;renderTaxonomy();
    }else if(form.id==='category-label-form'){
      saveCategoryDraft();
      const mode=finalModes().find(m=>m.name===form.dataset.mode);
      const selected=$$('[data-category-trace]',form).filter(row=>$('[data-category-select]',row).checked);
      if(!selected.length)throw new Error('Select at least one reviewed judgment to confirm.');
      const items=selected.map(row=>{
        const tid=row.dataset.categoryTrace,value=$('[data-category-value]',row).value,note=$('[data-category-note]',row).value.trim();
        if(!['0','1'].includes(value) || !note)throw new Error('Each selected row needs Present or Absent and an evidence reason.');
        if(currentLabel(tid,mode))throw new Error('A selected judgment has already been confirmed. Refresh state before saving.');
        return {trace_id:tid,mode:mode.name,mode_version:mode.version,label:Number(value),note,close_negative:$('[data-category-negative]',row).checked};
      });
      await mutate('label_batch',{items});
      const draft=categoryDraft(mode);
      for(const item of items){
        delete draft[item.trace_id];
        localStorage.removeItem('cartwheel-hw4-form:trace-labels:'+item.trace_id+':'+finalModes().map(m=>m.name+':'+m.version).join(','));
      }
      localStorage.setItem(categoryDraftKey(mode),json(draft));renderLabels();
      const pending=items.some(i=>state.labels[`${i.trace_id}:${i.mode}`]?.sync_status!=='synced');
      notice(`${items.length} judgments confirmed for ${mode.name}.`+(pending?' Saved locally; Langfuse sync is pending.':' Saved locally and synced to Langfuse.'),pending);
    }else if(form.id==='trace-label-form'){
      saveDraft();
      const items=$$('section[data-mode]',form).map(row=>({
        trace_id:current,mode:row.dataset.mode,mode_version:finalModes().find(m=>m.name===row.dataset.mode).version,
        label:$('[data-label]',row).value===''?null:Number($('[data-label]',row).value),
        note:$('[data-reason]',row).value,close_negative:$('[data-negative]',row).checked,
      }));
      await mutate('label_batch',{items});localStorage.removeItem('cartwheel-hw4-form:'+form.dataset.draftKey);renderLabels();
      const pending=items.some(i=>state.labels[`${i.trace_id}:${i.mode}`]?.sync_status!=='synced');
      notice(`${items.length} judgments saved locally.`+(pending?' Langfuse sync is pending.':' Synced to Langfuse.'),pending);
    }else if(form.id==='label-form'){
      await mutate('label',{trace_id:current,mode:labelMode,label:Number($('#label-value').value),note:$('#label-note').value,close_negative:$('#close-negative').checked});localStorage.removeItem('cartwheel-hw4-form:'+form.dataset.draftKey);renderLabels();
    }else if(form.id==='search-form'){
      const q=$('#depth-query').value; if(!q.trim())throw new Error('Enter search wording.');
      depthQuery=q;searchResults=await api('search?q='+encodeURIComponent(q));saveDepthDraft();if(view==='explore')renderExplore();
    }else if(form.dataset.suggestion){
      saveDraft();
      const decision=$('select[name="decision"]',form)?.value || submit?.value;
      await mutate('suggestion',{id:form.dataset.suggestion,decision,reason:$('textarea',form).value,revise:form.dataset.revise==='true'});
      localStorage.removeItem('cartwheel-hw4-form:'+form.dataset.draftKey);
      renderSuggestions();
      const pending=Object.values(state.outbox).some(o=>o.status!=='synced');
      notice('Suggestion decision saved locally. Previous versions are retained in the history.'+(pending?' Some Langfuse saves are pending; see the sync status above.':''),pending);
    }
  }catch(error){notice(error.message,true);}finally{if(submit)submit.disabled=false;}
});

document.addEventListener('input',event=>{
  const el=event.target;
  if(el.closest('#category-label-form')){categorySelectionStatus();saveCategoryDraft();}
  if(el.id==='queue-search'){filters.q=el.value;queueList();}
  if(el.id==='depth-query'){depthQuery=el.value;saveDepthDraft();}
  if(el.id==='depth-reason'){depthReason=el.value;saveDepthDraft();}
  if(el.id==='span-search'){navFilter=el.value;navigation();}
  if(['note-text','note-requirement'].includes(el.id))saveDraft();
  if(el.closest('form[data-draft-key]'))saveDraft();
});
document.addEventListener('change',event=>{
  const el=event.target;
  if(el.id==='category-mode' || el.id==='category-filter'){
    saveCategoryDraft();if(el.id==='category-mode')categoryMode=el.value;else categoryFilter=el.value;
    renderLabels();return;
  }
  if(el.closest('#category-label-form')){categorySelectionStatus();saveCategoryDraft();}
  if(el.dataset.filter){filters[el.dataset.filter]=el.value;queueList();}
  if(el.id==='turn-select'){focusTrace(el.value);document.getElementById('turn-'+current).scrollIntoView({block:'start'});}
  if(el.id==='label-trace'){saveDraft();current=el.value;renderLabels();}
  if(el.id==='label-mode'){saveDraft();labelMode=el.value;renderLabels();}
  if(el.closest('form[data-draft-key]'))saveDraft();
  if(el.dataset.depthRemove){$('[data-action="depth-remove"]').textContent=`Remove selected from depth batch (${$$('[data-depth-remove]:checked').length})`;}
  if(el.dataset.depth){if(el.checked)depthIds.add(el.dataset.depth);else depthIds.delete(el.dataset.depth);saveDepthDraft();$('[data-action="sample-depth"]').textContent=`Add selected traces to depth batch (${depthIds.size})`;}
});
document.addEventListener('mouseup',event=>{
  if(busy)return;
  if(!event.target.closest('#conversation'))return;
  const picked=window.getSelection();if(!picked || picked.isCollapsed || !picked.rangeCount)return;
  const range=picked.getRangeAt(0), start=(range.startContainer.nodeType===Node.TEXT_NODE?range.startContainer.parentElement:range.startContainer).closest('[data-evidence]');
  if(!start || !start.contains(range.endContainer))return;
  const prefix=range.cloneRange();prefix.selectNodeContents(start);prefix.setEnd(range.startContainer,range.startOffset);
  const quote=range.toString(),offset=prefix.toString().length;
  if(!quote.trim())return;
  if(start.dataset.trace!==current)focusTrace(start.dataset.trace);
  selection={trace_id:current,observation_id:start.dataset.obs || null,field:start.dataset.field,quote,start:offset,end:offset+quote.length};
  saveDraft();renderNotes();$('#note-text').focus();
});
document.addEventListener('keydown',event=>{
  if(view!=='review' || event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input,textarea,select,button,[contenteditable],dialog'))return;
  if(event.key==='j'){event.preventDefault();stepSpan(1);}if(event.key==='k'){event.preventDefault();stepSpan(-1);}
});
$('#spec-button').onclick=()=>{$('#spec-text').textContent=spec;$('#spec-dialog').showModal();};
$('#close-spec').onclick=()=>$('#spec-dialog').close();
$('#refresh').onclick=async()=>{try{saveDraft();state=await api('state');notice('');render();}catch(e){notice(e.message,true);}};
window.addEventListener('beforeunload',saveDraft);
async function boot(){
  try{
    const result=await api('bootstrap');state=result.state;traces=result.traces;source=result.source;spec=result.spec;status();
    try{
      const draft=JSON.parse(localStorage.getItem('cartwheel-hw4-depth-draft') || '{}');
      depthIds=new Set((draft.ids || []).filter(id=>byId(id) && !sampled().has(id)));
      depthQuery=draft.query || '';depthReason=draft.reason || '';
      searchResults=(draft.results || []).filter(r=>byId(r.trace_id));
    }catch{ /* Ignore an unreadable browser draft; saved workspace data is unaffected. */ }
    if(result.offline_reason)notice('Offline review: '+result.offline_reason);
    current=localStorage.getItem('cartwheel-hw4-current');if(!byId(current))current=traces[0]?.id;
    if(current)await openTrace(current);
  }catch(error){notice(error.message,true);$('#app').innerHTML='<div class="empty">The live collection could not be loaded. Check Langfuse, then reload this page.</div>';}
}
boot();
