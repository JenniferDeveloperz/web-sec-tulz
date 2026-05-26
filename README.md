# Cross-Platform MAC Address Changer

A Python-based tool to change the MAC address of a network interface across multiple operating systems, including **Linux, macOS, Windows, and BSD**.

---

## Features

- Cross-platform support (Linux, Windows, macOS, BSD)
- Random MAC address generation (locally administered)
- Network interface listing
- Input validation for MAC addresses
- Admin/root privilege detection
- Simple and clean CLI interface

---

## ‼️ Disclaimer‼️

This tool is intended for **educational purposes** and use in **authorized environments only**.

Changing MAC addresses may violate network policies or local regulations if used improperly.  
The user is responsible for ensuring compliance with applicable laws and organizational policies.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/JenniferDeveloperz/chmac.git
cd chmac

## HOW TO RUN?

Make sure you have Python 3 installed:

```bash
python3 --version

List available network interfaces:

```bash
python3 mac_changer.py --list

Change MAC address (random)

Linux / macOS:

```bash
sudo python3 mac_changer.py -i eth0 -r

Windows (PowerShell / CMD):

```bash PowerShell
python mac_changer.py -i "Wi-Fi" -r

Set specific MAC address:

Linux / macOS:

```bash
sudo python3 mac_changer.py -i eth0 -m AA:BB:CC:DD:EE:FF

Windows:

```bash
python mac_changer.py -i "Wi-Fi" -m AA:BB:CC:DD:EE:FF
