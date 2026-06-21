# 📦 Cluster Infrastructure Setup: LXC/LXD & Host Provisioning

This document outlines the step-by-step environment setup required to build the virtualized IoT edge emulation lab using lightweight Linux containers (**LXC/LXD**).

## 📋 1. Prerequisites & Host Node Dependencies

The system execution relies on an asynchronous Pub/Sub message matrix. The central host gateway must run a dedicated message broker and possess essential Python environments.

### Step 1.1: Install Core System Packages
Open a terminal on your host machine (Kali/Ubuntu) and install the Mosquitto MQTT suite along with Python compilation tools:

```bash
sudo apt update && sudo apt install -y mosquitto mosquitto-clients python3-pip python3-venv git
```

### Step 1.2: Initialize and Verify the Central MQTT Broker

Force the broker service to initialize and verify that its socket daemon is actively bound and listening natively on port 1883:

```bash
# Start and enable the daemon on system boot
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Verify operational status
sudo systemctl status mosquitto
```

> ⚠️ CRITICAL NETWORK CONFIGURATION NOTE:
> By default, modern Mosquitto installations restrict traffic exclusively to the loopback interface (localhost). To allow virtualized container interfaces (10.111.79.X) to hit the host broker gateway, you must open the configuration file:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Append these overriding parameters to the very bottom:
```bash
    listener 1883 0.0.0.0
    allow_anonymous true
```

Restart the service to apply changes: 
```bash
sudo systemctl restart mosquitto
```

## 📦 2. Initializing the Isolated LXC/LXD Fabric

We leverage container-level namespace virtualization via LXC/LXD to bypass heavy hypervisor storage and CPU translation penalties.

### Step 2.1: Establish a Dedicated Storage Pool Boundary

To protect the host root partition from heavy deep learning image layers and cached Python wheels, map an independent, directory-backed storage engine directly to your external media:
Bash

```bash
lxc storage create FU_storage_pool dir source=~/PFA_FU_Project/lxd_storage
```

### Step 2.2: Isolate the Project Security Namespace

Create a sandboxed LXD project compartment. This isolates our security laboratory's bridge profiles, container tracking tables, and base container image layers from the default system profile:

```bash
# 1. Create the dedicated laboratory project space
lxc project create FU-Project -c features.images=true -c features.profiles=true

# 2. Switch the active context to the new project
lxc project switch FU-Project
```

## 🛠️ 3. "Golden Image" Pipeline & Cluster Replication

Instead of installing a 1.5 GB Machine Learning runtime (PyTorch, Pandas, Scikit-Learn) across 4 individual container nodes sequentially, configure a single reference prototype node, capture its filesystem, and batch-clone it locally.

### Step 3.1: Build and Provision the Prototype Base

```bash
# Launch a base reference node using Ubuntu 22.04 LTS
lxc launch images:ubuntu/22.04 iot-device-1

# Drop into the reference container's terminal bash session
lxc exec iot-device-1 -- bash
```

Execute the following deployment block inside the iot-device-1 shell:

```bash
# Update local software sources and install core tools
apt update && apt install -y python3-pip python3-dev

# Deploy the complete Machine Learning runtime via pip3
pip3 install torch pandas numpy scikit-learn paho-mqtt

# Exit back to the host machine context
exit
```
If the previous pip3 command fails, install native system packages instead:
```bash
# Strategy B (Fallback):
apt install -y python3-pandas python3-numpy python3-torch python3-sklearn python3-paho-mqtt -y
```

### Step 3.2: Freeze the Blueprint and Batch-Clone the Edge Nodes

Stop the active instance, publish its volume state as an immutable local "Golden Image," and run a structured loop to spin up the rest of the edge cluster. The loop injects static network mappings onto the lxdbr0 virtual bridge interface:

```bash
# Freeze the reference prototype container
lxc stop iot-device-1

# Publish the prototype to the local image cache under an alias
lxc publish iot-device-1 --alias fu-base-image

# Execute automated batch deployment loop for the rest of the cluster
for i in {1..4}; do
  if [ $i -ne 1 ]; then
    lxc launch fu-base-image iot-device-$i
  fi
  lxc config device add iot-device-$i eth0 nic network=lxdbr0 name=eth0 ipv4.address=10.111.79.1$i
  lxc config set iot-device-$i security.nesting true
done
```

## 👥 Verification Check

To verify that your entire 4-node edge cluster is up, nested correctly, and actively holding their dedicated laboratory IP addresses, execute:

```bash
lxc list -c n,s,4
```

> 📌 **Success Verification:**
> Before proceeding to the next stage, ensure that the 10.111.79.X static IP addresses appear correctly under the IPV4 column for all four container instances. If a node displays no IP address, re-run the interface refresh loop above.

## ➡️ Next Step

Now that your containerized environment is fully provisioned, isolated, and bridged, move on to configuring the shared storage and executing the simulation matrix:

## 📑 **[Proceed to Runtime Orchestration & Security Auditing (docs/runtime.md)](docs/runtime.md)**