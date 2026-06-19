import pickle
import paho.mqtt.client as mqtt
import torch
import torch.nn as nn
import os

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

class Server:
    def __init__(self, num_clients=4, rounds=16): # 16 rounds (0 à 15)
        self.num_clients = num_clients
        self.rounds = rounds
        self.round = 0

        self.model = IDS_MLP()
        self.updates = {}
        self.ready = set()

        self.q = 2.0        
        self.learning_rate = 0.1  

        # --- ÉTAPE 1 & 2 : MÉMOIRE ET SAUVEGARDE DE L'OUBLI ---
        self.history = {} 

        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[SERVER] Connected. Starting Round {self.round}")
        client.subscribe("client/ready")
        client.subscribe("client/update/+")

    def on_message(self, client, userdata, msg):
        # ---------------------------------------------------------
        # PHASE A: HANDLING CLIENT CHECK-INS ("client/ready")
        # ---------------------------------------------------------
        if msg.topic == "client/ready":
            cid = msg.payload.decode()
            
            # Gestion de l'isolation du Client 0 pendant la réparation (Rounds 10 à 14)
            if self.round >= 10 and self.round < 15 and cid == "0":
                print(f"[SERVER] Phase d'oubli -> Client {cid} mis en sommeil.")
                return
            
            self.ready.add(cid)

            # Define exactly who we are waiting for to kick off the round
            if self.round == 15:
                expected_ready = 1  # Only waiting for Audit Client 0
            elif 10 <= self.round < 15:
                expected_ready = 3  # Waiting for Clients 1, 2, and 3
            else:
                expected_ready = self.num_clients  # Waiting for all 4 clients (Rounds 0-9)
            
            if len(self.ready) == expected_ready:
                self.ready = set()
                self.send_global()
            return

        # ---------------------------------------------------------
        # PHASE B: HANDLING MODEL WEIGHT UPDATES ("client/update/+")
        # ---------------------------------------------------------

        cid = msg.topic.split("/")[-1]

        # TEST ULTIME AU ROUND 15: Execute the audit immediately when Client 0 reports back
        if self.round == 15:
            if cid == "0":
                print("\n=======================================================")
                print("== AUDIT FU : RÉSULTAT DU CLIENT 0 SUR LE MODÈLE PURGÉ ==")
                print("=======================================================")
                update = pickle.loads(msg.payload)
                print(f" -> Client 0 | F1 Macro: {update['f1']:.4f} | Acc: {update['accuracy']:.4f}")
                torch.save(self.model.state_dict(), "model_unlearned.pth")
                print("[SERVER] Modèle purgé sauvegardé sous 'model_unlearned.pth'.")
                print("=======================================================\n")
                self.mqtt.loop_stop()
            return

        # If we are in the unlearning phase, instantly discard any stray updates from Client 0
        if 10 <= self.round < 15 and cid == "0":
            return  # Drop the packet completely! It never enters self.updates

        # Standard tracking logic for rounds 0 through 14
        self.updates[cid] = pickle.loads(msg.payload)

        # Define exactly how many updates we need to close the aggregation window
        expected_updates = 3 if 10 <= self.round < 15 else self.num_clients

        if len(self.updates) == expected_updates:
            print(f"\n--- Aggregating Round {self.round} ---")

            if self.round == 9:
                torch.save(self.model.state_dict(), "model_infected.pth")
                print("[SERVER] Modèle infecté (avec Client 0) sauvegardé sous 'model_infected.pth'.")

            self.aggregate()
            self.updates = {}
            self.round += 1

            if self.round < self.rounds:
                self.send_global()


    def aggregate(self):
        clients = list(self.updates.keys())
        global_state = self.model.state_dict()
        deltas, hs = [], []

        # STRATÉGIE FU : Si Round >= 10, on bannit le Client 0 de l'agrégation q-FedAvg
        if self.round >= 10:
            print(f"[SERVER] [UNLEARNING] Exclusion stricte du Client 0.")
            clients_a_agreger = [cid for cid in clients if cid != "0"]
        else:
            clients_a_agreger = clients

        for cid in clients_a_agreger:
            local_state = self.updates[cid]["state_dict"]
            f1 = self.updates[cid]["f1"]
            loss = max(1.0 - f1, 1e-8)

            local_delta = {}
            for k in global_state:
                local_delta[k] = global_state[k].float() - local_state[k].float()

            delta_norm_sq = sum(d.pow(2).sum().item() for d in local_delta.values())
            num_scale = (loss ** self.q)
            den_scale = (self.q * (loss ** max(self.q - 1, 0)) * delta_norm_sq) + (loss ** self.q)

            deltas.append((local_delta, num_scale))
            hs.append(den_scale)

        aggregated_delta = {k: torch.zeros_like(v, dtype=torch.float32) for k, v in global_state.items()}
        total_h = sum(hs) if sum(hs) > 0 else 1e-8

        for local_delta, num_scale in deltas:
            weight = num_scale / total_h
            for k in aggregated_delta:
                aggregated_delta[k] += weight * local_delta[k]

        new_global_state = {}
        for k in global_state:
            new_global_state[k] = global_state[k].float() - (self.learning_rate * aggregated_delta[k])

        self.model.load_state_dict(new_global_state)

        print("[SERVER] Target Metrics Received This Round:")
        for cid in clients:
            update = self.updates[cid]
            print(f"  -> Client {cid} | F1: {update['f1']:.4f} | Acc: {update['accuracy']:.4f}")

    def send_global(self):
        # On envoie un signal spécial au client 0 si c'est le round de test final
        payload_dict = {"weights": self.model.state_dict(), "is_final_test": (self.round == 15)}
        self.mqtt.publish("server/global", pickle.dumps(payload_dict))

    def start(self):
        self.mqtt.connect("127.0.0.1", 1883)
        self.mqtt.loop_forever()

if __name__ == "__main__":
    Server(num_clients=4, rounds=16).start()
