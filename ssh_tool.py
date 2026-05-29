#!/usr/bin/env python3
"""SSH tool for Alpine Linux device management at 192.168.42.1"""
import paramiko
import sys
import time

HOST = "192.168.42.1"
USER = "root"
PASS = "root"
PORT = 22

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
    return client

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return out, err

def push_pubkey(client, pubkey_path="C:/Users/Administrator/.ssh/id_ed25519.pub"):
    with open(pubkey_path) as f:
        pubkey = f.read().strip()
    cmds = [
        "mkdir -p /root/.ssh && chmod 700 /root/.ssh",
        f"echo '{pubkey}' >> /root/.ssh/authorized_keys",
        "chmod 600 /root/.ssh/authorized_keys",
        "sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys",
    ]
    for cmd in cmds:
        out, err = run(client, cmd)
        if err:
            print(f"  WARN: {err.strip()}")
    print("[+] Public key pushed to device")

def gather_info(client):
    sections = {
        "System": "uname -a && cat /etc/alpine-release",
        "Disk": "df -h",
        "Memory": "free -m",
        "Boot partition": "ls -lh /boot",
        "Network": "ip addr show && ip route",
        "Services": "rc-status",
        "Packages count": "apk list --installed 2>/dev/null | wc -l",
        "Top processes": "ps aux | head -20",
        "Kernel modules": "lsmod | head -20",
        "USB gadget": "cat /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null || echo 'not configured'",
        "Dmesg errors": "dmesg | grep -iE 'error|fail|warn' | tail -20",
    }
    results = {}
    for name, cmd in sections.items():
        out, err = run(client, cmd)
        results[name] = out.strip()
        print(f"\n=== {name} ===")
        print(out.strip() or "(empty)")
        if err.strip():
            print(f"  [stderr]: {err.strip()}")
    return results

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "info"
    print(f"[*] Connecting to {USER}@{HOST}...")
    client = get_client()
    print("[+] Connected!")

    if action == "pushkey":
        push_pubkey(client)
    elif action == "info":
        gather_info(client)
    elif action == "cmd":
        cmd = " ".join(sys.argv[2:])
        out, err = run(client, cmd)
        print(out)
        if err:
            print("[stderr]:", err)
    else:
        print(f"Unknown action: {action}")

    client.close()
