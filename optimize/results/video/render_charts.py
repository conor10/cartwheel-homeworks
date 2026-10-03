"""Regenerate HW8 video figures from recorded results; no API calls."""
import csv
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/hw8-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'optimize/results'
OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.facecolor': '#f7f9fc', 'axes.facecolor': '#f7f9fc',
                     'text.color': '#203047', 'axes.labelcolor': '#203047'})

def save(fig, name):
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)

manual = list(csv.DictReader((RESULTS / 'manual.csv').open()))
gepa = json.loads((RESULTS / 'gepa-result.json').read_text())
selection = json.loads((RESULTS / 'final-selection.json').read_text())
final = json.loads((ROOT / selection['final_development_result']).read_text())
fig, (a, b) = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={'width_ratios': [1.15, 1]})
fig.subplots_adjust(top=.77, bottom=.30, wspace=.30, left=.07, right=.97)
fig.suptitle('HW8 · The development experiment', x=.07, ha='left', y=.96, fontsize=24, weight='bold')
fig.text(.07, .89, 'Same agent model throughout: GLM-5.2  •  Seven development cases  •  Two target escalation cases', fontsize=12)
for ax in (a,b):
    ax.set_ylim(0, 4)
    ax.set_yticks(range(5))
    ax.set_ylabel('Development cases passed / 7')
    ax.grid(axis='y', alpha=.16)
    ax.set_axisbelow(True)
vals = [round(float(r['dev_score']) * 7) for r in manual]
a.bar(range(4), vals, color=['#8b98a9','#d78863','#59a4a0','#167a75'], width=.6)
a.set_xticks(range(4), ['Starting', 'Prompt\nreverted', 'Tool\nkept', 'Tool +\nharness kept'])
a.set_title('1. Manual changes', loc='left', weight='bold', pad=20)
for i,v in enumerate(vals):
    a.text(i,v+.13,f'{v}/7',ha='center',weight='bold')
    a.text(i,3.78,['Target: 0/2','0/2','1/2','2/2'][i],ha='center',fontsize=10,color='#59687b')
gvals=[round(s*7) for s in gepa['development_scores']] + [round(final['score']*7)]
b.plot(range(3),gvals,marker='o',markersize=10,color='#6557a7',linewidth=2)
b.set_xticks(range(3), ['Fresh GEPA\nbaseline', 'GEPA\ncandidate', 'Final\nrerun'])
b.set_xlim(-.3,2.3)
b.set_title('2. GEPA on retained tool + harness',loc='left',weight='bold',pad=20)
for i,v in enumerate(gvals):
    b.text(i,v+.17,f'{v}/7',ha='center',weight='bold')
fig.text(.07,.15,'GEPA: 20 search evaluations, one proposed revision. Claude Opus 4.6 proposed the wording; GLM ran the cases.',fontsize=12)
fig.text(.07,.105,'The fresh GEPA baseline fell to 1/7: results vary between runs. The selected prompt matched the best manual result.',fontsize=11)
fig.text(.07,.06,'Small sample; four cases use a response-detail judge with missing request context. Scores are observations, not reliable success rates.',fontsize=10,color='#59687b')
save(fig,'development-path')

rows=list(csv.DictReader((RESULTS/'frontier.csv').open()))
fig, ax=plt.subplots(figsize=(12,7))
fig.subplots_adjust(left=.10,right=.96,top=.79,bottom=.26)
fig.suptitle('HW8 · Accuracy versus cost',x=.10,ha='left',y=.95,fontsize=25,weight='bold')
fig.text(.10,.88,'Final test comparison  •  Three cases per configuration  •  Agent model-call costs only',fontsize=12)
x=[float(r['cost_per_100_conversations_usd']) for r in rows]
y=[float(r['score']) for r in rows]
ax.plot([x[2],x[3]],[y[2],y[3]],color='#167a75',ls='--',alpha=.65)
ax.scatter(x[:2],y[:2],s=110,color='#919aaa',zorder=3)
ax.scatter(x[2:],y[2:],s=130,color='#167a75',zorder=4)
labels=['Starting GPT-5.5\n0/3 · $6.84','Starting Claude Opus 4.6\n0/3 · $3.93','Starting GLM-5.2\n0/3 · $0.68','Final GLM-5.2\n2/3 · $1.37']
for i,label in enumerate(labels):
    ax.annotate(label,(x[i],y[i]),xytext=((15,-8) if i==3 else (0,20)),textcoords='offset points',ha=('left' if i==3 else 'center'),fontsize=12,weight=('bold' if i==3 else 'normal'))
ax.set(xlim=(0,7.9),ylim=(-.10,.86),xlabel='Estimated USD per 100 conversations →',ylabel='Cases passed')
ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.set_yticks([0,1/3,2/3])
ax.grid(alpha=.15)
fig.text(.10,.15,'Both GLM configurations are on the measured frontier: lower cost versus higher accuracy.',fontsize=12)
fig.text(.10,.105,'GPT and Claude are dominated in this sample. This is not a general ranking of the models.',fontsize=11)
fig.text(.10,.06,'Limits: n = 3; one case exposed during setup; catalogue escalation also encountered an incidental negative price.',fontsize=10,color='#59687b')
save(fig,'accuracy-cost-frontier')
print('Generated two charts in PNG and SVG.')
