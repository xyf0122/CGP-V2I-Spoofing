"""Optional diagnostic redraws; original manuscript figures are preserved."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, FancyArrowPatch
from matplotlib.lines import Line2D
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RESULTS, FIGURES = ROOT / 'results', ROOT / 'figures' / 'diagnostic_redraws'
FIGURES.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':8, 'axes.labelsize':8,
                     'xtick.labelsize':7, 'ytick.labelsize':7, 'pdf.fonttype':42,
                     'ps.fonttype':42, 'axes.linewidth':.7, 'savefig.facecolor':'white'})
COLORS = ['#2c7bb6', '#fdae61', '#d7191c']


def read(name):
    return pd.read_csv(RESULTS / f'{name}.csv')


def save(fig, name):
    fig.savefig(FIGURES / f'{name}.pdf', metadata={'Author':'', 'Creator':'CGP reproducibility scripts', 'CreationDate':None})
    plt.close(fig)


def strip(ax, title):
    ax.add_patch(Rectangle((0, 1), 1, .075, transform=ax.transAxes, clip_on=False, facecolor='black'))
    ax.text(.5, 1.035, title, transform=ax.transAxes, ha='center', va='center', color='white', weight='bold', fontsize=9)
    ax.grid(axis='y', color='#e6e6e6', lw=.55)
    ax.set_axisbelow(True)


def stars(p):
    return '***' if p < .001 else '**' if p < .01 else '*' if p < .05 else 'ns'


def paired_plot(frame, group, order, labels, metric, filename, tests=False):
    paired = frame.pivot(index='participant_id', columns=group, values=metric)[order]
    fig, ax = plt.subplots(figsize=(2.65, 3.65))
    fig.subplots_adjust(left=.24, bottom=.16, right=.96, top=.9)
    x = np.arange(1, len(order) + 1)
    ax.plot(x, paired.to_numpy().T, color='#777777', lw=.5, alpha=.35, zorder=1)
    boxes = ax.boxplot([paired[v].to_numpy() for v in order], positions=x, widths=.48,
                       patch_artist=True, showfliers=False,
                       medianprops={'color':'black','linewidth':.9},
                       whiskerprops={'linewidth':.7}, capprops={'linewidth':.7})
    for patch, color in zip(boxes['boxes'], COLORS):
        patch.set(facecolor=color, alpha=.85, linewidth=.7)
    for j, val in enumerate(order):
        ax.scatter(np.full(len(paired), j+1), paired[val], s=12, color='white', edgecolor='black', lw=.4, zorder=3)
    ax.set_xticks(x, labels)
    ax.set_ylabel('MAE (mph)' if metric == 'MAE' else 'MSE (mph²)')
    strip(ax, metric)
    maximum = paired.to_numpy().max()
    if tests:
        comparisons = [(i,j) for i in range(len(order)) for j in range(i+1,len(order))]
        raw = []
        for i,j in comparisons:
            delta=(paired[order[i]]-paired[order[j]]).to_numpy()
            method='exact' if np.all(delta!=0) and len(np.unique(abs(delta)))==len(delta) else 'approx'
            raw.append(stats.wilcoxon(delta,method=method,correction=(method=='approx')).pvalue)
        raw = np.asarray(raw)
        rank = np.argsort(raw)
        adjusted = np.empty(len(raw))
        adjusted[rank] = np.minimum(1,np.minimum.accumulate((raw[rank]*len(raw)/np.arange(1,len(raw)+1))[::-1])[::-1])
        for k, ((i,j), p) in enumerate(zip(comparisons,adjusted)):
            y = maximum * (1.08 + .14*k)
            ax.plot([i+1,i+1,j+1,j+1],[y-.02*maximum,y,y,y-.02*maximum],c='black',lw=.6)
            ax.text((i+j+2)/2,y+.005*maximum,stars(p),ha='center',va='bottom',fontsize=7)
        ax.set_ylim(0, maximum*(1.16+.14*(len(comparisons)-1)))
    else:
        ax.set_ylim(bottom=0)
    save(fig, filename)


def primary_plots():
    primary = read('primary_metrics')
    for metric in ['MAE','MSE']:
        paired_plot(primary,'model',['ConstDecel','SafeEnv','CGP'],['Const\nDecel','SafeEnv','CGP'],metric,f'FigR2_boxplot_{metric}')
        wins=read('win_rates').query('metric == @metric').set_index('baseline').loc[['ConstDecel','SafeEnv']]
        fig,ax=plt.subplots(figsize=(2.65,3.65));fig.subplots_adjust(left=.24,bottom=.16,right=.96,top=.9)
        fractions=wins.wins/wins.participants
        se=np.sqrt(fractions*(1-fractions)/(wins.participants-1))
        ax.bar([1,2],fractions,color=COLORS[:2],width=.52,edgecolor='black',lw=.7)
        ax.errorbar([1,2],fractions,yerr=se,fmt='none',ecolor='black',capsize=3,lw=.7)
        for x,(_,row) in enumerate(wins.iterrows(),1):
            ax.text(x,.08,f'{row.wins}/32',ha='center',weight='bold')
        ax.set(xticks=[1,2],xticklabels=['ConstDecel','SafeEnv'],ylim=(0,1.1),ylabel='Win rate (CGP < baseline)')
        ax.set_yticks(np.arange(0,1.01,.2),[f'{v}%' for v in range(0,101,20)])
        strip(ax,metric);save(fig,f'FigR3_winrate_{metric}')
    residual=read('trajectory_reconstructions')
    fig,axes=plt.subplots(8,4,figsize=(10,7.5),sharex=True)
    fig.subplots_adjust(left=.07,right=.99,bottom=.065,top=.965,hspace=.8,wspace=.2)
    for n,(pid,group) in enumerate(residual.groupby('participant_id')):
        ax=axes.flat[n]
        for level,(model,color) in enumerate(zip(['ConstDecel','SafeEnv','CGP'],COLORS)):
            g=group.query('model == @model')
            height=g.residual_mph.to_numpy()/15
            ax.fill_between(g.time_s,level,level+height,color=color,alpha=.85,lw=0)
            ax.axhline(level,c='#dddddd',lw=.5)
        ax.axvline(group.t2_hat.iloc[0],ls='--',color='black',lw=.6)
        ax.set_title(pid,fontsize=7,pad=2)
        ax.set_ylim(-1.1,3.2);ax.invert_yaxis()
        ax.set_yticks([0,1,2],['ConstDecel','SafeEnv','CGP'] if n%4==0 else ['', '', ''])
        ax.tick_params(axis='both',length=0,labelsize=6)
        ax.set_xticks([0,5,10,15]);ax.grid(axis='x',c='#e5e5e5',lw=.4)
        for spine in ax.spines.values():spine.set_visible(False)
    fig.supxlabel('Time from RLCD onset (s)',fontsize=9,y=.015)
    save(fig,'FigR1_ridgeline')


def constraint_plots():
    frame=read('constraint_metrics');table=read('table3_constraints')
    fig,ax=plt.subplots(figsize=(5.5,3.15));fig.subplots_adjust(left=.16,right=.98,bottom=.23,top=.9)
    for i,(name,color) in enumerate(zip(['C1','C2','C3','C4'],['#2c7bb6','#abd9e9','#fdae61','#d7191c'])):
        g=frame.query('constraint == @name');rate=g.violations/g.samples
        jitter=np.linspace(-.13,.13,len(g))
        ax.scatter(i+jitter,rate*100,s=16,color=color,edgecolors='black',lw=.35)
        overall=table.query('constraint == @name').violation_rate.iloc[0]*100
        ax.scatter(i,overall,s=45,marker='D',color='black',zorder=4)
        ax.text(i,rate.max()*100+.32,f'{overall:.2f}%',ha='center',fontsize=8)
    ax.set_xticks(range(4),['Nonnegative\nspeed','Bounded\nacceleration','Bounded\njerk','No stop-line\novershoot'])
    ax.set_ylabel('Violation rate per participant (%)');ax.set_ylim(-.35,5.5)
    ax.grid(axis='y',color='#eeeeee');ax.set_axisbelow(True)
    save(fig,'FigR5_constraint_compliance')
    states=read('simulated_states')
    fig,ax=plt.subplots(figsize=(5.5,3.15));fig.subplots_adjust(left=.17,right=.98,bottom=.18,top=.97)
    signals=[states.observed_acceleration_ftps2,states.acceleration_ftps2]
    bodies=ax.violinplot(signals,positions=[1,2],showextrema=False,showmedians=True)
    for body,color in zip(bodies['bodies'],COLORS):body.set(facecolor=color,edgecolor='black',alpha=.7,linewidth=.7)
    bodies['cmedians'].set(color='black',linewidth=1)
    ax.boxplot(signals,positions=[1,2],widths=.13,showfliers=False,medianprops={'color':'black'})
    ax.set_xticks([1,2],['Observed','CGP']);ax.set_ylabel('Acceleration (ft/s²)')
    ax.axhline(0,c='#888888',ls='--',lw=.7);save(fig,'FigR6_violin_accel')


def marginal_axes():
    fig=plt.figure(figsize=(4.7,4.7))
    ax=fig.add_axes([.15,.14,.68,.68])
    top=fig.add_axes([.15,.84,.68,.12],sharex=ax)
    side=fig.add_axes([.85,.14,.12,.68],sharey=ax)
    top.axis('off');side.axis('off')
    return fig,ax,top,side


def density(top,side,x,y):
    xx=np.linspace(min(x)-np.std(x),max(x)+np.std(x),200)
    yy=np.linspace(min(y)-np.std(y),max(y)+np.std(y),200)
    top.fill_between(xx,stats.gaussian_kde(x)(xx),color='#aaaaaa',edgecolor='black',lw=.6)
    side.fill_betweenx(yy,stats.gaussian_kde(y)(yy),color='#aaaaaa',edgecolor='black',lw=.6)


def discussion_plots():
    f=read('discussion_features')
    scores=read('pca_scores').merge(f,on='participant_id')
    variance=read('pca_variance').explained_fraction
    fig,ax,top,side=marginal_axes()
    for k,g in scores.groupby('cluster'):
        color=COLORS[int(k)-1]
        for proactive,gg in g.groupby(g.t2_hat<5):
            ax.scatter(gg.PC1,gg.PC2,c=color,marker='o' if proactive else '^',s=30,edgecolor='black',lw=.6)
        if len(g)>=3:
            covariance=np.cov(g[['PC1','PC2']].to_numpy().T)
            eigenvalues,eigenvectors=np.linalg.eigh(covariance)
            angle=np.degrees(np.arctan2(eigenvectors[1,-1],eigenvectors[0,-1]))
            width,height=2*np.sqrt(eigenvalues[::-1]*stats.chi2.ppf(.95,2))
            ax.add_patch(Ellipse(g[['PC1','PC2']].mean().to_numpy(),width,height,angle=angle,facecolor=color,edgecolor=color,alpha=.16))
            ax.add_patch(Ellipse(g[['PC1','PC2']].mean().to_numpy(),width,height,angle=angle,fill=False,edgecolor=color,lw=.8))
    ax.set_xlabel(f'PC1 ({variance.iloc[0]*100:.1f}%)');ax.set_ylabel(f'PC2 ({variance.iloc[1]*100:.1f}%)')
    ax.legend(handles=[Line2D([],[],marker='o',ls='',color='black',markerfacecolor='white',label='Before 5 s'),
                       Line2D([],[],marker='^',ls='',color='black',markerfacecolor='white',label='At/after 5 s')],loc='lower right',fontsize=7,frameon=False)
    density(top,side,scores.PC1,scores.PC2);save(fig,'discussion_pca_marginal')
    d=f.merge(read('timing_clusters'),on='participant_id')
    fit=read('timing_regression')
    fig,ax,top,side=marginal_axes()
    for k,g in d.groupby('cluster'):
        ax.scatter(g.ttb0,g.t2_hat,s=18+3*abs(g.a_post),c=COLORS[int(k)-1],edgecolor='black',lw=.5,alpha=.8)
    ax.plot(fit.ttb0,fit.fit,c='black',ls='--',lw=1)
    ax.fill_between(fit.ttb0,fit.lwr,fit.upr,color='#aaaaaa',alpha=.2)
    slope,intercept,r,p,_=stats.linregress(d.ttb0,d.t2_hat)
    ax.text(.04,.96,f'y = {intercept:.2f} + {slope:.2f}x\nR² = {r*r:.3f}; p = {p:.3f}',transform=ax.transAxes,va='top',fontsize=8)
    ax.set_xlabel('Initial time-to-boundary (s)');ax.set_ylabel('Commitment time (s)')
    density(top,side,d.ttb0,d.t2_hat);save(fig,'discussion_t2_vs_ttb_marginal')
    correlation=pd.read_csv(RESULTS/'discussion_correlations.csv',index_col=0)
    labels=['t₂','TTB₀','Slack₀','v₀','d₀','a_pre','a_post','Δa','Jerk₉₅','v_min']
    fig,ax=plt.subplots(figsize=(6.5,4.8));fig.subplots_adjust(left=.04,right=.99,bottom=.16,top=.98)
    names=list(correlation.columns);n=len(names)
    cmap=plt.get_cmap('RdYlBu');norm=plt.Normalize(-1,1)
    for i in range(n):
        ax.text(i+.1,i-.2,labels[i],fontsize=7,ha='left')
        for j in range(i):
            value=correlation.iloc[i,j]
            ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor='white',edgecolor='#999999',lw=.4))
            size=.85*np.sqrt(abs(value))
            ax.add_patch(Rectangle((j-size/2,i-size/2),size,size,facecolor=cmap(norm(value)),edgecolor='none'))
            pvalue=stats.pearsonr(f[names[i]],f[names[j]]).pvalue
            if pvalue<.05:ax.text(j,i,stars(pvalue),ha='center',va='center',fontsize=7)
    mantel=read('mantel_results')
    endpoints={'Demo':(8,-.2),'Att':(10,2.8),'Post':(11,6)}
    for block,(x,y) in endpoints.items():
        for _,row in mantel.query('spec == @block').iterrows():
            i=names.index(row.env)
            color='#d7191c' if row.p<.01 else '#fdae61' if row.p<.05 else '#bdbdbd'
            width=.45 if row.r<.2 else 1.0 if row.r<.4 else 1.7
            ax.add_patch(FancyArrowPatch((i,i-.35),(x,y),arrowstyle='-',connectionstyle='arc3,rad=-.08',color=color,lw=width,alpha=.85))
        ax.scatter(x,y,marker='D',c='#2c7bb6',s=28,zorder=4);ax.text(x+.3,y,block,fontsize=8,va='center')
    ax.set_xlim(-.7,13);ax.set_ylim(9.7,-1.6);ax.set_aspect('equal')
    ax.set_xticks(range(n-1),labels[:-1],rotation=90);ax.tick_params(length=0)
    ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(False)
    colorax=fig.add_axes([.028,.55,.018,.22]);fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=colorax).set_label('Pearson r',fontsize=7)
    fig.legend(handles=[Line2D([],[],c=c,lw=1,label=l) for c,l in [('#d7191c','p < .01'),('#fdae61','.01 ≤ p < .05'),('#bdbdbd','p ≥ .05')]],
              loc='upper left',bbox_to_anchor=(.003,.43),fontsize=6,frameon=False,title='Mantel p',title_fontsize=7)
    fig.legend(handles=[Line2D([],[],c='#777777',lw=w,label=l) for w,l in [(.45,'r < .2'),(1,'.2 ≤ r < .4'),(1.7,'r ≥ .4')]],
              loc='upper left',bbox_to_anchor=(.003,.24),fontsize=6,frameon=False,title='Mantel r',title_fontsize=7)
    save(fig,'discussion_corr_mantel')


def main():
    primary_plots();constraint_plots()
    for metric in ['MAE','MSE']:
        paired_plot(read('ablation_metrics'),'variant',['Full','Without gate','Without UGM'],['Full','Without\ngate','Without\nUGM'],metric,f'FigR7_ablation_paired_box_{metric}',True)
        paired_plot(read('downsampling_metrics'),'resolution_hz',[10,5],['10 Hz','5 Hz'],metric,f'FigR8_downsampling_paired_box_{metric}',True)
    discussion_plots()
    print(f'Generated {len(list(FIGURES.glob("*.pdf")))} empirical figure PDFs.')


if __name__=='__main__':main()
