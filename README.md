# Online Safety Guard — AI-Powered Scam & Phishing Message Detector

A lightweight tool that checks a message (SMS/email/social) and flags it as
**Scam** or **Safe**, with a human-readable reason (SHAP-based explainability
+ quick rule-based flags like "contains a link", "uses urgent language").

## Project structure

```
online-safety-guard/
├── spam.csv              <- dataset (a small placeholder is included, see below)
├── train_model.py        <- Step 2-6: load data, clean, train, save model
├── app.py                <- Step 7: Flask backend + SHAP explainability
├── templates/
│   └── index.html        <- Step 8: frontend UI
├── requirements.txt
└── pipeline.pkl           <- generated after training (already included as a demo)
```

## ⚠️ Important: replace the demo dataset before your real demo

`spam.csv` currently included is a **small synthetic placeholder** (300
spam-like + 300 normal messages) just so everything runs immediately.
For a real hackathon demo, replace it with the actual **SMS Spam Collection
Dataset**:

1. Go to Kaggle and search "SMS Spam Collection Dataset" (or UCI ML repo).
2. Download the CSV — it should have columns `v1` (label: spam/ham) and
   `v2` (message text).
3. Replace `spam.csv` in this folder with that file.
4. Re-run `python train_model.py` to retrain on real data.

## How to run (in Antigravity, or any local machine)

### 1. Open this folder as your project

Import/open the `online-safety-guard` folder in Antigravity (or any code
editor/terminal).

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If you're on Mac/Linux and get a "externally managed environment" error:

```bash
pip install -r requirements.txt --break-system-packages
```

### 3. Train the model (only needed once, or after changing spam.csv)

```bash
python train_model.py
```

This prints accuracy and saves `pipeline.pkl`.

### 4. Run the app

```bash
python app.py
```

You'll see something like `Running on http://127.0.0.1:5000`. Open that
link in your browser.

### 5. Test it

Paste a message like:

```
Dear customer, your account will be blocked in 24 hrs. Click here to verify: bit.ly/xyz123
```

→ Should show **⚠️ Suspicious — likely a Scam** with reasons like
"contains a link", "uses urgent/pressure language", and top SHAP words.

Paste a normal message like:

```
Hey, are we still meeting for lunch tomorrow?
```

→ Should show **✅ Looks Safe**.

## Notes for your demo/pitch

- The model is a lightweight **TF-IDF + Naive Bayes** classifier — fast to
  train, easy to explain, good accuracy on this kind of text classification.
- Explainability comes from **SHAP**, which highlights which words pushed
  the message toward "Scam" — this is the same explainability approach used
  in the team's earlier Trinetra AI project, adapted here into a smaller,
  focused module.
- If SHAP feels slow during a live demo (it recomputes per request), you
  can rely on the quick rule-based flags (link detection, urgency words)
  as a fast fallback — the code already does this automatically alongside
  SHAP.

## Known limitations (good to mention honestly if judges ask)

- Trained on English SMS-style text; may not generalize well to other
  languages without retraining.
- Small dataset = decent demo accuracy, but a production version would
  need a much larger, more diverse dataset (emails, WhatsApp forwards,
  multiple languages).
- SHAP's KernelExplainer-style computation is not instant — fine for a
  single message in a demo, but would need optimization (e.g. a
  faster/cached explainer) for real-time, high-volume use.
# online-safety-guard-
