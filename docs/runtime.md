# 🏃‍♂️ Runtime Orchestration & Security Auditing Pipeline

This document guides you through connecting your zero-copy storage resources, executing parallel asynchronous container scripts, and running the defensive evaluation suite.

> 🛑 **PREREQUISITE CHECKPOINT:**
> 
> Before proceeding with these execution steps, ensure you have completely configured your host and container cluster by following the **[Infrastructure Setup Guide (infrastructure.md)](infrastructure.md)**. Do not carry on if your containers do not yet show a valid `10.111.79.X` IP address.

---

## 💾 1. Zero-Copy Shared Workspace Configuration

To prevent duplicating large network traffic CSV datasets (UNSW-NB15 / ML-EdgeIIoT) across every individual instance, execute a physical disk segment bind-mount. The data consumes exactly 1x storage blocks while remaining globally accessible.

```bash
# Bind-mount the host dataset workspace to the entire cluster concurrently
for i in {1..4}; do
  lxc config device add iot-device-$i shared-data disk source=~/PFA_FU_Project/client_shared_data path=/root/workspace
done
```

## 🏃‍♂️ 2. Asynchronous Simulation Runtime Execution

The system execution relies on a robust Pub/Sub asynchronous workflow topology. The host handles global aggregation, while the containers process local model gradients concurrently in the background.

### Step 2.1: Start the Central Aggregator (On the Host Terminal)

```bash
cd ~/PFA_FU_Project/
python3 serverSDG.py
```

The server initializes its network stack and listens for client connections.

### Step 2.2: Launch the Asynchronous Client Cluster (Via Host Context)

Open a new terminal window on the host machine and trigger the concurrent client background loops. Using the ampersand (&) token forces the container processes into background execution:

```bash
lxc exec iot-device-1 --project FU-Project -- python3 /root/workspace/clientSDG_0.py 0 workspace/client_0.csv workspace/test.csv &
sleep 1.5
lxc exec iot-device-2 --project FU-Project -- python3 /root/workspace/clientSDG_0.py 1 workspace/client_1.csv workspace/test.csv &
sleep 1.5
lxc exec iot-device-3 --project FU-Project -- python3 /root/workspace/clientSDG_0.py 2 workspace/client_2.csv workspace/test.csv &
sleep 1.5
lxc exec iot-device-4 --project FU-Project -- python3 /root/workspace/clientSDG_0.py 3 workspace/client_3.csv workspace/test.csv &
```

## 🔍 3. Security Auditing (Membership Inference Attack)

At Round 10, the server triggers strict client unlearning, resulting in two output models at Round 14: model_infected.pth and model_unlearned.pth. To mathematically prove that Client 0's private footprint was cleanly purged from the model weights, run the loss profile attack:

```bash
python3 mia_audit.py
```

> 📌 **Auditing Validation Target:**
> 
> A structural loss profile difference exceeding **15%** on the unlearned model weights verifies that the network data footprint was successfully purged from the system matrices.

> 👉 **Stuck on a Runtime or Connection Error?** Check out the resolution steps in the [**Network Troubleshooting & Diagnostics Matrix**](troubleshooting.md).