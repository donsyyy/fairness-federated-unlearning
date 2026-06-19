import paho.mqtt.client as mqtt
import pandas as pd
import pickle
import sys
import time
import random

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report


# =========================================================
# MODEL
# =========================================================
class IDS_MLP(nn.Module):
    def __init__(self, input_size=42):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.net(x)


# =========================================================
# CLIENT
# =========================================================
class Client:

    def __init__(self, client_id, train_path, test_path):
        self.client_id = client_id

        # Thread synchronization flags
        self.active_round = False
        self.msg_payload = None

        # 1. Load Data & Compute Local Positive Class Weight
        self.X_train, self.y_train, self.X_test, self.y_test, self.pos_weight = self.load_data(train_path, test_path)

        self.train_loader = DataLoader(
            TensorDataset(self.X_train, self.y_train),
            batch_size=256, shuffle=True
        )

        self.test_loader = DataLoader(
            TensorDataset(self.X_test, self.y_test),
            batch_size=256, shuffle=False
        )

        self.model = IDS_MLP(self.X_train.shape[1])
        
        # 2. Assign dynamic class weighting directly to the loss function
        print(f"[CLIENT {self.client_id}] Computed pos_weight penalty for Attack class: {self.pos_weight.item():.4f}")
        self.loss_fn = nn.BCEWithLogitsLoss(pos_weight=self.pos_weight)
        
        self.opt = optim.Adam(self.model.parameters(), lr=0.001)

        # FIX: Explicitly use Paho MQTT API v2 to resolve deprecation warnings
        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message

    # ---------------- DATA ----------------
    def load_data(self, train_path, test_path):
        train = pd.read_csv(train_path)
        test = pd.read_csv(test_path)

        drop = ['id', 'attack_cat']
        train = train.drop(columns=[c for c in drop if c in train.columns])
        test = test.drop(columns=[c for c in drop if c in test.columns])

        target = 'label' if 'label' in train.columns else 'Label'

        X_train = train.drop(columns=[target])
        y_train = train[target].values

        X_test = test.drop(columns=[target])
        y_test = test[target].values

        # --- DYNAMIC CLASS BALANCING ---
        num_negatives = (y_train == 0).sum()
        num_positives = (y_train == 1).sum()
        
        if num_positives == 0: 
            num_positives = 1
            
        pos_weight_val = num_negatives / num_positives
        pos_weight_tensor = torch.tensor([pos_weight_val], dtype=torch.float32)

        for col in ['proto', 'service', 'state']:
            if col in X_train.columns:
                le = LabelEncoder()
                all_vals = pd.concat([X_train[col], X_test[col]]).astype(str)
                le.fit(all_vals)

                X_train[col] = le.transform(X_train[col].astype(str))
                X_test[col] = le.transform(X_test[col].astype(str))

        scaler = StandardScaler()
        num_cols = X_train.select_dtypes(include=['int64','float64']).columns

        X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
        X_test[num_cols] = scaler.transform(X_test[num_cols])

        return (
            torch.tensor(X_train.values, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.float32).unsqueeze(1),
            torch.tensor(X_test.values, dtype=torch.float32),
            torch.tensor(y_test, dtype=torch.float32).unsqueeze(1),
            pos_weight_tensor
        )

    # ---------------- TRAIN ----------------
    def train(self, epochs=1):
        self.model.train()

        for _ in range(epochs):
            for X, y in self.train_loader:
                self.opt.zero_grad()
                loss = self.loss_fn(self.model(X), y)
                loss.backward()
                self.opt.step()

    # ---------------- EVALUATION WITH THRESHOLD CALIBRATION ----------------
    def evaluate(self):
        self.model.eval()

        all_probs, all_targets = [], []

        with torch.no_grad():
            for X, y in self.test_loader:
                probs = torch.sigmoid(self.model(X))
                all_probs.extend(probs.numpy())
                all_targets.extend(y.numpy())

        # --- POST-TRAINING THRESHOLD CALIBRATION SWEEP ---
        # --- POST-TRAINING THRESHOLD CALIBRATION SWEEP (MACRO F1) ---
        best_threshold = 0.5
        best_f1_macro = -1.0
        
        for t in [i / 20.0 for i in range(1, 20)]: # Version rapide par pas de 0.05
            preds = [(p >= t) for p in all_probs]
            # FIX: On force le calcul en 'macro' pour prendre en compte le Normal ET l'Attaque
            current_f1_macro = f1_score(all_targets, preds, average='macro', zero_division=0)
            
            if current_f1_macro > best_f1_macro:
                best_f1_macro = current_f1_macro
                best_threshold = t

        print(f"[CLIENT {self.client_id}] Optimal threshold calibrated to: {best_threshold:.2f} (Max Macro F1: {best_f1_macro:.4f})")
        final_preds = [(p >= best_threshold) for p in all_probs]
        
        precision = precision_score(all_targets, final_preds, zero_division=0)
        recall    = recall_score(all_targets, final_preds, zero_division=0)
        f1 = f1_score(all_targets, final_preds, average='macro', zero_division=0)
        acc       = accuracy_score(all_targets, final_preds)

        # --- EXTRACTION DES METRIQUES PAR CLASSE ---
        report_dict = classification_report(
            all_targets, final_preds,
            target_names=["Normal", "Attaque"],
            zero_division=0,
            output_dict=True
        )
        
        classify_metrics = {
            "normal": {
                "precision": report_dict["Normal"]["precision"],
                "recall": report_dict["Normal"]["recall"],
                "f1": report_dict["Normal"]["f1-score"]
            },
            "attaque": {
                "precision": report_dict["Attaque"]["precision"],
                "recall": report_dict["Attaque"]["recall"],
                "f1": report_dict["Attaque"]["f1-score"]
            }
        }

        print(f"[CLIENT {self.client_id}] Final Metrics -> Acc:{acc:.4f} P:{precision:.4f} R:{recall:.4f} F1:{f1:.4f}")
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": acc,
            "classify_metrics": classify_metrics
        }

    # ---------------- WEIGHTS ----------------
    def get_state(self):
        return {k: v.cpu() for k, v in self.model.state_dict().items()}

    def load_state(self, payload):
        raw_state = pickle.loads(payload)
        
        if any(isinstance(k, int) for k in raw_state.keys()):
            model_keys = list(self.model.state_dict().keys())
            cleaned_state = {model_keys[i]: torch.tensor(v) if not isinstance(v, torch.Tensor) else v 
                             for i, (k, v) in enumerate(raw_state.items())}
            self.model.load_state_dict(cleaned_state)
        else:
            self.model.load_state_dict(raw_state)

    # ---------------- MQTT CALLBACKS ----------------
    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[CLIENT {self.client_id}] Connected to broker. Ready for execution loop.")
        client.subscribe("server/global")
        client.publish("client/ready", str(self.client_id))

    def on_message(self, client, userdata, msg):
        # FIX: Simply capture data and exit callback immediately to prevent background thread hang
        self.msg_payload = msg.payload
        self.active_round = True

    # ---------------- ENGINE START ----------------
    def load_state(self, payload):
        data = pickle.loads(payload)
        # Décodage du dictionnaire ou des poids bruts
        raw_state = data["weights"] if isinstance(data, dict) and "weights" in data else data
        
        if any(isinstance(k, int) for k in raw_state.keys()):
            model_keys = list(self.model.state_dict().keys())
            cleaned_state = {model_keys[i]: torch.tensor(v) if not isinstance(v, torch.Tensor) else v 
                             for i, (k, v) in enumerate(raw_state.items())}
            self.model.load_state_dict(cleaned_state)
        else:
            self.model.load_state_dict(raw_state)
        return data

    def start(self):
        print("Avant connexion MQTT")
        self.mqtt.connect("10.111.79.1", 1883)
        print("Après connexion MQTT")

        self.mqtt.loop_start()
        print("Loop MQTT démarrée")
        try:
            while True:
                if self.active_round and self.msg_payload is not None:
                    meta_data = self.load_state(self.msg_payload)
                    is_final_test = isinstance(meta_data, dict) and meta_data.get("is_final_test", False)

                    if is_final_test:
                        print(f"[CLIENT {self.client_id}] Final unlearning audit signal received. Evaluating only...")
                        metrics = self.evaluate()
                    else:
                        print(f"[CLIENT {self.client_id}] Starting local training round...")
                        self.train(epochs=1)
                        metrics = self.evaluate()

                    payload = pickle.dumps({
                        "state_dict": self.get_state(),
                        "precision": metrics["precision"],
                        "recall": metrics["recall"],
                        "f1": metrics["f1"],
                        "accuracy": metrics["accuracy"],
                        "classify_metrics": metrics["classify_metrics"]
                    })
                    self.mqtt.publish(f"client/update/{self.client_id}", payload)
                    
                    self.active_round = False
                    self.msg_payload = None
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.mqtt.loop_stop()


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python client.py <client_id> <train_path> <test_path>")
        sys.exit(1)
        
    c = Client(sys.argv[1], sys.argv[2], sys.argv[3])
    c.start()
