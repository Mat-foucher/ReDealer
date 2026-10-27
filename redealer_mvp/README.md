# ReDealer

**Your deals. Your re-deals.** A deal starts a subscription; a re-deal improves its value later. The current MVP implements new-subscription deals and previews the re-deal concept. It does not yet switch existing subscriptions or activate retention offers.

## Savings dashboard

The Savings tab separates first-charge savings on completed mock transactions from projected 12-month savings. It compares the same service at regular pricing with introductory pricing for the actual promotional duration, followed by normal renewal pricing. Example: SoundNest is $5.99 for 3 months, then $12.99 for 9 months: $134.88 total vs $155.88 regular pricing, or $21 projected savings, not $84.

Projections start at activation, assume the subscription stays active for 12 months with unchanged pricing and zero demo taxes/fees, and exclude canceled plans. They are not additional savings on top of first-charge savings; the first payment is already included. Historical first-charge comparisons remain after cancellation. No actual money has been saved. Preview examples are never counted in totals.

A dark-mode Streamlit MVP for price-triggered subscriptions with a **mock PayPal wallet** and fictional merchants. No API keys required. No real money, customer credentials, PayPal API calls, or service activation.

## Run (Python 3.10+)

Unzip this project, open a terminal in the `dealpilot` directory, then:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Windows activation: `.venv\Scripts\activate`. Open the local URL printed by Streamlit.

## Two-minute demo

1. Connect **mock PayPal** in the sidebar. The wallet starts with $100 of fictional money.
2. Create a SoundNest watch: maximum $8/month introductory price; maximum $15/month regular price; seven-day purchase window; new customer; **Ask first**.
3. Advance one demo day. A $5.99/month offer appears, for three months, then $12.99/month.
4. Read the terms, check the acceptance box, and approve the mock purchase.
5. See the wallet fall to $94.01, a mock transaction receipt, and a linked fictional subscription.
6. For auto-buy, create a TrailPlus watch with limits of $8/$15 and select **Auto-buy demo**. Explicitly check the authorization box. Advance to day 3; the mock transaction occurs once.
7. Test guardrails with a too-low renewal cap or by unchecking new-customer eligibility.

## Included features

- Target-price watches with separate introductory and regular monthly price caps.
- Manual approval by default; explicitly authorized simulated auto-buy.
- Expiring purchase windows and expiring offers.
- New-customer, balance, connection, duplicate-watch, and duplicate-subscription checks.
- Deterministic mock deal feed: SoundNest days 1–3; FocusFlow days 2–3; TrailPlus days 3–5.
- Cancel watches; cancel mock subscriptions; inspect transaction and event history; export audit JSON.
- Dark, high-contrast dashboard with labeled statuses rather than color alone.

## Honest boundaries

This is NOT PayPal Sandbox. The connect button changes in-memory demo state only. Fictional brands avoid implying real partnerships or working codes. The simulation charges only the first payment; displayed renewal dates are illustrative, using 30-day months. Taxes and fees are zero. No actual recurring billing, refunds, or cancellation requests occur.

State lives in one Streamlit browser session. Reloads/new sessions or a server restart may lose it; exported JSON is an audit download, not a restore file. There is no background job: deal checks happen only through app interactions. No real coupon discovery or deal forecasting is implemented. The separate Beautiful Soup deal extractor is not integrated; real scraped codes must never inherit this demo feed's verification label.

## Tests

```bash
python -m unittest -v test_engine.py
python -m unittest -v test_app.py
```

## Going beyond a hackathon

1. Persist per-user rules and consent in a database; use authentication and secure sessions.
2. Ingest licensed/merchant-approved offers with provenance, validity windows, and eligibility. Treat external codes as unverified until legitimately validated.
3. Replace the wallet adapter with approved PayPal Sandbox APIs. Keep credentials server-side, reconcile webhooks, and use transaction idempotency and recovery handling. A payment success alone does not prove service activation.
4. Integrate a consenting provider's provisioning/account-linking API. Do not collect third-party account passwords. Universal activation is not supported merely by adding PayPal.
5. Add durable scheduling, final-price checks including taxes, explicit billing/renewal consent, inventory/offer revalidation, and failure compensation/refunds before any real automatic purchase.
6. Review merchant terms, payments requirements, consumer disclosures, privacy, and subscription cancellation obligations before handling real customers.

The current engine is deliberately a pure no-network simulation so that none of these production capabilities are implied.
