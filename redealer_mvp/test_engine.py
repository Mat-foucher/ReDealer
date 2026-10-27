import unittest
from engine import add_rule, advance, cancel_rule, evaluate, initial_state, purchase, savings_projection, savings_summary


class EngineTests(unittest.TestCase):
    def setup_rule(self, **overrides):
        s = initial_state()
        s['connected'] = True
        args = dict(product='soundnest', max_price=800, max_renewal=1500,
                    wait_days=7, mode='Ask first', new_customer=True, consent=False)
        args.update(overrides)
        r = add_rule(s, **args)
        return s, r

    def test_manual(self):
        s,r = self.setup_rule()
        advance(s)
        self.assertEqual(r['status'], 'Approval needed')
        with self.assertRaises(ValueError): purchase(s,r['id'])
        purchase(s,r['id'],approved=True)
        self.assertEqual(s['balance'], 9401)
        self.assertEqual(len(s['subscriptions']), 1)
        with self.assertRaises(ValueError): purchase(s,r['id'],approved=True)
        self.assertEqual(len(s['transactions']), 1)

    def test_auto_requires_consent(self):
        with self.assertRaises(ValueError): self.setup_rule(mode='Auto-buy demo')

    def test_auto_idempotent(self):
        s,r = self.setup_rule(mode='Auto-buy demo',consent=True)
        advance(s)
        for _ in range(5): evaluate(s)
        self.assertEqual(len(s['transactions']),1)

    def test_caps_and_eligibility(self):
        for override in ({'max_price':500},{'max_renewal':1000},{'new_customer':False}):
            with self.subTest(override=override):
                s,r = self.setup_rule(**override)
                advance(s)
                self.assertEqual(r['status'],'Watching')
                self.assertFalse(s['transactions'])

    def test_wallet(self):
        for key,value in [('balance',1),('connected',False)]:
            s,r = self.setup_rule(mode='Auto-buy demo',consent=True)
            s[key] = value
            advance(s)
            self.assertFalse(s['transactions'])

    def test_expiry(self):
        s,r = self.setup_rule(wait_days=1)
        advance(s)
        advance(s)
        self.assertEqual(r['status'],'Expired')
        with self.assertRaises(ValueError): purchase(s,r['id'],approved=True)

    def test_cancellation(self):
        s,r = self.setup_rule(mode='Auto-buy demo',consent=True)
        cancel_rule(s,r['id'])
        advance(s)
        self.assertEqual(r['status'],'Canceled')
        self.assertFalse(s['transactions'])

    def test_duplicate_watch(self):
        s,r = self.setup_rule()
        with self.assertRaises(ValueError):
            add_rule(s,'soundnest',800,1500,7,'Ask first',True,False)

    def test_offer_disappears(self):
        s,r = self.setup_rule()
        for _ in range(4): advance(s)
        self.assertEqual(r['status'],'Watching')
        self.assertEqual(r['reason'],'No active offer.')

    def test_savings_intro_not_annualized(self):
        p = savings_projection(1299,599,3,1299)
        self.assertEqual(p['baseline'],15588)
        self.assertEqual(p['cost'],13488)
        self.assertEqual(p['savings'],2100)
        self.assertEqual(p['monthly'][3]['savings'],0)

    def test_savings_cancellation(self):
        s,r = self.setup_rule(mode='Auto-buy demo',consent=True)
        advance(s)
        self.assertEqual(savings_summary(s)['first_charge'],700)
        self.assertEqual(savings_summary(s)['projected_savings'],2100)
        s['subscriptions']['soundnest']['status']='Canceled (mock)'
        self.assertEqual(savings_summary(s)['first_charge'],700)
        self.assertEqual(savings_summary(s)['projected_savings'],0)

    def test_empty_savings(self):
        self.assertEqual(savings_summary(initial_state())['projected_savings'],0)

    def test_short_horizon(self):
        self.assertEqual(savings_projection(1299,599,3,1299,2)['savings'],1400)

    def test_negative_savings_preserved(self):
        self.assertLess(savings_projection(1000,500,1,1200)['savings'],0)


if __name__ == '__main__': unittest.main()
