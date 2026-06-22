# 🧩 System Prerequisites & Hypervisor Installation

This sheet walks you through installing the core LXC/LXD containerization hypervisor engine onto your Linux host system, adding user group permissions, and running basic subsystem initialization.

> 🐧 **SYSTEM COMPATIBILITY NOTICE:**
> 
> This installation pipeline is optimized and verified for **Debian-based distributions** (including **Ubuntu 22.04/24.04 LTS** and **Kali Linux**).
> 
> If you are utilizing an RPM-based system (Fedora/RHEL) or an Arch-based distribution, your native package manager syntax (`dnf` or `pacman`) and snap path symlinks will differ. It is recommended to use the verified Debian/Kali environment to ensure script repeatability.

---

## 💾 1. Installing the LXD Container Daemon via Snap

Ubuntu and Kali Linux manage up-to-date LXD releases exclusively via the Snap package manager infrastructure.

### Step 1.1: Install the Snap Package Engine (If Missing)

```bash
sudo apt update && sudo apt install -y snapd
```

### Step 1.2: Install the Core LXD Subsystem

Execute the snap distribution download tracking track:

```bash
sudo snap install lxd
```

## 👥 2. Managing System Permissions & Environment Reboots

By default, executing hypervisor infrastructure commands requires structural root privilege access (sudo). To allow seamless non-root pipeline execution:

### Step 2.1: Add Your Active User to the LXD Group Boundary

```bash
sudo usermod -aG lxd $USER
```

### Step 2.2: Apply Group Membership Changes

> 🛑 CRITICAL SYSTEM REBOOT CHECKPOINT:
> 
> For the kernel to completely flush your user session permissions and actively bind your shell to the lxd execution group boundary, you must completely restart your host operating system or manually refresh your login context using:
>> ```newgrp lxd```
>
> If commands throw permissions errors after using newgrp, save your work and reboot your machine.

## 🚀 3. Engine Initialization & Subsystem Validation Testing

Once back from the system refresh, configure the foundational loopback storage values and network parameters.

### Step 3.1: Trigger Automated Core Configuration

Run the automated infrastructure initialization command sequence:

```bash
sudo lxd init --minimal
```

### Step 3.2: Verify Binary Path Map Execution

Test that the client binary successfully queries the back-end system socket wrapper by listing instances:

```bash
lxc list
```

> 📌 **Binary Path Resolution Warning:**
> 
> If your system terminal outputs bash: lxc: command not found but the snap install succeeded, your system shell is missing the global snap path mapping inside its .bashrc or .zshrc configuration profiles.
> 
> To bypass this without modifying system scripts, swap out the raw lxc command keyword and explicitly reference its direct path binary signature: **`/snap/bin/lxc`** for all future commands across the sheets.
>> Example: `/snap/bin/lxc list` instead of `lxc list`

---

### ➡️ Next Step

Now that the core hypervisor engine is successfully processing terminal commands on your host, proceed to mapping out your isolated project directories:

### 📑 [Proceed to Cluster Infrastructure Setup (docs/infrastructure.md)](infrastructure.md)