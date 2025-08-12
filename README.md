# aci-ucsm-intgeration
A project to automate ACI connectivity to/through UCS

This project is still very much a work in progress.  I’m close to a functional solution, but I still need to put it all together.

The files in this Repo:

### aci.py ###
An ACI class object that can be used to interact with an ACI fabric.  Import into a project like this:
```
	from aci import ACI
```
Then instantiate and use the object like this:
```
	sandbox = ACI(“sandbox-aci.rtp.lab”, “myusername”, “MyPassword!”)
	sandbox.get(“uni/tn-demo”)
	sandbox.get(“fvTenant”)
```

### aci_monitor.py ###
A specific ACI class object for creating and using subscriptions.  Import into a project like this:
```
	from aci_monitor import ACI_Monitor
```
Then instantiate and use the object like this:
```
	monitor = ACI_Monitor(“sandbox-aci.rtp.lab”, “myuser”, “MyPwd!”)
	mon.subscribe(“tenant”, “fvTenant”, target=”subtree”)
```

### aci_to_ucsm_vlan_mapping.py ###
A script that will: 
-	connect to an ACI fabric and a UCS domain
-	find the links that connect them
-	read the VLANs from the ACI side of the link
-	create/find a VLAN Group in UCS Manager
-	update the VLAN Group to match the VLANs trunked from ACI

### simulate_change.py ###
This was just a little script created to simulate changes in ACI that could be seen by a monitoring subscription.  It just runs an infinite loop where it posts a small change to a tenant every 15 seconds.

### test_monitor.py ###
This is a demo of the aci_monitor object to prove the aci subscription works.  This makes use of Threading to run a couple of simultaneous processes.

### ucsm.py ###
This is a UCS Manager class object that leverages the UCSM SDK to interact with UCS.  Import into a project like this:
```
	from ucsm import UCSM
```
then instantiate and use the object like this:
```
	ucs3 = UCSM(“rtp-ucsm-03.rtp.lab”, “myusername”, “mypassword!”)
	ucs3.query_classid(“NetworkElement”)
	ucs3.create_vlan_group(“MyVlanGroup”)
```



Some links to useful resources:

Soumitra Mukherji’s guide to ACI Subscriptions in the Unofficial ACI Guide
https://unofficialaciguide.com/2019/09/22/aci-websocket-subscription-for-push-notification/

Documentation on using the REST API with ACI:
https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/apic-rest-api-configuration-guide/cisco-apic-rest-api-configuration-guide-42x-and-later/m_using_the_rest_api.html

UCS Manager object model documentation:
https://developer.cisco.com/docs/ucs-mim/latest/

The UCS Manager SDK GitHub:
https://github.com/CiscoUcs/ucsmsdk


<img width="462" height="642" alt="image" src="https://github.com/user-attachments/assets/507ceef7-d67e-4fe9-9b3a-79691a902a71" />
