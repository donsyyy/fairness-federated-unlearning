# 📦 Fairness-Aware Federated Unlearning for IoT Networks

An advanced, decentralized DevSecOps laboratory designed to evaluate machine unlearning ($q$-FedAvg) within highly heterogeneous, non-IID Internet of Things (IoT) network settings. This project provides a fully localized, containerized pipeline to evaluate data erasure against adversarial **Membership Inference Attacks (MIA)**.

---

## 🏗️ System Architecture Overview

Unlike classical implementations running on heavy, volatile virtual machines (VMs) that trigger hardware RAM exhaustion, this framework leverages lightweight Linux kernel virtualization (**LXC/LXD**). 

* **The Server Core (Host Node):** Manages global parameter aggregation, orchestrates asynchronous round validation loops, and logs metrics.
* **The Cluster Client Edge (LXC Containers):** 4 isolated, lightweight instances executing local optimization passes concurrently using specialized background runtimes.
* **Communication Matrix:** Managed via an asynchronous Pub/Sub topology powered by an optimized **MQTT** broker interface.

---

## 📋 Hardware & Resource Efficiency

| Performance Metric | Traditional Hypervisors (VirtualBox) | Our Lightweight LXC Cluster |
| :--- | :--- | :--- |
| **Active Concurrent Nodes** | Maximum 3 clients (System Crash) | **4 Clients + 1 Central Aggregator Server** |
| **Total Memory Consumption**| $> 16$ GB RAM (Total Saturated) | **$< 8$ GB RAM Total Footprint** |
| **Storage Allocation Mode** | Monolithic Pre-Allocated Virtual Disks | **Zero-Copy Bind-Mount Shared Volume** |
| **Initial Provisioning Time**| Multiple Hours (Manual Setup per OS) | **$< 5$ Minutes (Golden Image Pipeline)** |

---

## 📖 Deep Documentation Index

To ensure total reproducibility, the system deployment blueprint has been broken down into granular, actionable engineering sheets. Navigate through them sequentially to stand up and evaluate the environment:

0. 🧩 **[System Prerequisites & Hypervisor Installation (docs/prerequisites.md)](docs/prerequisites.md)** *Complete step-by-step installation guides for the snap-based LXC/LXD virtualization daemon, post-install environment configurations, core system reboots, and engine validation testing.*

1. 📦 **[Infrastructure & Cluster Provisioning (docs/infrastructure.md)](docs/infrastructure.md)** *Step-by-step guides for host packet dependencies, LXD project workspace isolation, directory-backed storage pool mapping, automated "Golden Image" batch-cloning, and live interface cache refreshes.*

2. 🏃‍♂️ **[Runtime Orchestration & Security Auditing (docs/runtime.md)](docs/runtime.md)** *Zero-copy data volume bind-mounting, concurrent background client container initialization loops, model metadata tracking, and evaluating data erasure using the Membership Inference Attack (`mia_audit.py`) suite.*

3. 🩺 **[Network Troubleshooting & Diagnostics Matrix (docs/troubleshooting.md)](docs/troubleshooting.md)** *A complete recovery reference for resolving MQTT startup synchronization deadlocks, patching PyTorch unexpected keyword weight exceptions, restoring hung LXD virtual bridge interfaces, and injecting host-level NAT masquerading rules.*