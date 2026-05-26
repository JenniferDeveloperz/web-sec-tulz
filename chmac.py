#!/usr/bin/env python3
"""Change network interface MAC address (Linux, macOS, Windows, BSD)."""

import argparse
import os
import platform
import random
import re
import shutil
import subprocess
import sys

MAC_RE = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
)


def is_admin() -> bool:
    if platform.system() == "Windows":
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0


def normalize_mac(mac: str) -> str:
    mac = mac.strip().lower().replace("-", ":")
    if not MAC_RE.match(mac):
        raise ValueError(f"Invalid MAC address: {mac}")
    return mac


def random_mac() -> str:
    """Locally administered, unicast MAC (second nibble = 2, 6, A, or E)."""
    first = random.randint(0x00, 0xFE) & 0xFE | 0x02
    rest = [random.randint(0x00, 0xFF) for _ in range(5)]
    parts = [f"{first:02x}"] + [f"{b:02x}" for b in rest]
    return ":".join(parts)


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
    )


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required tool not found: {name}")
    return path


# --- Linux / BSD ---

def change_mac_linux(interface: str, mac: str) -> None:
    if shutil.which("ip"):
        run(["ip", "link", "set", interface, "down"])
        run(["ip", "link", "set", interface, "address", mac])
        run(["ip", "link", "set", interface, "up"])
    elif shutil.which("ifconfig"):
        run(["ifconfig", interface, "down"])
        run(["ifconfig", interface, "hw", "ether", mac])
        run(["ifconfig", interface, "up"])
    else:
        raise RuntimeError("Neither 'ip' nor 'ifconfig' found")


def change_mac_bsd(interface: str, mac: str) -> None:
    _require_tool("ifconfig")
    run(["ifconfig", interface, "down"])
    ether_flag = "ether" if platform.system() == "Darwin" else "lladdr"
    run(["ifconfig", interface, ether_flag, mac])
    run(["ifconfig", interface, "up"])


def list_interfaces_unix() -> list[str]:
    if shutil.which("ip"):
        out = run(["ip", "-o", "link", "show"], check=True).stdout
        return [
            line.split(":", 2)[1].strip()
            for line in out.splitlines()
            if ": " in line
        ]
    if shutil.which("ifconfig"):
        out = run(["ifconfig", "-a"], check=True).stdout
        names = []
        for line in out.splitlines():
            if line and not line.startswith((" ", "\t")):
                name = line.split(":")[0].strip()
                if name:
                    names.append(name)
        return names
    return []


# --- Windows ---

def change_mac_windows(interface: str, mac: str) -> None:
    mac_plain = mac.replace(":", "").replace("-", "")
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        raise RuntimeError("PowerShell not found")

    script = (
        f'$a = Get-NetAdapter -Name "{interface}" -ErrorAction Stop; '
        f'Set-NetAdapter -InputObject $a -MacAddress "{mac_plain}" -Confirm:$false'
    )
    result = subprocess.run(
        [ps, "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "Set-NetAdapter failed"
        )


def list_interfaces_windows() -> list[str]:
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return []
    script = "Get-NetAdapter | Where-Object Status -ne 'Not Present' | Select-Object -ExpandProperty Name"
    out = subprocess.run(
        [ps, "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return []
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def change_mac(interface: str, new_mac: str) -> None:
    mac = normalize_mac(new_mac)
    system = platform.system()

    print(f"[+] Changing MAC for {interface} -> {mac} ({system})")

    if system == "Linux":
        change_mac_linux(interface, mac)
    elif system == "Darwin":
        change_mac_bsd(interface, mac)
    elif system == "Windows":
        change_mac_windows(interface, mac)
    elif system in ("FreeBSD", "OpenBSD", "NetBSD", "DragonFly"):
        change_mac_bsd(interface, mac)
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    print("[+] Done")


def list_interfaces() -> None:
    system = platform.system()
    if system == "Windows":
        names = list_interfaces_windows()
    else:
        names = list_interfaces_unix()

    if not names:
        print("[-] Could not list interfaces (missing tools or no permissions)")
        sys.exit(1)

    print("[*] Network interfaces:")
    for name in names:
        print(f"    {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Change MAC address of a network interface (cross-platform)",
    )
    parser.add_argument(
        "-i", "--interface",
        help="Interface name (e.g. eth0, wlan0, en0, 'Wi-Fi')",
    )
    parser.add_argument(
        "-m", "--mac",
        help="New MAC (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)",
    )
    parser.add_argument(
        "-r", "--random",
        action="store_true",
        help="Generate a random locally-administered MAC",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available interfaces and exit",
    )
    args = parser.parse_args()

    if args.list:
        return args

    if not args.interface:
        parser.error("Specify interface (-i / --interface)")
    if not args.mac and not args.random:
        parser.error("Specify MAC (-m / --mac) or use --random")

    return args


def main() -> None:
    args = parse_args()

    if args.list:
        list_interfaces()
        return

    if not is_admin():
        print("[-] Root/Administrator privileges required")
        sys.exit(1)

    new_mac = random_mac() if args.random else args.mac

    try:
        change_mac(args.interface, new_mac)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        err = e.stderr.strip() if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        print(f"[-] {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
