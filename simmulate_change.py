from aci import ACI
import datetime
import time
import sys
from getpass import getpass

apic = "sandbox-aci.rtp.lab"
interval = 15
if len(sys.argv) > 1: interval=int(sys.argv[1])
print(f"Interval: {interval}")

while (not "apic" in locals()) or not apic: apic = input("APIC Address: ")
while (not "user" in locals()) or not user: user = input("User: ")
while (not "password" in locals()) or not password: password = getpass("Password: ")

aci = ACI(apic, user, password)
if not aci.authenticated: raise Exception("Authentication failed")
auth_time = datetime.datetime.now()

while True:
  ts = datetime.datetime.now().strftime("%H:%M:%S")
  print(f"{ts} Updating...")
  payload = {
    "fvTenant": {
      "attributes":{
        "descr":f"Davis playground - {ts}",
        "dn":"uni/tn-davis"
      }
    }
  }
  url = f"https://{apic}/api/mo/uni.json"
  aci.post(url, payload=payload)
  if aci.session_time_left < datetime.timedelta(minutes=3):
    print("Refreshing Auth")
    aci.refresh_session()
    auth_time = datetime.datetime.now()
  time.sleep(interval)

