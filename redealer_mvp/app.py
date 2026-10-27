import json
from decimal import Decimal

import streamlit as st
from engine import CATALOG, add_rule, advance, cancel_rule, evaluate, initial_state, money, offers, purchase, snapshot, today, savings_projection, savings_summary

st.set_page_config(page_title='ReDealer • Your deals. Your re-deals.', page_icon='◈', layout='wide')
st.markdown('''<style>
.stApp {background:#0b1120;color:#edf2fa}
[data-testid="stSidebar"] {background:#111b2c}
.block-container {max-width:1250px;padding-top:2.5rem}
h1,h2,h3 {letter-spacing:-.035em}
.eyebrow {color:#6ee7cf;font-size:.8rem;letter-spacing:.16em;font-weight:700}
.hero {font-size:1.1rem;color:#aab8cf;max-width:760px}
[data-testid="stMetric"] {background:#142035;border:1px solid #263651;border-radius:16px;padding:18px}
.stButton>button[kind="primary"] {background:#6ee7cf;color:#081820;border:0}
</style>''', unsafe_allow_html=True)

if 'demo' not in st.session_state:
    st.session_state.demo = initial_state()
state = st.session_state.demo


def cents(value):
    return int(Decimal(str(value)) * 100)


with st.sidebar:
    st.markdown('## ◈ ReDealer')
    st.caption('Your deals. Your re-deals.')
    st.warning('SIMULATION · Mock PayPal wallet. No real charges or service activation.')
    st.markdown('### Demo wallet')
    st.write('mat.demo@example.test')
    st.metric('Available demo balance', money(state['balance']))
    if not state['connected']:
        if st.button('Connect mock PayPal', type='primary', width='stretch'):
            state['connected'] = True
            evaluate(state)
            st.rerun()
    else:
        st.success('Mock PayPal connected')
        if st.button('Disconnect mock wallet', width='stretch'):
            state['connected'] = False
            evaluate(state)
            st.rerun()
    st.divider()
    st.markdown('### Simulation clock')
    st.write(f'Day {state["day"]} · {today(state):%b %d, %Y}')
    if st.button('Advance one demo day →', width='stretch'):
        advance(state)
        st.rerun()
    st.caption('Deals appear on days 1, 2, and 3. Advancing checks every active watch. No background scheduler runs.')
    with st.expander('Reset demo'):
        if st.button('Erase session and start again'):
            st.session_state.demo = initial_state()
            st.rerun()

st.markdown('<div class="eyebrow">YOUR PRICE. YOUR PERMISSION.</div>', unsafe_allow_html=True)
st.title('You have deals. We find your re-deals.')
st.markdown('<p class="hero">A deal gets you started. A re-deal keeps you looking for better value. Set your limits and see what smarter timing could save.</p>', unsafe_allow_html=True)
st.caption('Fictional merchants • USD • Session-only storage • PayPal integration is mocked, not Sandbox-connected')

summary = savings_summary(state)
a,b,c,d = st.columns(4)
a.metric('Active watches', sum(r['status'] in ('Watching','Approval needed') for r in state['rules']))
b.metric('Subscriptions activated', len(state['subscriptions']))
c.metric('Saved on first charges · mock', money(summary['first_charge']))
d.metric('Projected 12-month savings', money(summary['projected_savings']))
st.caption('First-charge savings reflect completed mock payments. Projections compare active plans with regular pricing over 12 months from activation, assuming no cancellation or price changes. No real money has been saved.')

watch_tab, deals_tab, savings_tab, subscriptions_tab, activity_tab = st.tabs(['◎ Watchlist', '✦ Deals', '↘ Savings', '▣ My deals & re-deals', '↗ Activity'])

with watch_tab:
    st.subheader('Make your next subscription intentional')
    with st.expander('＋ Create a price watch', expanded=not state['rules']):
        with st.form('new_watch'):
            product = st.selectbox('Service', list(CATALOG), format_func=lambda p: CATALOG[p]['name'])
            col1,col2,col3 = st.columns(3)
            max_price = col1.number_input('Maximum intro price / month ($)', min_value=0.01, max_value=1000.0, value=8.0, step=0.5)
            max_renewal = col2.number_input('Maximum regular renewal / month ($)', min_value=0.01, max_value=1000.0, value=15.0, step=0.5)
            wait = col3.number_input('Purchase window (demo days)', min_value=1, max_value=90, value=7)
            new = st.checkbox('I am a new customer of this service', value=True)
            mode = st.radio('When an eligible deal appears', ['Ask first','Auto-buy demo'], horizontal=True)
            st.caption('All demo plans bill monthly. Intro discounts last 1–3 months. Taxes and fees are $0 in this simulation. No actual recurring billing occurs.')
            consent = st.checkbox('I authorize ONE simulated purchase within these price limits and this window, including the disclosed monthly renewal terms. (Required for auto-buy.)')
            if st.form_submit_button('Create watch', type='primary'):
                try:
                    add_rule(state, product, cents(max_price), cents(max_renewal), int(wait), mode, new, consent)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    if not state['rules']:
        st.info('Try SoundNest with an $8 intro limit and $15 renewal limit. Connect the mock wallet, then advance to day 1.')
    for rule in reversed(state['rules']):
        with st.container(border=True):
            left,right = st.columns([3,1])
            left.markdown('### ' + CATALOG[rule['product']]['name'])
            right.markdown('**' + rule['status'] + '**')
            st.write(f'Intro ≤ {money(rule["max_price"])}/mo · Renewal ≤ {money(rule["max_renewal"])}/mo · {rule["mode"]}')
            st.caption(f'Authorized through demo day {rule["deadline"]} (inclusive). {rule["reason"]}')
            if rule['status'] == 'Approval needed':
                offer = next(o for o in offers(state) if o['id'] == rule['offer_id'])
                st.info(f'{money(offer["price"])}/month for {offer["intro_months"]} months, then {money(offer["renewal"])}/month until canceled. New customers only. Code: {offer["code"]}.')
                accepted = st.checkbox('I accept these specific demo price and renewal terms.', key='terms-'+rule['id'])
                if st.button('Approve mock purchase', key='buy-'+rule['id'], disabled=not accepted, type='primary'):
                    try:
                        purchase(state, rule['id'], approved=True)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            if rule['status'] in ('Watching','Approval needed'):
                if st.button('Cancel watch', key='cancel-'+rule['id']):
                    cancel_rule(state, rule['id'])
                    st.rerun()

with deals_tab:
    st.subheader('The offer, not just the headline')
    st.caption('Deterministic mock feed—not scraped deals, a forecast, or evidence of real merchant partnerships.')
    current = offers(state)
    if not current:
        st.info('No active offers today. Advance the demo clock to see promotions appear.')
    for offer in current:
        with st.container(border=True):
            item = CATALOG[offer['product']]
            st.markdown('### ' + item['name'])
            st.write(f'**{money(offer["price"])}/month** for {offer["intro_months"]} months · normally {money(item["regular"])}/month')
            st.write(f'Then {money(offer["renewal"])}/month until canceled. New customers only. No stacking. USD; no demo taxes or fees.')
            p = savings_projection(item['regular'], offer['price'], offer['intro_months'], offer['renewal'])
            st.success(f'Potential savings: {money(item["regular"]-offer["price"])} on the first bill · {money(p["savings"])} over 12 months if eligible and retained.')
            st.caption(f'Code {offer["code"]} · Expires after demo day {offer["expires_day"]} · {offer["source"]}')

with savings_tab:
    st.subheader('See the difference. Not just the discount.')
    st.caption('Counterfactual comparison with the same service at its fictional regular monthly price. Projections start at activation, not today. This is not a guarantee, remaining-savings forecast, or verified market-lowest price.')
    x,y,z = st.columns(3)
    x.metric('12-month regular-price baseline', money(summary['baseline']))
    y.metric('12-month cost with your deals', money(summary['cost']))
    z.metric('Projected difference', money(summary['projected_savings']))
    if summary['rows']:
        st.dataframe([{'Service':r['service'], 'Regular price · 12 mo':money(r['baseline']), 'With deal · 12 mo':money(r['cost']), 'Projected savings':money(r['savings'])} for r in summary['rows']], hide_index=True, width='stretch')
        st.markdown('#### Monthly cost comparison · active subscriptions')
        st.bar_chart({'Regular pricing ($)': [sum(r['monthly'][i]['regular'] for r in summary['rows'])/100 for i in range(12)], 'With ReDealer ($)': [sum(r['monthly'][i]['redealer'] for r in summary['rows'])/100 for i in range(12)]}, stack=False)
        st.caption('Chart rows 0–11 correspond to billing months 1–12 after each subscription’s activation. Different activation dates are aligned by subscription age, not calendar month.')
    else:
        st.info('Activate a demo subscription to populate your savings ledger. Explore the example below before buying.')
    with st.expander('Explore an example before purchasing', expanded=not summary['rows']):
        example = st.selectbox('Preview a fictional deal', list(CATALOG), format_func=lambda p: CATALOG[p]['name'])
        item = CATALOG[example]
        p = savings_projection(item['regular'],item['intro'],item['intro_months'],item['regular'])
        st.write(f'{money(item["intro"])}/month for {item["intro_months"]} months, then {money(item["regular"])}/month.')
        st.write(f'12 × {money(item["regular"])} = **{money(p["baseline"])}** at regular pricing. With the deal: **{money(p["cost"])}**. Projected savings: **{money(p["savings"])}**.')
        st.caption('Example only—not counted in your ledger. Availability and eligibility still apply. Intro discounts are NOT multiplied by 12 unless they actually last 12 months.')
    st.caption('Assumptions: same monthly service, no fees/taxes in demo, no additional promotions, no cancellation, and unchanged renewal pricing. Canceled plans are excluded from projections; their historical first-charge savings remain.')

with subscriptions_tab:
    st.subheader('Your activated services')
    st.caption('Account linking and activation are simulated. Billing dates use 30-day months for demo purposes; no future charges run.')
    if not state['subscriptions']:
        st.info('Your first mock subscription will appear here after a qualifying purchase.')
    for product, sub in state['subscriptions'].items():
        with st.container(border=True):
            st.markdown('### '+sub['name'])
            st.write(f'**{sub["status"]}** · Linked to {sub["account"]}')
            st.write(f'{money(sub["price"])}/mo for {sub["intro_months"]} months → {money(sub["renewal"])}/mo afterward')
            st.caption(f'Activated {sub["activated"]} · Next illustrative bill {sub["next_bill_date"]} · Regular pricing begins {sub["first_regular_date"]}')
            st.markdown('**Re-deal watch · concept preview**')
            st.caption('Look for eligible existing-customer offers before renewal. No eligible re-deal is available in this demo feed; its current promotions are new-customer-only. No automatic switching or renewal discounts are implemented.')
            if sub['status'] == 'Active (mock)' and st.button('Cancel mock subscription', key='sub-'+product):
                sub['status'] = 'Canceled (mock)'
                st.rerun()
    st.caption('Canceled services remain in account history, preventing reuse of a new-customer promotion. No refunds are simulated.')

with activity_tab:
    st.subheader('A receipt for every decision')
    if state['transactions']:
        st.dataframe([dict(t, amount=money(t['amount'])) for t in state['transactions']], width='stretch', hide_index=True)
    else:
        st.info('No mock payments yet.')
    for e in state['events'][:30]:
        st.caption(e['date'] + ' · ' + e['message'])
    st.download_button('Download demo audit JSON', json.dumps({'state':snapshot(state),'savings':summary}, indent=2), 'redealer-audit.json', 'application/json')

st.divider()
st.caption('Demo guardrails: new-customer eligibility · intro + renewal caps · expiring authorization · wallet checks · duplicate prevention · manual approval by default. Production requires real consent, secure persistence, payment reconciliation, and merchant provisioning integrations.')
