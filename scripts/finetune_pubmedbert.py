"""
Phase 4: Fine-tune PubMedBERT for drug-gene evidence classification.
Three tasks simultaneously:
  1. supports_relationship (binary)
  2. mechanism (multi-class)
  3. direction (multi-class)
"""

import os
import json
import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_NAME    = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
MAX_LENGTH    = 512
BATCH_SIZE    = 8
EPOCHS        = 5
LEARNING_RATE = 2e-5
OUTPUT_DIR    = "models/pubmedbert_drug_gene"
VERSION       = "v4_retrain"
DATA_PATH    = "data/annotations/training_dataset_v4.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Label definitions ─────────────────────────────────────────────────────────
MECHANISM_LABELS = [
    "inhibitor", "antagonist", "agonist", "activator",
    "downregulator", "upregulator", "degrader",
    "binder_only", "modulator_unclear_direction", "unknown"
]

DIRECTION_LABELS = [
    "decreases_expression", "increases_expression",
    "decreases_activity", "increases_activity",
    "mixed", "unclear", "not_applicable"
]

# ── Dataset ───────────────────────────────────────────────────────────────────
class DrugGeneDataset(Dataset):
    def __init__(self, records, tokenizer, max_length=512):
        self.records    = records
        self.tokenizer  = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        r = self.records[idx]
        # Input: [gene] [SEP] [drug] [SEP] [abstract text]
        text = f"{r['gene']} [SEP] {r['drug']} [SEP] {r['text']}"
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids":      encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "label_rel":      torch.tensor(r["label_rel"],  dtype=torch.long),
            "label_mech":     torch.tensor(r["label_mech"], dtype=torch.long),
            "label_dir":      torch.tensor(r["label_dir"],  dtype=torch.long),
        }

# ── Model ─────────────────────────────────────────────────────────────────────
class DrugGeneClassifier(nn.Module):
    def __init__(self, model_name, n_mech, n_dir):
        super().__init__()
        self.bert      = AutoModel.from_pretrained(model_name)
        hidden         = self.bert.config.hidden_size
        self.dropout   = nn.Dropout(0.1)
        # Three classification heads
        self.head_rel  = nn.Linear(hidden, 2)        # binary
        self.head_mech = nn.Linear(hidden, n_mech)   # mechanism
        self.head_dir  = nn.Linear(hidden, n_dir)    # direction

    def forward(self, input_ids, attention_mask):
        out    = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.dropout(out.last_hidden_state[:, 0, :])  # [CLS] token
        return (
            self.head_rel(pooled),
            self.head_mech(pooled),
            self.head_dir(pooled)
        )

# ── Data loading ──────────────────────────────────────────────────────────────
def load_data(path):
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} total rows")

    # Use reviewed gold labels where available, else LLM labels
    df["final_mechanism"] = df["reviewed_gold_correct_mechanism"].fillna(
        df["gold_correct_mechanism"]
    ).fillna(df["llm_mechanism"]).fillna("unknown")

    df["final_direction"] = df["reviewed_gold_correct_direction"].fillna(
        df["gold_correct_direction"]
    ).fillna(df["llm_direction"]).fillna("unclear")

    df["final_rel"] = df["llm_supports_relationship"].fillna(False).astype(bool)

    # Normalize labels
    df["final_mechanism"] = df["final_mechanism"].str.lower().str.strip()
    df["final_direction"]  = df["final_direction"].str.lower().str.strip()

    # Map to known labels
    df["final_mechanism"] = df["final_mechanism"].apply(
        lambda x: x if x in MECHANISM_LABELS else "unknown"
    )
    df["final_direction"] = df["final_direction"].apply(
        lambda x: x if x in DIRECTION_LABELS else "unclear"
    )

    # Encode labels
    mech_to_id = {m: i for i, m in enumerate(MECHANISM_LABELS)}
    dir_to_id  = {d: i for i, d in enumerate(DIRECTION_LABELS)}

    records = []
    for _, row in df.iterrows():
        text = str(row.get("text", ""))
        if not text or len(text) < 10:
            continue
        records.append({
            "gene":      str(row.get("gene", "")),
            "drug":      str(row.get("drug", "")),
            "text":      text[:2000],
            "label_rel":  int(row["final_rel"]),
            "label_mech": mech_to_id.get(row["final_mechanism"], 9),
            "label_dir":  dir_to_id.get(row["final_direction"],  5),
            "is_gold":    bool(row.get("is_gold_standard", False)),
        })

    print(f"Valid records: {len(records)}")
    print(f"Gold standard: {sum(r['is_gold'] for r in records)}")
    print(f"Relationship dist: {pd.Series([r['label_rel'] for r in records]).value_counts().to_dict()}")

    # Save label mappings
    with open(os.path.join(OUTPUT_DIR, "label_maps.json"), "w") as f:
        json.dump({"mechanism": mech_to_id, "direction": dir_to_id}, f, indent=2)

    return records, mech_to_id, dir_to_id

# ── Training ──────────────────────────────────────────────────────────────────
def train():
    print(f"\n{'='*60}")
    print("Phase 4: Fine-tuning PubMedBERT")
    print(f"{'='*60}\n")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load data
    records, mech_to_id, dir_to_id = load_data(DATA_PATH)

    # Split — oversample gold standard in train
    gold    = [r for r in records if r["is_gold"]]
    non_gold = [r for r in records if not r["is_gold"]]

    train_ng, val_ng = train_test_split(non_gold, test_size=0.15, random_state=42)
    train_g,  val_g  = train_test_split(gold,     test_size=0.15, random_state=42)

    # Gold standard gets 3x weight by repeating in training set
    train_records = train_ng + train_g * 3
    val_records   = val_ng   + val_g

    print(f"\nTrain: {len(train_records)} | Val: {len(val_records)}")
    print(f"Train gold (3x): {len(train_g)*3} | Val gold: {len(val_g)}")

    # Tokenizer and datasets
    print(f"\nLoading tokenizer: {MODEL_NAME}")
    tokenizer    = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_dataset = DrugGeneDataset(train_records, tokenizer, MAX_LENGTH)
    val_dataset   = DrugGeneDataset(val_records,   tokenizer, MAX_LENGTH)
    train_loader  = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader    = DataLoader(val_dataset,   batch_size=BATCH_SIZE)

    # Model
    print(f"Loading model: {MODEL_NAME}")
    model = DrugGeneClassifier(MODEL_NAME, len(MECHANISM_LABELS), len(DIRECTION_LABELS))
    model.to(device)

    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps//10, num_training_steps=total_steps
    )
    loss_fn = nn.CrossEntropyLoss()

    best_val_f1 = 0.0

    for epoch in range(EPOCHS):
        # ── Train ──
        model.train()
        total_loss = 0
        for batch in train_loader:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            label_rel      = batch["label_rel"].to(device)
            label_mech     = batch["label_mech"].to(device)
            label_dir      = batch["label_dir"].to(device)

            optimizer.zero_grad()
            logits_rel, logits_mech, logits_dir = model(input_ids, attention_mask)

            loss = (
                loss_fn(logits_rel,  label_rel)  * 1.0 +
                loss_fn(logits_mech, label_mech) * 1.5 +
                loss_fn(logits_dir,  label_dir)  * 1.5
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # ── Validate ──
        model.eval()
        all_rel, all_mech, all_dir = [], [], []
        pred_rel, pred_mech, pred_dir = [], [], []

        with torch.no_grad():
            for batch in val_loader:
                input_ids      = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                logits_rel, logits_mech, logits_dir = model(input_ids, attention_mask)

                pred_rel  += logits_rel.argmax(-1).cpu().tolist()
                pred_mech += logits_mech.argmax(-1).cpu().tolist()
                pred_dir  += logits_dir.argmax(-1).cpu().tolist()
                all_rel   += batch["label_rel"].tolist()
                all_mech  += batch["label_mech"].tolist()
                all_dir   += batch["label_dir"].tolist()

        f1_rel  = f1_score(all_rel,  pred_rel,  average="macro", zero_division=0)
        f1_mech = f1_score(all_mech, pred_mech, average="macro", zero_division=0)
        f1_dir  = f1_score(all_dir,  pred_dir,  average="macro", zero_division=0)
        avg_f1  = (f1_rel + f1_mech + f1_dir) / 3

        print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {avg_loss:.4f} | "
              f"F1 rel: {f1_rel:.3f} | mech: {f1_mech:.3f} | dir: {f1_dir:.3f} | avg: {avg_f1:.3f}")

        # Save best model
        if avg_f1 > best_val_f1:
            best_val_f1 = avg_f1
            # Save to standard location
            model.bert.save_pretrained(os.path.join(OUTPUT_DIR, "best_model"))
            tokenizer.save_pretrained(os.path.join(OUTPUT_DIR, "best_model"))
            torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, "best_model_state.pt"))
            # Save versioned copy so previous versions are never overwritten
            versioned_dir = os.path.join(OUTPUT_DIR, f"best_model_{VERSION}")
            os.makedirs(versioned_dir, exist_ok=True)
            model.bert.save_pretrained(versioned_dir)
            tokenizer.save_pretrained(versioned_dir)
            torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, f"best_model_state_{VERSION}.pt"))
            print(f"  -> Saved best model (avg F1: {avg_f1:.3f}) [{VERSION}]")

    # Final evaluation on validation set
    print(f"\n{'='*60}")
    print("FINAL EVALUATION")
    print(f"{'='*60}")
    print("\nRelationship Detection:")
    print(classification_report(all_rel, pred_rel,
          target_names=["no_relationship", "supported"], zero_division=0))
    print("\nMechanism Classification:")
    print(classification_report(all_mech, pred_mech,
          target_names=MECHANISM_LABELS, zero_division=0))
    print("\nDirection Classification:")
    print(classification_report(all_dir, pred_dir,
          target_names=DIRECTION_LABELS, zero_division=0))

    print(f"\nBest validation F1: {best_val_f1:.3f}")
    print(f"Model saved to: {OUTPUT_DIR}/best_model")

if __name__ == "__main__":
    train()
