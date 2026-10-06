"""Render HW9 video charts and a local presentation from saved evidence. No API calls."""
import csv
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/hw9-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'profile/results/video'
OUT.mkdir(parents=True, exist_ok=True)
TEAL, GRAY, RED, BLUE = '#157b73', '#8493a7', '#b74939', '#4266a8'
BG = '#f7f9fc'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'figure.facecolor':BG,
 'axes.facecolor':BG,'axes.spines.top':False,'axes.spines.right':False,
 'text.color':'#203047','axes.labelcolor':'#203047','xtick.color':'#526178','ytick.color':'#526178'})
def read(path): return json.loads((ROOT/path).read_text())
def csvread(path): return list(csv.DictReader((ROOT/path).open()))
def frame(title, subtitle, n=2):
 fig, axes=plt.subplots(1,n,figsize=(16,9),squeeze=False)
 fig.subplots_adjust(left=.085,right=.96,top=.72,bottom=.26,wspace=.4)
 fig.text(.06,.91,title,fontsize=27,weight='bold')
 fig.text(.06,.85,subtitle,fontsize=15)
 return fig,list(axes[0])
def footer(fig,headline,note):
 fig.text(.06,.14,headline,fontsize=18,weight='bold',color=TEAL)
 fig.text(.06,.075,note,fontsize=12,color='#526178')
def save(fig,name):
 for ext in ['png','svg']: fig.savefig(OUT/f'{name}.{ext}',dpi=150,facecolor=BG)
 plt.close(fig)
def bars(ax,labels,values,title,fmt,colors=None):
 ax.bar(range(len(values)),values,color=colors or [GRAY,TEAL],width=.55)
 ax.set_xticks(range(len(values)),labels)
 ax.set_title(title,loc='left',pad=25,weight='bold',fontsize=16)
 ax.set_ylim(0,max(values)*1.3)
 ax.grid(axis='y',alpha=.15); ax.set_axisbelow(True)
 for i,v in enumerate(values): ax.text(i,v+max(values)*.04,fmt(v),ha='center',weight='bold',fontsize=17)

costs=csvread('profile/results/costs.csv')
fig,axes=frame('A · Where the recorded costs came from','Historical audit of retained records — customer traffic and evaluation activity shown separately')
fig.subplots_adjust(bottom=.33)
c=costs[0]
bars(axes[0],['Support agent'],[float(c['cost_usd'])],'Customer conversations · USD',lambda v:f'${v:.2f}',[BLUE])
axes[0].set_xlabel('server/app.py:201\n1,124 model calls',labelpad=15)
judge=costs[1:]
bars(axes[1],['HW5 GPT\njudges','HW5 Jev','HW7\nmonitoring'],[float(r['cost_usd']) for r in judge], 'Judge calls · USD',lambda v:f'${v:.3f}',[BLUE,TEAL,GRAY])
axes[1].set_xlabel('Largest judge call site: analysis/helpers/scale.py:259',labelpad=15,fontsize=12)
footer(fig,'Focus: customer conversations were the largest recorded cost.','Different panel scales. Not a complete billing history. GPT judge tokens estimated; Jev cost uses recorded tokens × list price.')
save(fig,'01-cost-audit')

b=read('profile/results/part-b-comparison.json')['metrics']
fig,axes=frame('B · Preloading policies increased cost','GLM-5.2 · Same seven development cases · Score unchanged at 3/7',3)
for ax,key,title,fmt in zip(axes,['input_tokens','output_tokens','cost_per_100_conversations_usd'],['Input tokens','Output tokens','USD / 100 conversations'],[lambda v:f'{v:,.0f}',lambda v:f'{v:,.0f}',lambda v:f'${v:.2f}']):
 bars(ax,['Baseline','Preloaded'],[b[key]['baseline'],b[key]['preloaded']],title,fmt,[GRAY,RED])
footer(fig,'REVERTED · Cost rose 8%, despite fewer output tokens.','Input +25%; output −38%. One run per configuration. Saved results do not establish how many policy lookups were avoided.')
save(fig,'02-policy-preloading')

c=read('profile/results/part-c-comparison.json')['metrics']
fig,axes=frame('C · A longer shared prefix did not improve cache hits','GPT-5.5 · Session details moved to the end of the prompt · Score unchanged at 3/7')
bars(axes[0],['Before','After'],[c['cached_fraction'][k]*100 for k in ['before','after']],'Cached share of input tokens (%)',lambda v:f'{v:.1f}%')
bars(axes[1],['Before','After'],[c['cost_per_100_conversations_usd'][k] for k in ['before','after']],'USD / 100 conversations',lambda v:f'${v:.2f}')
footer(fig,'KEPT · Score unchanged; cost fell 1.6%, but caching benefit was not demonstrated.','One seven-case run before and after. Cache warming and routing were uncontrolled. A small cost change may be run variability.')
save(fig,'03-prompt-caching')

rows=csvread('cascade/results/thresholds.csv')
d=read('cascade/results/development-summary.json')
fig,axes=frame('D · Bonsai’s confidence did not predict agreement','Bonsai proxy → Jev fallback · 33 development reviews · Minimum agreement chosen in advance: 95%')
ax=axes[0]
x=[float(r['threshold']) for r in rows]
ax.step(x,[100*float(r['agreement_with_oracle']) for r in rows],where='post',color=BLUE,lw=3,label='Agreement with Jev')
ax.step(x,[100*float(r['proxy_share']) for r in rows],where='post',color=GRAY,lw=2,label='Handled by Bonsai')
ax.axhline(95,color=RED,ls='--',lw=2,label='Required agreement: 95%')
ax.set(xlim=(0,1.02),ylim=(0,105),xlabel='Minimum proxy confidence',ylabel='Share of 33 reviews (%)')
ax.legend(loc='lower left',fontsize=12); ax.grid(alpha=.15)
ax=axes[1]; ax.axis('off')
ax.text(0,.91,'Even at confidence = 1.00',fontsize=20,weight='bold')
for y,big,small in [(.68,'26 / 33','reviews handled by Bonsai'),(.40,'5 disagreements','among those “100% confident” verdicts'),(.12,'84.8% agreement','below the required 95%')]:
 ax.text(0,y,big,fontsize=25,weight='bold',color=RED if y<.5 else BLUE)
 ax.text(0,y-.085,small,fontsize=14)
footer(fig,'REJECTED · No threshold in [0, 1] qualified. Held-out test was not run.','Two malformed outputs fell back to Jev. At threshold 1: human agreement 69.7%; Jev alone 78.8%. Published Bonsai token cost: $0.')
save(fig,'04-judge-cascade')

rows=csvread('profile/results/frontier.csv')
fig,axes=frame('E · The measured HW8 GLM configuration was cheapest','All four configurations scored 3/7 · Frontier considers score and cost only',1)
ax=axes[0]
labels=['HW8 final · GLM','Preloaded policies · GLM','Original prompt order · GPT','Reordered prompt · GPT']
values=[float(r['cost_per_100_conversations_usd']) for r in rows]
ax.barh(range(4),values,color=[TEAL,GRAY,GRAY,GRAY],height=.55)
ax.set_yticks(range(4),labels); ax.invert_yaxis();ax.set_xlim(0,6.3);ax.set_xlabel('USD per 100 conversations')
fig.subplots_adjust(left=.27)
for i,v in enumerate(values):ax.text(v+.09,i,f'${v:.2f}  ·  '+('frontier / selected' if i==0 else 'dominated'),va='center',fontsize=15)
ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
footer(fig,'SELECTED · Measured HW8 GLM: $1.58 per 100 conversations; median latency 4.24s.','Single runs; not proof of equal model quality. Write reliability unavailable. GLM with the later prompt reorder was not measured.')
save(fig,'05-configuration-choice')

slides=[('01-cost-audit','A · Cost audit'),('02-policy-preloading','B · Policy preloading'),('03-prompt-caching','C · Prompt caching'),('04-judge-cascade','D · Judge cascade'),('05-configuration-choice','E · Configuration choice')]
sections=''.join(f'<section><img src="{name}.svg" alt="{label}"></section>' for name,label in slides)
decision=read('cascade/results/decision.json')
sections+=f'''<section class="calc"><div><small>RECALCULATE A SAVED RESULT · DEVELOPMENT ONLY</small><h1>Agreement with Jev</h1><p>33 reviews, with 5 disagreements at confidence = 1.00.</p><label>Reviews <input id="n" type="number" min="1" value="{decision['development_count']}"></label><label>Disagreements <input id="d" type="number" min="0" value="{decision['disagreements_at_strictest_threshold']}"></label><button id="calculate">Recalculate</button><h2 id="answer"></h2><p>Required: 95%. Cascade rejected during development.</p><p class="muted">Changing these calculator inputs does not change the saved evaluation results.</p></div></section>'''
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HW9 · Cost experiments</title><style>
*{box-sizing:border-box}body{margin:0;background:#f7f9fc;color:#203047;font-family:system-ui,sans-serif}header{height:64px;padding:10px 24px;display:flex;align-items:center;gap:14px;border-bottom:1px solid #d8dfe7}header strong{margin-right:auto}button,select,input{font:inherit;border:1px solid #bcc7d4;border-radius:7px;padding:8px 12px;background:white;color:#203047}button{cursor:pointer}button:disabled{opacity:.35;cursor:default}section{display:none;height:calc(100vh - 64px)}section.active{display:flex;align-items:center;justify-content:center}section img{width:100%;height:100%;object-fit:contain}.calc>div{max-width:1100px;padding:40px}h1{font-size:46px}h2{font-size:48px;color:#b74939;min-height:60px}p{font-size:23px;line-height:1.5}small,.muted{color:#526178}.muted{font-size:16px}label{margin-right:18px}input{width:95px}#calculate{background:#157b73;color:white}
</style><header><strong>HW9 · Cost experiments</strong><select id="jump" aria-label="Choose chart">'''+''.join(f'<option>{label}</option>' for _,label in slides)+'''<option>Recalculate agreement</option></select><button id="prev">← Previous</button><span id="page"></span><button id="next">Next →</button><button id="full">Full screen</button></header>'''+sections+'''<script>
const slides=[...document.querySelectorAll('section')];let current=0;const jump=document.querySelector('#jump');function show(i){current=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,n)=>s.classList.toggle('active',n===current));jump.selectedIndex=current;document.querySelector('#page').textContent=`${current+1} / ${slides.length}`;document.querySelector('#prev').disabled=current===0;document.querySelector('#next').disabled=current===slides.length-1}document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);jump.onchange=()=>show(jump.selectedIndex);document.querySelector('#full').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();document.addEventListener('keydown',e=>{if(['INPUT','SELECT','BUTTON'].includes(e.target.tagName))return;if(e.key==='ArrowRight')show(current+1);if(e.key==='ArrowLeft')show(current-1)});document.querySelector('#calculate').onclick=()=>{const n=Number(document.querySelector('#n').value),d=Number(document.querySelector('#d').value);document.querySelector('#answer').textContent=Number.isInteger(n)&&Number.isInteger(d)&&n>0&&d>=0&&d<=n?`(${n} − ${d}) ÷ ${n} × 100 = ${((n-d)/n*100).toFixed(2)}%`:'Enter valid review and disagreement counts.'};show(0);
</script></html>'''
(OUT/'index.html').write_text(html)
print('Generated five PNG/SVG charts and the local video presentation.')
