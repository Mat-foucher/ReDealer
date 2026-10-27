"""Deterministic, no-network simulation. All prices are integer USD cents."""
from copy import deepcopy
from datetime import date, timedelta

CATALOG = {
    'soundnest': {'name': 'SoundNest Music', 'category': 'Music', 'regular': 1299, 'intro_months': 3, 'intro': 599, 'code': 'LISTEN3', 'launch': 1, 'duration': 3},
    'focusflow': {'name': 'FocusFlow Pro', 'category': 'Productivity', 'regular': 1999, 'intro_months': 1, 'intro': 999, 'code': 'FOCUS50', 'launch': 2, 'duration': 2},
    'trailplus': {'name': 'TrailPlus', 'category': 'Outdoors', 'regular': 1499, 'intro_months': 2, 'intro': 749, 'code': 'GETOUT', 'launch': 3, 'duration': 3},
}


def initial_state():
    return {'day': 0, 'start': date.today().isoformat(), 'connected': False,
            'balance': 10000, 'rules': [], 'subscriptions': {}, 'transactions': [], 'events': []}


def today(state):
    return date.fromisoformat(state['start']) + timedelta(days=state['day'])


def money(cents):
    return f'${cents / 100:,.2f}'


def event(state, message):
    state['events'].insert(0, {'date': today(state).isoformat(), 'message': message})


def offers(state):
    result = []
    for product, item in CATALOG.items():
        if item['launch'] <= state['day'] < item['launch'] + item['duration']:
            result.append({'id': product + '-intro-v1', 'product': product, 'price': item['intro'],
                           'intro_months': item['intro_months'], 'renewal': item['regular'],
                           'code': item['code'], 'new_only': True,
                           'expires_day': item['launch'] + item['duration'] - 1,
                           'source': 'Simulated merchant feed', 'currency': 'USD',
                           'verified': 'Verified only inside this simulation'})
    return result


def add_rule(state, product, max_price, max_renewal, wait_days, mode, new_customer, consent):
    if product not in CATALOG:
        raise ValueError('Unknown demo service.')
    if any(r['product'] == product and r['status'] in ('Watching', 'Approval needed') for r in state['rules']):
        raise ValueError('You already have an active watch for this service.')
    if product in state['subscriptions']:
        raise ValueError('This demo account already has that subscription.')
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (max_price, max_renewal, wait_days)):
        raise ValueError('Prices must be integer cents and wait days an integer.')
    if max_price <= 0 or max_renewal <= 0 or not 1 <= wait_days <= 90:
        raise ValueError('Use positive limits and a 1–90 day window.')
    if mode not in ('Ask first', 'Auto-buy demo'):
        raise ValueError('Unknown mode.')
    if mode == 'Auto-buy demo' and not consent:
        raise ValueError('Explicit demo purchase authorization is required.')
    rule = {'id': 'watch-' + str(len(state['rules']) + 1), 'product': product,
            'max_price': max_price, 'max_renewal': max_renewal, 'mode': mode,
            'new_customer': bool(new_customer), 'consent': bool(consent),
            'deadline': state['day'] + wait_days, 'status': 'Watching', 'reason': 'Waiting for a qualifying offer.',
            'offer_id': None}
    state['rules'].append(rule)
    event(state, 'Created watch for ' + CATALOG[product]['name'])
    evaluate(state)
    return rule


def eligibility(state, rule, offer):
    if state['day'] > rule['deadline']:
        return 'Purchase window expired.'
    if rule['product'] in state['subscriptions']:
        return 'Duplicate subscription blocked.'
    if not offer:
        return 'No active offer.'
    if offer['new_only'] and not rule['new_customer']:
        return 'Offer is for new customers only.'
    if offer['price'] > rule['max_price']:
        return 'Introductory price is above your limit.'
    if offer['renewal'] > rule['max_renewal']:
        return 'Post-promotion monthly price is above your limit.'
    if not state['connected']:
        return 'Connect the demo wallet to continue.'
    if state['balance'] < offer['price']:
        return 'Insufficient demo funds.'
    return None


def purchase(state, rule_id, approved=False):
    rule = next((r for r in state['rules'] if r['id'] == rule_id), None)
    if not rule or rule['status'] not in ('Watching', 'Approval needed'):
        raise ValueError('Watch is not purchasable; completed purchases cannot be repeated.')
    offer = next((o for o in offers(state) if o['product'] == rule['product']), None)
    problem = eligibility(state, rule, offer)
    if problem:
        raise ValueError(problem)
    if rule['mode'] == 'Ask first' and not approved:
        raise ValueError('User confirmation required.')
    if rule['mode'] == 'Auto-buy demo' and not rule['consent']:
        raise ValueError('Auto-buy authorization missing.')
    # No external side effects: the payment and provisioning are mock state updates.
    charge_date = today(state)
    state['balance'] -= offer['price']
    state['transactions'].insert(0, {'id': f'MOCK-{len(state["transactions"])+1:04d}',
        'date': charge_date.isoformat(), 'service': CATALOG[rule['product']]['name'],
        'amount': offer['price'], 'status': 'Simulated completed', 'offer': offer['id']})
    state['subscriptions'][rule['product']] = {'name': CATALOG[rule['product']]['name'],
        'activated': charge_date.isoformat(), 'price': offer['price'], 'renewal': offer['renewal'],
        'intro_months': offer['intro_months'], 'first_regular_date': (charge_date + timedelta(days=30*offer['intro_months'])).isoformat(),
        'next_bill_date': (charge_date + timedelta(days=30)).isoformat(),
        'status': 'Active (mock)', 'account': 'mat.demo@example.test'}
    rule['status'] = 'Purchased'
    rule['reason'] = 'Mock payment completed and mock service account linked.'
    rule['offer_id'] = offer['id']
    event(state, f'Activated {CATALOG[rule["product"]]["name"]} for {money(offer["price"])} — simulated only.')


def evaluate(state):
    for rule in state['rules']:
        if rule['status'] not in ('Watching', 'Approval needed'):
            continue
        if state['day'] > rule['deadline']:
            rule.update(status='Expired', reason='Purchase window expired.', offer_id=None)
            continue
        offer = next((o for o in offers(state) if o['product'] == rule['product']), None)
        problem = eligibility(state, rule, offer)
        if problem:
            rule.update(status='Watching', reason=problem, offer_id=None)
        elif rule['mode'] == 'Auto-buy demo' and rule['consent']:
            purchase(state, rule['id'])
        else:
            rule.update(status='Approval needed', reason='Eligible deal found. Review the terms and approve.', offer_id=offer['id'])


def advance(state):
    state['day'] += 1
    event(state, 'Advanced simulation by one day. No recurring charges are simulated.')
    evaluate(state)


def cancel_rule(state, rule_id):
    rule = next(r for r in state['rules'] if r['id'] == rule_id)
    if rule['status'] not in ('Watching', 'Approval needed'):
        raise ValueError('Only active watches can be canceled.')
    rule.update(status='Canceled', reason='Canceled by you; no further purchase authorization.', offer_id=None)
    event(state, 'Canceled watch for ' + CATALOG[rule['product']]['name'])


def snapshot(state):
    return deepcopy(state)


def savings_projection(regular, intro, intro_months, renewal, months=12):
    """Like-for-like monthly plan comparison; no extrapolation of intro discount."""
    if not all(isinstance(v, int) and v >= 0 for v in (regular, intro, intro_months, renewal, months)) or months < 1:
        raise ValueError('Use nonnegative integer cents and a positive month count.')
    monthly = []
    for month in range(1, months + 1):
        cost = intro if month <= intro_months else renewal
        monthly.append({'month': month, 'regular': regular, 'redealer': cost, 'savings': regular-cost})
    baseline = sum(m['regular'] for m in monthly)
    cost = sum(m['redealer'] for m in monthly)
    return {'baseline': baseline, 'cost': cost, 'savings': baseline-cost, 'monthly': monthly}


def savings_summary(state, months=12):
    # Each purchased subscription's first payment occurred once. Cancellations do
    # not undo that historical first-charge comparison; future projections exclude them.
    first_charge = 0
    for rule in state['rules']:
        if rule['status'] == 'Purchased':
            tx = next(t for t in state['transactions'] if t['offer'] == rule['offer_id'])
            first_charge += CATALOG[rule['product']]['regular'] - tx['amount']
    rows = []
    for product, sub in state['subscriptions'].items():
        if sub['status'] != 'Active (mock)':
            continue
        p = savings_projection(CATALOG[product]['regular'], sub['price'], sub['intro_months'], sub['renewal'], months)
        rows.append({'service': sub['name'], **p})
    return {'first_charge': first_charge, 'rows': rows,
            'projected_savings': sum(r['savings'] for r in rows),
            'baseline': sum(r['baseline'] for r in rows), 'cost': sum(r['cost'] for r in rows)}
