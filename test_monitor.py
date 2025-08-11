from aci_monitor import ACI_Monitor
import threading
from getpass import getpass

apic="sandbox-aci.rtp.lab"

while (not "apic" in locals()) or not apic: apic = input("APIC Address: ")
while (not "user" in locals()) or not user: user = input("User: ")
while (not "password" in locals()) or not password: password = getpass("Password: ")

mon = ACI_Monitor(apic, user, password)
print("Setting up subscriptions")
mon.subscribe("tenant", "fvTenant", target="subtree")
mon.subscribe("dynamicIfConn", "fvIfConn", filter="wcard(fvIfConn.dn, \"\[UCS-03\]\")")
mon.subscribe("login", "aaaActiveUserSession", filter="wcard(aaaActiveUserSession.status, \"created\")")
mon.subscribe("logout", "aaaActiveUserSession", filter="wcard(aaaActiveUserSession.status, \"deleted\")")

print("Monitoring subscriptions")
th1 = threading.Thread(target=mon.monitor_threads)
th2 = threading.Thread(target=mon.maintain_subscriptions)
th1.start()
th2.start()