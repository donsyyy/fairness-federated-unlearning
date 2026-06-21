## 💾 3: Zero-Copy Shared Workspace Configuration

To prevent duplicating large network traffic CSV datasets (UNSW-NB15 / ML-EdgeIIoT) across every individual instance, execute a physical disk segment bind-mount. The data consumes exactly 1x storage blocks while remaining globally accessible.

```bash
# Bind-mount the host dataset workspace to the entire cluster concurrently
for i in {1..4}; do
  lxc config device add iot-device-$i shared-data disk source=~/PFA_FU_Project/client_shared_data path=/root/workspace
done
```

## 🏃‍♂️ 4: Asynchronous Simulation Runtime Execution

The system execution relies on a robust Pub/Sub asynchronous workflow topology. The host handles global aggregation, while the containers process local model gradients concurrently in the background.

### Step 4.1: Start the Central Aggregator (On the Host Terminal)

```bash
cd ~/PFA_FU_Project/
python3 serverSDG.py
```

The server initializes its network stack and listens for client connections.

### Step 4.2: Launch the Asynchronous Client Cluster (Via Host Context)

Open a new terminal window on the host machine and trigger the concurrent client background loops. Using the ampersand (&) token forces the container processes into background execution:

```bash
lxc exec iot-device-1 -- python3 /root/workspace/clientSDG_0.py 0 workspace/client_0.csv workspace/test.csv &
sleep 1.5
lxc exec iot-device-2 -- python3 /root/workspace/clientSDG_0.py 1 workspace/client_1.csv workspace/test.csv &
sleep 1.5
lxc exec iot-device-3 -- python3 /root/workspace/clientSDG_0.py 2 workspace/client_2.csv workspace/test.csv &
sleep 1.5
lxc exec iot-device-4 -- python3 /root/workspace/clientSDG_0.py 3 workspace/client_3.csv workspace/test.csv &
```

## 🔍 5: Security Auditing (Membership Inference Attack)

At Round 10, the server triggers strict client unlearning, resulting in two output models at Round 14: model_infected.pth and model_unlearned.pth. To mathematically prove that Client 0's private footprint was cleanly purged from the model weights, run the loss profile attack:

```bash
python3 mia_audit.py
```

> Success Metric: A structural entropy/loss increase exceeding 15% on the unlearned weights file confirms that Client 0's data was successfully forgotten by q-FedAvg under the hood, regardless of standard classification accuracy metrics.

## 📑 **[Having trouble with runtime errors or network? Check out the troubleshooting file (docs/troubleshooting.md)](docs/troubleshooting.md)**