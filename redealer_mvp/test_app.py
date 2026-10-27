"""UI interaction smoke tests using Streamlit's built-in AppTest."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def button(self, app, label):
        return next(b for b in app.button if b.label == label)

    def start(self):
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=20)
        self.assertFalse(app.exception)
        self.button(app,'Connect mock PayPal').click().run()
        self.assertTrue(app.session_state['demo']['connected'])
        return app

    def test_manual_flow(self):
        app = self.start()
        self.button(app,'Create watch').click().run()
        self.assertFalse(app.exception)
        self.button(app,'Advance one demo day →').click().run()
        self.assertEqual(app.session_state['demo']['rules'][0]['status'],'Approval needed')
        self.assertTrue(self.button(app,'Approve mock purchase').disabled)
        next(c for c in app.checkbox if c.label.startswith('I accept these specific')).check().run()
        self.button(app,'Approve mock purchase').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['demo']['balance'],9401)
        self.assertEqual(len(app.session_state['demo']['transactions']),1)
        self.button(app,'Cancel mock subscription').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['demo']['subscriptions']['soundnest']['status'],'Canceled (mock)')

    def test_auto_flow(self):
        app = self.start()
        app.radio[0].set_value('Auto-buy demo')
        next(c for c in app.checkbox if c.label.startswith('I authorize ONE')).check()
        self.button(app,'Create watch').click().run()
        self.button(app,'Advance one demo day →').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['demo']['transactions']),1)
        self.button(app,'Advance one demo day →').click().run()
        self.assertEqual(len(app.session_state['demo']['transactions']),1)


if __name__ == '__main__': unittest.main()
