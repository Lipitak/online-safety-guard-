"""
train_model.py
--------------
Steps 2-6: Load dataset -> preprocess -> train model -> save pipeline

We save a single sklearn Pipeline (TF-IDF + Naive Bayes) so that app.py can
run SHAP's text explainer directly on raw text (no separate vectorizer step
needed at request time).

Run this once:
    python train_model.py

It creates: pipeline.pkl
"""

import re
import string
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# -----------------------------
# Step 2: Load dataset
# -----------------------------
# Dataset: "SMS Spam Collection Dataset" (Kaggle / UCI)
# Download from Kaggle: search "sms spam collection dataset", download spam.csv
# Place spam.csv in this same folder. Expected raw columns: v1 (label), v2 (message)

DATA_PATH = "spam.csv"

print("Loading dataset...")
df = pd.read_csv(DATA_PATH, encoding="latin-1")
df = df[["v1", "v2"]]
df.columns = ["label", "message"]
print(f"Loaded {len(df)} messages")
print(df["label"].value_counts())

# -----------------------------
# Step 3: Preprocessing
# -----------------------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", " link ", text)
    text = re.sub(r"\d{6,}", " longnum ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["clean_message"] = df["message"].apply(clean_text)
df["target"] = df["label"].apply(lambda x: 1 if str(x).strip().lower() == "spam" else 0)

X_train, X_test, y_train, y_test = train_test_split(
    df["clean_message"], df["target"], test_size=0.2, random_state=42, stratify=df["target"]
)

# -----------------------------
# Step 4: Model training (single Pipeline: TF-IDF + Naive Bayes)
# -----------------------------
print("Training pipeline (TF-IDF + Naive Bayes)...")
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2))),
    ("nb", MultinomialNB()),
])
pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nTest Accuracy: {acc:.4f}\n")
print(classification_report(y_test, y_pred, target_names=["Safe", "Scam"]))

# -----------------------------
# Step 6: Save pipeline
# -----------------------------
joblib.dump(pipeline, "pipeline.pkl")
print("\nSaved pipeline.pkl")
print("Next: run `python app.py` to start the API + web UI")
