'use strict';
let hw5Initial = true, hw5AllVersions = false;
function hw5Runs() {
  const runs=hw5State.development || [];
  return hw5AllVersions ? runs : runs.filter(r => r.version === Math.max(...runs.filter(x=>x.model===r.model).map(x=>x.version)));
}
let hw5State, hw5Current, hw5Session = [], hw5Filter = 'pending', hw5Token = 0, hw5Saving = false;
const hw5DraftKey = () => 'cartwheel-hw5-label:'+hw5Current;
function hw5SaveDraft() {
  if (!$('#hw5-note')) return;
  localStorage.setItem(hw5DraftKey(),json({note:$('#hw5-note').value,label:$('#hw5-value').value}));
}
function hw5Rows() {
  if (hw5Filter === 'dev' || hw5Filter === 'disagreements') return hw5State.rows.filter(r => hw5Runs().some(run => run.predictions[r.trace_id] && (hw5Filter === 'dev' || run.predictions[r.trace_id].disagrees)));
  return hw5State.rows.filter(r => hw5Filter === 'all' || (hw5Filter === 'pending' ? !hw5State.labels[r.trace_id] : !!hw5State.labels[r.trace_id]));
}
async function renderHW5(tid) {
  hw5SaveDraft();
  const token = ++hw5Token;
  try {
    hw5State = await api('hw5');
    if(token !== hw5Token || view !== 'hw5')return;
    if(!hw5State.rows.length){$('#app').innerHTML='<div class="empty">No HW5 queue has been prepared.</div>';return;}
    if(hw5Initial && hw5State.development?.some(r=>Object.keys(r.predictions).length)){hw5Filter='disagreements';hw5Initial=false;}
    const rows = hw5Rows();
    hw5Current = tid || (rows.some(r=>r.trace_id===hw5Current) ? hw5Current : rows[0]?.trace_id);
    if(!hw5Current){drawHW5();return;}
    $('#app').innerHTML='<div class="loading">Loading the HW5 conversation…</div>';
    const loaded = await api('session?trace_id='+encodeURIComponent(hw5Current));
    if(token !== hw5Token || view !== 'hw5')return;
    const at=loaded.findIndex(t=>t.id===hw5Current);
    if(at<0)throw new Error('The selected trace is unavailable. Your saved labels are unchanged.');
    // Later replies cannot explain the reply being judged.
    hw5Session=loaded.slice(0,at+1);
    drawHW5();
  }catch(e){if(view==='hw5'){notice(e.message,true);$('#app').innerHTML='<div class="empty">Unable to load this HW5 trace. Refresh state to retry.</div>';}}
}
function drawHW5() {
  const counts=hw5State.counts, row=hw5State.rows.find(r=>r.trace_id===hw5Current), saved=hw5State.labels[hw5Current];
  let draft={};try{draft=JSON.parse(localStorage.getItem(hw5DraftKey()) || '{}');}catch{}
  const value=draft.label ?? saved?.label ?? '', note=draft.note ?? saved?.note ?? '';
  $('#app').innerHTML=`<div class="hw5-header"><h1>HW5 · Response relevance</h1><p><strong>${counts.Pass} / 30 Pass · ${counts.Fail} / 30 Fail</strong> · ${counts.pending} candidates remain. ${counts.Pass>=30 && counts.Fail>=30 ? 'Label collection complete. Use Development disagreements to review the model decisions.' : 'Review until both classes reach 30. You do not need to finish every candidate.'}</p><p>Judge only whether the final reply contains unnecessary detail. Other failures do not automatically make this category Fail.</p><details><summary>Pass / Fail boundary and saved data</summary><p><strong>Pass:</strong> the reply’s details help answer this request, identify the item, explain a decision, report an action or give a necessary next step. <strong>Fail:</strong> a specific passage can be removed without losing any of those. Explain what can be removed and why.</p><p>Length alone is not a failure. Preserve requested calculations, necessary explanations of inconsistent data, action identifiers and required policy citations. Do not judge model-only narration. See SPEC.md RESP-6.</p><p>Existing HW4 human decisions were reused; candidates are unlabelled. Saved locally to analysis/state/hw5_labels/${esc(hw5State.mode)}.jsonl using Pass=1 / Fail=0. HW4 labels are unchanged. No model calls or Langfuse score writes.</p><p>${esc(hw5State.independence_status)}</p></details></div>
  <div class="hw5-layout"><aside class="queue"><label><input type="checkbox" id="hw5-all-versions" ${hw5AllVersions?'checked':''}> Include earlier judge versions</label><label for="hw5-filter">Review queue</label><select id="hw5-filter">${[['disagreements','Development disagreements'],['dev','All development predictions'],['pending','Needs your decision'],['saved','Saved decisions'],['all','All HW5 traces']].map(([v,l])=>`<option value="${v}" ${v===hw5Filter?'selected':''}>${l}</option>`).join('')}</select>${hw5Rows().map(r=>{const l=hw5State.labels[r.trace_id];return `<button class="queue-item ${r.trace_id===hw5Current?'current':''}" data-action="hw5-open" data-id="${esc(r.trace_id)}"><strong>${esc(r.scenario_id)}</strong><div>${l ? badge(l.label===1?'Pass':'Fail',l.label===1?'good':'pending') : badge('Needs decision')}</div></button>`;}).join('')}</aside>
  <div class="hw5-conversation">${row ? `<h2>${esc(row.scenario_id)}</h2><p>${esc(row.selection_reason)}</p>${hw5Session.map(t=>`<section class="hw5-turn"><h3>${t.id===hw5Current?'Reply to evaluate':'Earlier conversation context'} · ${esc(short(t.id))}</h3><article class="evidence-card user"><strong>User</strong><div class="prose">${esc(t.input)}</div></article><article class="evidence-card generation"><strong>Assistant · final reply</strong><div class="prose">${esc(t.output)}</div></article><details><summary>Inspect ${t.spans.length} spans, tool calls and results</summary>${t.spans.map(s=>spanCard(s,t)).join('')}</details></section>`).join('')}` : '<p>No traces in this filter. You can view or edit saved decisions using the queue filter.</p>'}</div>
  <aside class="notes-pane">${row ? `${hw5PredictionsHTML()}<h2>Your decision</h2><p>${saved ? `Saved ${saved.label===1?'Pass':'Fail'} · ${saved.source==='reused_hw4_human_label'?'reused from HW4':'your HW5 review'}. You can edit it below.`:'No decision saved yet.'}</p><form id="hw5-form"><label for="hw5-value">Response relevance</label><select id="hw5-value" required><option value="">Choose a verdict</option><option value="1" ${String(value)==='1'?'selected':''}>Pass · no irrelevant detail</option><option value="0" ${String(value)==='0'?'selected':''}>Fail · irrelevant detail present</option></select><label for="hw5-note">Evidence / reason</label><textarea id="hw5-note" required placeholder="For Fail, quote the removable passage and explain why. For Pass, briefly explain why the details are needed.">${esc(note)}</textarea><button class="primary" type="submit">${saved?'Save changes':'Save decision'}</button></form><p id="hw5-feedback" role="status">${draft.note!==undefined?'Unsaved draft restored.':''}</p>${button('Next candidate →','hw5-next')}<p class="tiny muted">Saving stays on this trace. Use Next candidate when ready. Earlier turns provide context; judge the final marked reply.</p>`:''}</aside></div>`;
  const pane=$('.hw5-layout .queue');if(pane)revealCurrentItem(pane);
}
document.addEventListener('click',event=>{
  const el=event.target.closest('[data-action^="hw5-"]');if(!el || hw5Saving)return;
  if(el.dataset.action==='hw5-open')renderHW5(el.dataset.id);
  if(el.dataset.action==='hw5-next'){
    const rows=['dev','disagreements'].includes(hw5Filter)?hw5Rows():hw5State.rows, at=rows.findIndex(r=>r.trace_id===hw5Current);
    const next=[...rows.slice(at+1),...rows.slice(0,at)].find(r=>['dev','disagreements'].includes(hw5Filter) || !hw5State.labels[r.trace_id]);
    if(next){if(!['dev','disagreements'].includes(hw5Filter))hw5Filter='pending';renderHW5(next.trace_id);}else notice('No unlabelled candidates remain. Return to your agent to check the class counts.');
  }
});
document.addEventListener('change',event=>{
  if(event.target.id==='hw5-all-versions'){hw5AllVersions=event.target.checked;renderHW5();}
  if(event.target.id==='hw5-filter'){hw5SaveDraft();hw5Filter=event.target.value;renderHW5();}
  if(event.target.id==='hw5-value')hw5SaveDraft();
});
document.addEventListener('input',event=>{if(event.target.id==='hw5-note')hw5SaveDraft();});
document.addEventListener('submit',async event=>{
  if(event.target.id!=='hw5-form')return;
  event.preventDefault();if(hw5Saving)return;
  hw5SaveDraft();hw5Saving=true;
  const token=hw5Token, tid=hw5Current, key=hw5DraftKey();
  const body={trace_id:tid,label:Number($('#hw5-value').value),note:$('#hw5-note').value,revision:hw5State.revision};
  const controls=$$('button,input,textarea,select',event.target);controls.forEach(e=>e.disabled=true);
  try{
    const result=await api('hw5-label',body);
    localStorage.removeItem(key);
    if(token===hw5Token && view==='hw5'){
      hw5State=result;drawHW5();$('#hw5-feedback').textContent='Saved locally. Your decision is recorded; use Next candidate to continue.';
    }
  }catch(e){notice(e.message,true);}finally{hw5Saving=false;controls.forEach(e=>e.disabled=false);}
});
window.addEventListener('beforeunload',hw5SaveDraft);

function hw5PredictionsHTML() {
  return hw5Runs().filter(run=>run.predictions[hw5Current]).map(run=>{
    const p=run.predictions[hw5Current], review=p.review;
    return `<section class="panel"><strong>${esc(run.model)} · v${run.version}</strong><p>${esc(run.id)}</p>${badge(p.label===1?'Pass':'Fail',p.label===1?'good':'pending')} ${badge(p.disagrees?'Disagrees with you':'Agrees with you',p.disagrees?'pending':'good')}<p class="prose">${esc(p.critique || 'No written critique: Jev returns structured decisions only.')}</p>${p.probabilities?`<p>Pass probability ${Math.round(p.probabilities.Pass*100)}% · confidence ${Math.round(p.confidence*100)}%</p>`:''}${review?`<p>Reviewed: ${esc(review.decision.replaceAll('_',' '))}</p>`:''}${p.disagrees || review ? `<form data-hw5-disagreement="${esc(run.id)}"><label>Your assessment<select name="decision" required><option value="">Choose an assessment</option>${[['judge_wrong','Judge is wrong'],['human_label_wrong','My label needs correcting'],['boundary_unclear','Definition needs clarification']].map(([v,l])=>`<option value="${v}" ${review?.decision===v?'selected':''}>${l}</option>`).join('')}</select></label><label>Reason<textarea name="reason" required>${esc(review?.reason || '')}</textarea></label><button type="submit">Save assessment</button><p class="tiny">This records your assessment. If your label is wrong, edit it below as well.</p></form>`:''}</section>`;
  }).join('');
}
document.addEventListener('submit',async event=>{
  const form=event.target;if(!form.matches('[data-hw5-disagreement]'))return;
  event.preventDefault();if(hw5Saving)return;hw5Saving=true;
  const button=$('button',form);button.disabled=true;
  try{
    hw5SaveDraft();hw5State=await api('hw5-disagreement',{run_id:form.dataset.hw5Disagreement,trace_id:hw5Current,decision:$('select',form).value,reason:$('textarea',form).value});
    drawHW5();notice('Assessment saved. Your human label has not been changed.');
  }catch(e){notice(e.message,true);}finally{hw5Saving=false;button.disabled=false;}
});
