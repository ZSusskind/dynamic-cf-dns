#!/usr/bin/env python3
# Slightly hacky script for pointing Cloudflare to a dynamic IP
# Run as a cron job

import os
import sys
import time
from requests import get
from psutil import boot_time
import CloudFlare

email = "[REDACTED]@gmail.com"
api_key = "[REDACTED]"

log_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "update_dns.log")
last_ip_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "last_ip_address")

def timestamp():
    return f"[{time.ctime()}]"

clobber_log_file = False
if not (os.path.exists(log_fname)):
    clobber_log_file = True
else:
    last_boot = boot_time()
    last_log_update = os.stat(log_fname).st_mtime
    if last_log_update < last_boot:
        clobber_log_file = True

if not clobber_log_file:
    log_f = open(log_fname, "a")
else:
    log_f = open(log_fname, "w")
sys.stdout = log_f
sys.stderr = log_f

try:
    ip = get("https://api64.ipify.org").text
    ip4 = get("https://api.ipify.org").text
except:
    print("Failed to get external IP address")
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    log_f.close()
    sys.exit()

changed = False
if not (os.path.exists(last_ip_fname)):
    print(timestamp(), f"File {last_ip_fname} not found; will update DNS and create")
    changed = True
else:
    with open(last_ip_fname, "r") as last_ip_f:
        last_ip = last_ip_f.read().strip()
    if ip != last_ip:
        print(timestamp(), f"IP address has changed from {last_ip} to {ip}; will update DNS")
        changed = True

if changed:
    print(timestamp(), "  Updating DNS records...")
    try:
        found_record = False
        cf = CloudFlare.CloudFlare(email=email, token=api_key)
        zones = cf.zones.get()
        if len(zones) == 0:
            raise RuntimeError("No zones returned from API request")
        for zone in zones:
            zone_id = zone["id"]
            records = cf.zones.dns_records.get(zone_id)
            if len(records) == 0:
                raise RuntimeError(f"Zone {zone['name']} has no associated regions")
            for record in records:
                if record["type"] == "AAAA":
                    print(timestamp(), "  Updating IPv6 record")
                    record_id = record["id"]
                    new_data = {"name": record["name"], "type": "AAAA", "content": ip, "proxied": record["proxied"]}
                    cf.zones.dns_records.put(zone_id, record_id, data=new_data)
                    found_record = True
                elif record["type"] == "A":
                    print(timestamp(), "  Updating IPv4 record")
                    record_id = record["id"]
                    new_data = {"name": record["name"], "type": "A", "content": ip4, "proxied": record["proxied"]}
                    cf.zones.dns_records.put(zone_id, record_id, data=new_data)
        if not found_record:
            raise RuntimeError("Didn't find AAAA record")
    except Exception as ex:
        if type(ex) == CloudFlare.exceptions.CloudFlareAPIError and str(ex) == "Record already exists.":
            print(timestamp(), "Cloudflare reports it already has the updated record. This probably shouldn't have happened, but we're just going to roll with it.")
        else: 
            print(timestamp(), "Something went wrong, DNS records not updated")
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            log_f.close()
            sys.exit()

    with open(last_ip_fname, "w") as last_ip_f:
        last_ip_f.write(ip)
    print(timestamp(), "DNS records updated")
else:
    print(timestamp(), "IP address unchanged")

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
log_f.close()

