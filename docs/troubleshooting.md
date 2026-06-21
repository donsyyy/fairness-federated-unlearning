🩺 Network Troubleshooting & Diagnostics Matrix

If the cluster system stalls, disconnects, or displays exceptions, follow this standard network troubleshooting blueprint:
1. Containers Freeze Indefinitely at Launch (Synchronization Deadlock)

    Root Cause: Container threads fire their initial "client/ready" payload over MQTT before the central host server script has finished initializing its network listening context or subscribing to the network topics.

    Resolution: Terminate all dangling background runtime components and respect the exact timing delay (sleep 1.5) in the launch script:
    Bash

    # Clear zombie processes on host and inside container runtimes
    pkill -f serverSDG.py
    for i in {1..4}; do lxc exec iot-device-$i -- pkill -f python3; done


### 2. PyTorch Exception: `RuntimeError: Error(s) in loading state_dict... Unexpected key(s) "weights"`
* **Root Cause:** A container node is erroneously executing the boilerplate template `clientSDG.py` instead of the audited script `clientSDG_0.py`. The base template expects unmapped weight arrays, whereas the central aggregator transmits custom key-value pairs (`{"weights": ..., "is_final_test": ...}`).
* **Resolution:** Ensure that **all 4 active containers** are executing the updated `clientSDG_0.py` routine which includes the reverse structural decoder.

### 3. Container Connection Timeouts to Host MQTT Broker (`Connection Refused`)
* **Root Cause:** By default, security rules on local Linux Mosquitto installations block remote or external container bridge traffic, restricting loopback messaging strictly to `localhost (127.0.0.1)`.
* **Resolution:** Open the configuration file on the host operating system:
  ```bash
  sudo nano /etc/mosquitto/mosquitto.conf

Append these overriding interface bindings to the very bottom:
Plaintext

listener 1883 0.0.0.0
allow_anonymous true

Save and reload the service matrix:
Bash

sudo systemctl restart mosquitto