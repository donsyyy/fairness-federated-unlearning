# Fairness-Aware Federated Unlearning for IoT Networks

An advanced, decentralized DevSecOps laboratory designed to evaluate machine unlearning ($q$-FedAvg) within highly heterogeneous, non-IID Internet of Things (IoT) network settings. This project provides a fully localized, containerized pipeline to evaluate data erasure against adversarial **Membership Inference Attacks (MIA)**.

## 🏗️ System Architecture Overview

Unlike classical implementations running on heavy, volatile virtual machines (VMs) that trigger hardware RAM exhaustion, this framework leverages lightweight Linux kernel virtualization (**LXC/LXD**). 

* **The Server Core (Host Hôte):** Manages global parameter aggregation, orchestrates asynchronous round validation loops, and logs metrics.
* **The Cluster Client Edge (LXC Containers):** 4 isolated, lightweight instances executing local optimization passes concurrently using specialized background runtimes.
* **Communication Matrix:** Managed via an asynchronous Pub/Sub topology powered by an optimized **MQTT** broker interface.

---

## 📋 Hardware & Resource Efficience

| Performance Metric | Traditional Hypervisors (VirtualBox) | Our Lightweight LXC Cluster |
| :--- | :--- | :--- |
| **Active Concurrent Nodes** | Maximum 3 clients (System Crash) | **4 Clients + 1 Central Aggregator Server** |
| **Total Memory Consumption**| $> 16$ GB RAM (Total Saturated) | **$< 8$ GB RAM Total Footprint** |
| **Storage Allocation Mode** | Monolithic Pre-Allocated Virtual Disks | **Zero-Copy Bind-Mount Shared Volume** |
| **Initial Provisioning Time**| Multiple Hours (Manual Setup per OS) | **$< 5$ Minutes (Golden Image Pipeline)** |

---

## 📖 Deep Documentation Index

To ensure reproducibility, the system deployment blueprint has been broken down into granular, actionable engineering sheets:

1. **[Infrastructure & Cluster Provisioning](docs/infrastructure.md)** *Step-by-step guides for host setup, LXD project boundary mapping, storage pool isolation, and automated Golden Image batch-cloning loop.*
2. **[Runtime Orchestration & Security Auditing](docs/runtime.md)** *(Coming Soon / Create This)* *Zero-copy shared workspace disk-mapping, concurrent background container process initialization, unlearning gates, and running the `mia_audit.py` script.*
3. **[Network Troubleshooting & Diagnostics Matrix](docs/troubleshooting.md)** *(Coming Soon / Create This)* *Resolving MQTT synchronization deadlocks, handling PyTorch multi-key state dictionary dictionary errors, and host interface binding overrides.*
