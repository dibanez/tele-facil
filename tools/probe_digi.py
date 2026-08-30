#!/usr/bin/env python3
"""Discover a DIGI R2A (or any Android TV) on the LAN and report which control
paths are available: Android TV Remote v2 (preferred) or ADB over network.

Dependency-free: runs with a stock Python 3 on the Raspberry Pi or any laptop
sitting on the same subnet as the set-top box.

Usage:
    python3 probe_digi.py                 # auto-detect subnet, full probe
    python3 probe_digi.py --host 1.2.3.4  # probe a known address only
    python3 probe_digi.py --timeout 10    # longer mDNS wait for slow devices
"""

import argparse
import ipaddress
import socket
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Android TV Remote v2 pairing and command ports.
REMOTE_PORTS = (6466, 6467)
# ADB over TCP, only open when "network debugging" is enabled.
ADB_PORT = 5555
# Chromecast port: any powered-on Google TV keeps this open. Useful as a
# liveness signal even when the remote service is unavailable.
CAST_PORT = 8009

MDNS_GROUP = "224.0.0.251"
MDNS_PORT = 5353
MDNS_SERVICES = (
    "_androidtvremote2._tcp.local",
    "_googlecast._tcp.local",
    "_adb-tls-connect._tcp.local",
    "_adb._tcp.local",
    "_services._dns-sd._udp.local",
)


# --------------------------------------------------------------------------
# mDNS
# --------------------------------------------------------------------------

def _encode_qname(name):
    out = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".") if p)
    return out + b"\x00"


def _build_ptr_query(name):
    header = struct.pack("!6H", 0, 0, 1, 0, 0, 0)
    return header + _encode_qname(name) + struct.pack("!2H", 12, 1)


def _decode_name(data, offset):
    """Decode a DNS name, following compression pointers.

    Returns (name, offset_after_name). When a pointer was followed the returned
    offset is the position after the pointer, not after the target.
    """
    parts = []
    resume = None
    for _ in range(128):
        if offset >= len(data):
            break
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:
            pointer = struct.unpack("!H", data[offset:offset + 2])[0] & 0x3FFF
            if resume is None:
                resume = offset + 2
            offset = pointer
            continue
        offset += 1
        parts.append(data[offset:offset + length].decode("utf-8", "replace"))
        offset += length
    return ".".join(parts), (resume if resume is not None else offset)


def mdns_discover(timeout=6.0):
    """Broadcast PTR queries and collect answers per responding host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(1.0)
    sock.bind(("0.0.0.0", 0))

    for service in MDNS_SERVICES:
        try:
            sock.sendto(_build_ptr_query(service), (MDNS_GROUP, MDNS_PORT))
        except OSError as exc:
            print(f"  ! mDNS send failed for {service}: {exc}", file=sys.stderr)

    found = {}
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(9000)
        except socket.timeout:
            continue
        except OSError:
            break
        names = _parse_records(data)
        if names:
            found.setdefault(addr[0], set()).update(names)
    sock.close()
    return found


def _parse_records(data):
    """Extract PTR targets and SRV hostnames from a DNS response."""
    names = []
    try:
        qd, an, ns, ar = struct.unpack("!4H", data[4:12])
        offset = 12
        for _ in range(qd):
            _, offset = _decode_name(data, offset)
            offset += 4
        for _ in range(an + ns + ar):
            _, offset = _decode_name(data, offset)
            if offset + 10 > len(data):
                break
            rtype, _, _, rdlen = struct.unpack("!HHIH", data[offset:offset + 10])
            offset += 10
            if rtype == 12:  # PTR
                target, _ = _decode_name(data, offset)
                names.append(target)
            elif rtype == 33 and rdlen >= 6:  # SRV
                target, _ = _decode_name(data, offset + 6)
                names.append(target)
            offset += rdlen
    except (struct.error, IndexError):
        pass
    return [n for n in names if n]


# --------------------------------------------------------------------------
# TCP probing
# --------------------------------------------------------------------------

def tcp_open(host, port, timeout=0.6):
    try:
        with socket.create_connection((str(host), port), timeout=timeout):
            return True
    except OSError:
        return False


def local_subnets():
    """Return IPv4 /24 networks from `ip -4 addr`, skipping loopback/docker."""
    nets = []
    try:
        out = subprocess.run(
            ["ip", "-4", "-o", "addr", "show"],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return nets
    for line in out.splitlines():
        fields = line.split()
        if len(fields) < 4:
            continue
        iface, cidr = fields[1], fields[3]
        if iface == "lo" or iface.startswith(("docker", "br-", "veth")):
            continue
        try:
            net = ipaddress.ip_interface(cidr).network
        except ValueError:
            continue
        if net.num_addresses > 1024:
            continue
        if net not in nets:  # two NICs on the same LAN would scan it twice
            nets.append(net)
    return nets


def scan_subnet(network, ports, workers=128):
    """Return {ip: [open_ports]} for hosts with at least one port open."""
    hosts = list(network.hosts())
    results = {}

    def probe(ip):
        return str(ip), [p for p in ports if tcp_open(ip, p)]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for ip, open_ports in pool.map(probe, hosts):
            if open_ports:
                results[ip] = open_ports
    return results


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def classify(open_ports):
    has_remote = any(p in open_ports for p in REMOTE_PORTS)
    has_adb = ADB_PORT in open_ports
    has_cast = CAST_PORT in open_ports
    return has_remote, has_adb, has_cast


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", help="probe only this address")
    parser.add_argument("--timeout", type=float, default=6.0,
                        help="mDNS listen window in seconds (default: 6)")
    parser.add_argument("--no-scan", action="store_true",
                        help="skip the subnet port sweep, use mDNS only")
    args = parser.parse_args()

    ports = list(REMOTE_PORTS) + [ADB_PORT, CAST_PORT]
    candidates = {}

    if args.host:
        print(f"Probing {args.host} ...")
        open_ports = [p for p in ports if tcp_open(args.host, p, timeout=1.5)]
        candidates[args.host] = open_ports
    else:
        print(f"[1/2] mDNS discovery ({args.timeout:.0f}s) ...")
        for ip, services in sorted(mdns_discover(args.timeout).items()):
            interesting = [s for s in services
                           if "androidtvremote" in s or "googlecast" in s or "adb" in s]
            if interesting:
                print(f"      {ip}: {', '.join(sorted(interesting)[:3])}")
                candidates.setdefault(ip, [])
        if not candidates:
            print("      no Android TV / Cast / ADB services announced")

        if not args.no_scan:
            nets = local_subnets()
            print(f"[2/2] Port sweep on {', '.join(str(n) for n in nets) or 'nothing'} ...")
            for net in nets:
                for ip, open_ports in scan_subnet(net, ports).items():
                    candidates[ip] = open_ports
        else:
            print("[2/2] port sweep skipped")

        # Fill in port state for hosts that only showed up via mDNS.
        for ip, open_ports in list(candidates.items()):
            if not open_ports:
                candidates[ip] = [p for p in ports if tcp_open(ip, p, timeout=1.5)]

    print("\n" + "=" * 62)
    print("RESULT")
    print("=" * 62)

    if not candidates:
        print("\nNo Android TV device found on this network.\n")
        print("Check, in order:")
        print("  1. The set-top box is powered on and showing picture.")
        print("  2. It is on the SAME subnet as this machine (not guest WiFi).")
        print("  3. Client isolation / AP isolation is disabled on the router.")
        return 2

    best = None
    for ip, open_ports in sorted(candidates.items()):
        has_remote, has_adb, has_cast = classify(open_ports)
        if not (has_remote or has_adb or has_cast):
            continue
        label = "Android TV Remote" if has_remote else ("ADB" if has_adb else "Cast only")
        print(f"\n  {ip}")
        print(f"    open ports : {', '.join(str(p) for p in sorted(open_ports))}")
        print(f"    remote v2  : {'YES' if has_remote else 'no'}")
        print(f"    adb tcp    : {'YES' if has_adb else 'no'}")
        print(f"    cast alive : {'YES' if has_cast else 'no'}")
        print(f"    -> {label}")
        if best is None or has_remote:
            best = (ip, has_remote, has_adb, has_cast)

    if best is None:
        print("\nHosts responded but none exposes a usable control port.")
        return 2

    ip, has_remote, has_adb, has_cast = best
    print("\n" + "-" * 62)
    if has_remote:
        print(f"RECOMMENDED PATH: Android TV Remote at {ip}")
        print("Home Assistant -> Settings -> Devices & Services -> Add Integration")
        print(f"-> 'Android TV Remote' -> host {ip} -> enter the on-screen code.")
        return 0
    if has_adb:
        print(f"FALLBACK PATH: ADB at {ip}:{ADB_PORT}")
        print("The remote service is not reachable; use the Android Debug Bridge")
        print("integration instead. Note ADB debugging often resets on reboot.")
        return 1
    print(f"Device alive at {ip} but neither control port is open.")
    print("Enable the Android TV Remote service, or turn on network debugging.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
