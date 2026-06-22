# 🩺 Network Troubleshooting & Diagnostics Matrix

If the cluster system stalls, disconnects, or displays exceptions, follow this standard network troubleshooting blueprint:

---

## 🚨 CASE A: Containers Lack WAN/Internet Access (Missing Host NAT Masquerading)

* **Root Cause:** The host operating system's kernel has packet forwarding disabled, or the iptables firewall rules are not configured to perform Network Address Translation (NAT) for the container bridge subnet (10.111.79.0/24). This prevents the containers from hitting the external internet to pull down updates or Python dependencies.
* **Resolution:** Enable IPv4 packet forwarding in the host kernel and append a masquerade target rule to your routing tables, **on the host machine, not inside any of the containers** :

```bash
# 1. Enable packet forwarding at the kernel level
sudo sysctl -w net.ipv4.ip_forward=1

# 2. Configure iptables to perform NAT masquerading for your cluster's subnet
# Replace 'eth0' or 'wlan0' with your host machine's actual primary internet-connected interface
sudo iptables -t nat -A POSTROUTING -s 10.111.79.0/24 -o wlan0 -j MASQUERADE

# 3. Force the firewall to instantly permit transit traffic entering and leaving the cluster bridge
sudo iptables -I FORWARD -i lxdbr0 -j ACCEPT
sudo iptables -I FORWARD -o lxdbr0 -j ACCEPT
```

> 📌 **Persistent Configuration Tip:**
> 
> Kernel changes made via sysctl -w disappear on reboot. To make this change permanent on your host,
open /etc/sysctl.conf and uncomment or add the following line:
>> net.ipv4.ip_forward=1

---

## CASE B:. Containers Freeze Indefinitely at Launch (Synchronization Deadlock)

**Root Cause:** Container threads fire their initial "client/ready" payload over MQTT before the central host server script has finished initializing its network listening context or subscribing to the network topics.

Resolution: Terminate all dangling background runtime components and respect the exact timing delay (sleep 1.5) in the launch script:

```bash
# Clear zombie processes on host and inside container runtimes
pkill -f serverSDG.py
for i in {1..4}; do lxc exec iot-device-$i -- pkill -f python3; done
```

---

## CASE C: PyTorch Exception: `RuntimeError: Error(s) in loading state_dict... Unexpected key(s) "weights"`
* **Root Cause:** A container node is erroneously executing the boilerplate template `clientSDG.py` instead of the audited script `clientSDG_0.py`. The base template expects unmapped weight arrays, whereas the central aggregator transmits custom key-value pairs (`{"weights": ..., "is_final_test": ...}`).
* **Resolution:** Ensure that **all 4 active containers** are executing the updated `clientSDG_0.py` routine which includes the reverse structural decoder.

---

## CASE D: Container Connection Timeouts to Host MQTT Broker (`Connection Refused`)
* **Root Cause:** By default, security rules on local Linux Mosquitto installations block remote or external container bridge traffic, restricting loopback messaging strictly to `localhost (127.0.0.1)`.
* **Resolution:** Open the configuration file on the host operating system:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Append these overriding interface bindings to the very bottom:

```bash
listener 1883 0.0.0.0
allow_anonymous true
```

Save and reload the service matrix:

```bash
sudo systemctl restart mosquitto
```

---

## CASE E: LXD Virtual Bridge Routing Failures (IP Hangs / Routing Loss)

* **Root Cause:** After forcefully terminating (pkill) multiple training runs, the host kernel's virtual network switch (lxdbr0) can get hung or leak network state. The containers remain active but lose their IP bindings or fail to route payloads across the bridge interface.
* **Resolution:** Reset the core containerization hypervisor subsystem on your host machine to completely flush and rebuild the virtual routing tables:

```bash
sudo systemctl restart snap.lxd.daemon
```

## CASE F: Binary Call Failures (`bash: lxc: command not found`)

* **Root Cause:** The host operating system's shell lookup table has not linked the `/snap/bin/` directory map path to your active environmental `$PATH` parameters. The software engine is completely alive, but the terminal cannot resolve the raw shorthand `lxc` shortcut target.
* **Resolution:** Swap the short target string execution syntax out for the explicit, absolute hardcoded snap directory layout binary prefix across all automation script configurations:

```bash
# Fallback testing rule if raw 'lxc' command drops out:
/snap/bin/lxc list

# Subsystem config modification example:
/snap/bin/lxc project switch PFA-FU-Project
```

> 💡 **Automation Tip:** 
> 
> If you are building automated shell loops, you can quickly alias the command by running `alias lxc='/snap/bin/lxc'` inside your active terminal session to restore the standard short notation instantly.
