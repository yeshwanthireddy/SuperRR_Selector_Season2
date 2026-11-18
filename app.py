from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='THE PRESSURE ROOM | Selector Edition',page_icon='🏏',layout='wide',initial_sidebar_state='expanded')
DATA=Path(__file__).resolve().parent/'results'
PINK='#ED2D83'; GOLD='#F4C46C'; GREEN='#33C7A5'; NAVY='#0C1325'; PANEL='#17243A'
st.markdown('''<style>
.stApp{background:linear-gradient(135deg,#0C1325,#101B32 65%,#0B1325);color:#F8F5F9}
[data-testid="stSidebar"]{background:#111B30;border-right:1px solid #31405A}
.block-container{padding-top:1.2rem;max-width:1400px}
h1,h2,h3{color:#FFF7FA!important;letter-spacing:-.025em}
[data-testid="stMetric"]{background:#18263F;border:1px solid #34445F;border-radius:14px;padding:14px}
[data-testid="stMetricValue"]{color:#FFFFFF}
button[data-baseweb="tab"][aria-selected="true"]{color:#FF7FB4!important;border-bottom:2px solid #ED2D83}
.stButton button[kind="primary"]{background:#ED2D83;color:white;border:0}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def read(name):
    p=DATA/name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

def ranked(kind,fmt):
    df=read(f'{kind}_v4_{fmt}.csv')
    if df.empty:return df
    df=df[df['eligible'].astype(str).str.lower().isin(['true','1','yes'])].copy()
    for c in ['matches','deliveries','bootstrap_low','bootstrap_high','score_per_100','positive_match_rate']:
        df[c]=pd.to_numeric(df[c],errors='coerce')
    return df.sort_values('bootstrap_low',ascending=False).reset_index(drop=True)

def short_verdict(p):
    rate=float(p['positive_match_rate'])
    score=float(p['bootstrap_low'])
    matches=int(p['matches'])
    if score>0 and rate>=.7: lead='Strong positive historical evidence in this sample.'
    elif score>0:lead='Positive conservative impact, with mixed match-to-match results.'
    else:lead='The conservative estimate is below the model baseline; evidence is less conclusive.'
    caution=' The IPL sample is relatively limited.' if matches<30 else ''
    return lead+caution+' This is not a prediction of future performance.'

def plot_style(fig,height=400):
    fig.update_layout(template='plotly_dark',paper_bgcolor=PANEL,plot_bgcolor=PANEL,font=dict(color='#F3F5FC'),height=height,
        margin=dict(l=10,r=18,t=28,b=42),showlegend=False)
    fig.update_xaxes(gridcolor='#2A3850')
    fig.update_yaxes(gridcolor='#2A3850')
    return fig

def leaderboard(df):
    if df.empty:
        st.info('No players match these filters.')
        return
    top = df.head(10).copy()
    top.insert(0, 'Rank', range(1, len(top) + 1))
    top['Matches above expectation'] = top['positive_match_rate'].map(lambda v: f'{v:.0%}' if pd.notna(v) else 'N/A')
    top['Evidence'] = top.apply(
        lambda p: 'Promising · smaller sample' if p['bootstrap_low'] > 0 and p['matches'] < 30
        else 'Positive conservative evidence' if p['bootstrap_low'] > 0
        else 'Needs closer review', axis=1
    )
    st.dataframe(
        top[['Rank', 'player_name', 'primary_role', 'matches', 'Matches above expectation', 'Evidence']]
        .rename(columns={'player_name': 'Player', 'primary_role': 'Main phase', 'matches': 'Matches analyzed'}),
        hide_index=True, use_container_width=True
    )
    st.caption('Ordered using the same V4 conservative scores. "Needs closer review" means the conservative score is not positive; it does not label a player as bad.')
    with st.expander('Advanced: see exact model scores and uncertainty'):
        details = top[['player_name', 'score_per_100', 'bootstrap_low', 'bootstrap_high', 'positive_match_rate', 'deliveries']].copy()
        st.dataframe(details.rename(columns={
            'player_name': 'Player', 'score_per_100': 'Average adjusted impact',
            'bootstrap_low': 'Conservative impact', 'bootstrap_high': 'Upper bootstrap diagnostic',
            'positive_match_rate': 'Positive-match share', 'deliveries': 'Deliveries'
        }), hide_index=True, use_container_width=True)
        st.caption('These scores are relative to a modeled baseline. The bootstrap range is a stability diagnostic, not a formal confidence interval.')

def dossier(kind,fmt,df):
    st.subheader('Player dossier')
    if df.empty:st.info('No eligible players.');return
    name=st.selectbox('Choose a player',df['player_name'].tolist(),key=f'dossier_{kind}_{fmt}')
    p=df.loc[df.player_name.eq(name)].iloc[0]
    st.markdown(f'### {name}')
    st.caption(f"{kind[:-1].title()} · Main innings phase: {str(p['primary_role']).title()}")
    a,b,c,d=st.columns(4)
    a.metric('Matches analyzed',f"{int(p['matches']):,}")
    b.metric('Matches above expectation',f"{p['positive_match_rate']:.0%}")
    c.metric('Conservative impact',f"{p['bootstrap_low']:+.2f}")
    d.metric('Deliveries analyzed',f"{int(p['deliveries']):,}")
    st.markdown('#### Cricket performance by innings phase')
    stats=read(f'{kind}_phase_stats_{fmt}.csv')
    player_id='striker_id' if kind=='batters' else 'bowler_id'
    if not stats.empty and player_id in stats.columns and player_id in p.index:
        ps=stats.loc[stats[player_id].astype(str).eq(str(p[player_id]))].copy()
        phase_order=['Powerplay','Middle','Death']
        ps['stage']=pd.Categorical(ps['stage'],categories=phase_order,ordered=True)
        ps=ps.sort_values('stage')
        if not ps.empty:
            if kind=='batters':
                display=ps[['stage','matches','runs','balls','strike_rate']].rename(columns={
                    'stage':'Phase','matches':'Matches','runs':'Runs','balls':'Balls faced','strike_rate':'Strike rate'})
                display['Strike rate']=display['Strike rate'].round(1)
                st.dataframe(display,hide_index=True,use_container_width=True)
                st.caption('Strike rate = 100 × batter runs / balls faced. Wides are excluded from balls faced; no-balls count as balls faced.')
            else:
                display=ps[['stage','matches','runs_conceded','legal_balls','wickets','economy']].rename(columns={
                    'stage':'Phase','matches':'Matches','runs_conceded':'Runs conceded',
                    'legal_balls':'Legal balls','wickets':'Bowler wickets','economy':'Economy'})
                display['Economy']=display['Economy'].round(2)
                st.dataframe(display,hide_index=True,use_container_width=True)
                st.caption('Economy = 6 × bowler-conceded runs / legal deliveries. Wides and no-balls add runs but not legal balls; byes/leg-byes are excluded. Run-outs are not credited to bowlers.')
            st.caption(f'Raw match statistics for {fmt.upper() if fmt != "all" else "all supplied formats"}; separate from model-adjusted pressure impact. Small phase samples can be misleading.')
        else:st.info('No phase statistics for this player in this competition.')
    else:st.info('Phase statistics CSV not found. Copy the six *_phase_stats_*.csv files into the results folder.')
    st.info('**Scouting takeaway:** '+short_verdict(p))
    with st.expander('See match-by-match evidence'):
        idcol='striker_id' if kind=='batters' else 'bowler_id'
        ev=read(f'{kind}_v4_{fmt}_match_evidence.csv')
        if not ev.empty and idcol in ev.columns and idcol in p.index:
            pe=ev.loc[ev[idcol].astype(str).eq(str(p[idcol]))].copy()
            if not pe.empty:
                pe['impact']=pd.to_numeric(pe['total'],errors='coerce')/pd.to_numeric(pe['exposure'],errors='coerce').replace(0,float('nan'))*100
                pe=pe.sort_values('match_id')
                fig=go.Figure(go.Bar(x=pe['match_id'].astype(str),y=pe['impact'],marker_color=[GREEN if v>=0 else PINK for v in pe['impact'].fillna(0)]))
                fig.add_hline(y=0,line_color=GOLD)
                fig.update_layout(xaxis_title='Match identifier (not a date)',yaxis_title='Adjusted impact / 100')
                st.plotly_chart(plot_style(fig,330),use_container_width=True)
                st.caption('Small per-match samples may produce extreme scores; these are adjusted model outputs.')
            else:st.info('No match evidence available for this player.')
        else:st.info('Match evidence file not available.')
    with st.expander('See performance by innings phase'):
        ph=read(f'{kind}_v4_phase_diagnostics.csv')
        namecol='striker_name' if kind=='batters' else 'bowler_name'
        if not ph.empty and namecol in ph.columns:
            ph=ph[ph[namecol].eq(name)]
            if not ph.empty:
                fig=go.Figure(go.Bar(x=ph['stage'],y=ph['phase_impact_per_100'],marker_color=PINK))
                fig.add_hline(y=0,line_color=GOLD)
                fig.update_layout(xaxis_title='Innings phase',yaxis_title='Adjusted impact / 100')
                st.plotly_chart(plot_style(fig,320),use_container_width=True)
                st.caption('These phase diagnostics combine all supplied competitions, even if IPL is selected.')
            else:st.info('No phase evidence for this player.')
        else:st.info('Phase diagnostics unavailable.')

def duel(df):
    st.subheader('The Duel · Compare two players')
    if len(df)<2:st.info('At least two eligible players are needed.');return
    names=df.player_name.tolist()
    a,b=st.columns(2)
    x=a.selectbox('Player A',names,index=0)
    y=b.selectbox('Player B',names,index=1)
    if x==y:st.warning('Select two different players.');return
    sel=df[df.player_name.isin([x,y])].copy()
    view=sel[['player_name','primary_role','matches','positive_match_rate','bootstrap_low','score_per_100']].rename(columns={
        'player_name':'Player','primary_role':'Main phase','matches':'Matches','positive_match_rate':'Positive-match share',
        'bootstrap_low':'Conservative impact','score_per_100':'Mean impact'})
    st.dataframe(view,hide_index=True,use_container_width=True)
    st.caption('The comparison table shows the exact model scores. Prefer comparing players with similar roles and adequate match samples.')
    st.caption('Compare players in similar roles when possible. These historical results do not establish future outcomes.')

def board():
    st.subheader('RR scouting shortlist · IPL evidence')
    s=read('v4_final_role_review_shortlist.csv')
    if s.empty:
        st.warning('Shortlist file missing. Showing the IPL leaderboard instead.')
        for kind in ['batters','bowlers']:
            st.markdown(f'#### {kind.title()}')
            st.dataframe(ranked(kind,'ipl').head(10)[['player_name','matches','bootstrap_low']],hide_index=True)
    else:
        for kind in ['batters','bowlers']:
            st.markdown(f'#### {kind.title()} · Top 10')
            t=s[s.category.eq(kind)].sort_values('ipl_rank').copy()
            st.dataframe(t[['ipl_rank','player_name','primary_role','matches','positive_match_rate','bootstrap_low']].rename(columns={
                'ipl_rank':'Rank','player_name':'Player','primary_role':'Main phase','matches':'Matches',
                'positive_match_rate':'Positive-match share','bootstrap_low':'Conservative impact'}),hide_index=True,use_container_width=True)
        with st.expander('Review evidence warnings'):
            st.dataframe(s[['category','player_name','review_flag']],hide_index=True,use_container_width=True)
        st.download_button('Download shortlist CSV',s.to_csv(index=False),'RR_pressure_shortlist.csv','text/csv')
    st.warning('Pressure-reliability candidates only. IPL 2027 auction availability, retention and price are not verified.')

def main():
    st.sidebar.markdown('## 🏏 SCOUTING ROOM')
    st.sidebar.caption('SupeRR Selector · Season 2')
    fmt_label=st.sidebar.radio('Competition',['IPL','T20I','All supplied matches'])
    fmt={'IPL':'ipl','T20I':'t20i','All supplied matches':'all'}[fmt_label]
    kind_label=st.sidebar.radio('Player type',['Batters','Bowlers'])
    kind=kind_label.lower()
    st.sidebar.divider()
    st.sidebar.caption('V4 historical model · Rankings provisional')
    st.markdown(f'<div style="color:{GOLD};font-size:12px;letter-spacing:2.5px;font-weight:800">SUPERR SELECTOR  /  SEASON 02  /  PLAYER INTELLIGENCE</div>',unsafe_allow_html=True)
    st.title('THE PRESSURE ROOM 🏏')
    st.markdown('**Who delivers when the match gets difficult?** Explore the evidence behind each selection.')
    df=ranked(kind,fmt)
    if df.empty:
        st.error(f'Missing or empty results file: results/{kind}_v4_{fmt}.csv');return
    c1,c2,c3=st.columns(3)
    c1.metric('Players assessed',len(df))
    c2.metric('Competition',fmt_label)
    c3.metric('Analysis',kind_label)
    tabs=st.tabs(['🏆 Rankings','🪪 Player Profiles','⚔️ Compare Players','🎯 Final Shortlist','🔬 How We Ranked'])
    with tabs[0]:
        st.subheader(f'{fmt_label} {kind_label} · Most reliable candidates')
        st.caption('Ranked by conservative pressure-adjusted impact. Higher scores indicate stronger evidence relative to the model expectation.')
        c1,c2=st.columns([2,1])
        role=c1.selectbox('Main innings phase',['All phases']+sorted(df.primary_role.dropna().unique().tolist()))
        minimum=c2.slider('Minimum matches',12,100,12)
        view=df[df.matches.ge(minimum)]
        if role!='All phases':view=view[view.primary_role.eq(role)]
        leaderboard(view)
        with st.expander('Full filtered ranking (including model scores)'):
            t=view.head(20).copy()
            t.insert(0,'Rank',range(1,len(t)+1))
            st.dataframe(t[['Rank','player_name','primary_role','matches','positive_match_rate','bootstrap_low']].rename(columns={
                'player_name':'Player','primary_role':'Main phase','matches':'Matches',
                'positive_match_rate':'Positive-match share','bootstrap_low':'Conservative impact'}),hide_index=True,use_container_width=True)
    with tabs[1]:dossier(kind,fmt,df)
    with tabs[2]:duel(df)
    with tabs[3]:board()
    with tabs[4]:
        st.subheader('How we identified reliable players')
        st.markdown('**1.** Reconstructed match context from ball-by-ball data.  **2.** Compared performance with situation-adjusted expectations.  **3.** Checked consistency across matches.  **4.** Used match resampling to reduce reliance on a few standout games.')
        st.markdown('**Data coverage:** 833 eligible matches, 196,528 deliveries (362 IPL, 441 T20I, 30 other T20 matches). Revised matches and special innings were excluded.')
        with st.expander('Technical definitions and limitations'):
            st.write('**Conservative impact:** 10th percentile of match-resampled adjusted impact per 100 weighted deliveries. It is not a calibrated confidence interval or win probability.')
            st.write('**Positive-match share:** Share of evaluable matches with positive model-adjusted impact. **Main phase:** Most frequently observed innings phase, not a complete tactical role classification.')
            st.write('Pressure weights and wicket valuation are heuristic. These observational scores do not prove clutch ability. Format and role differences may remain. Auction eligibility is not assessed.')
    st.divider()
    st.caption('Independent Rajasthan Royals-inspired scouting concept · Not an official Rajasthan Royals product')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        st.error('The dashboard encountered an error. See details below.')
        st.exception(exc)
