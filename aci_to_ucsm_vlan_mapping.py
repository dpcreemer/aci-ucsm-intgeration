import aci
import ucsm
from getpass import getpass

ucs_addr = "rtp-ucsm-03.mgmt.rtp.lab"
aci_addr = "sandbox-aci.rtp.lab"

# prompt for credentials
while (not "user" in locals()) or not user: user = input("User: ")
while (not "password" in locals()) or not password: password = getpass("Password: ")

aci_fab = aci.ACI(aci_addr, user, password)
ucsm_dom = ucsm.UCSM(ucs_addr, user, password)

# Find ACI interfaces connecting to the UCS FIs
fi_oob_ip = ucsm_dom.query_classid("NetworkElement")[0].oob_if_ip
aci_fi_interfaces = aci_fab.get_attr("lldpAdjEp", filter=f"eq(lldpAdjEp.mgmtIp, \"{fi_oob_ip}\")", attr="dn")
dn = aci_fi_interfaces[0]
pod = dn[dn.find("/pod-")+5:dn.find("/node")]
node = dn[dn.find("/node-")+6:dn.find("/sys")]
ifc = dn[dn.find("/if-[")+5:dn.find("]/")]
print(f"FI connection found in pod {pod} on leaf {node} interface {ifc}.")

# Collect the VLANs configured on the FI connected interfaces
aci_vlans = aci_fab.interface_vlans(pod, node, ifc)
print(f"VLANs configured on FI facing interface: {aci_vlans}")

# Read the VLAN list from UCS and add ACI VLANs not already configured
ucs_vlans_all = [int(vlan.id) for vlan in ucsm_dom.vlans]
ucs_vlans_needed = [vlan for vlan in aci_vlans if vlan not in ucs_vlans_all]
for vlan in ucs_vlans_needed:
  name = aci_fab.get_attr(f"topology/pod-{pod}/node-{node}/sys", target="subtree", target_class="vlanCktEp", 
                          filter=f"eq(vlanCktEp.encap, \"vlan-{vlan}\")", attr="name")
  print(f"Adding VLAN {vlan} to UCS as \"{name}\".")
  ucsm_dom.create_vlan(f"{aci_fab.name}-aci:{name}", vlan)

# Look for the ACI fabric VLAN Group in UCS.  
# Create the VLAN Group if it doesn't exist
vlan_group = f"{aci_fab.name}-aci"
if vlan_group not in [g.name for g in ucsm_dom.vlan_groups]:
  print(f"Creating VLAN Group \"{vlan_group}\".")
  ucsm_dom.create_vlan_group(vlan_group)

# Identify VLANs in the VLAN Group and correlate with ACI VLANs
# Add VLANs to the VLAN Group as needed
ucs_group_vlans = ucsm_dom.get_vlan_group_vlans(vlan_group)
ucs_group_vlans_needed = [vlan for vlan in aci_vlans if vlan not in ucs_group_vlans]
if ucs_group_vlans_needed:
  print(f"Adding VLANs to VLAN Group \"{vlan_group}\": {ucs_group_vlans_needed}")
  ucsm_dom.add_vlan_to_group(ucs_group_vlans_needed, vlan_group)

# Check the UCS VLAN Group for VLANs that are no longer need for ACI and remove them
ucs_group_vlans_not_needed = [vlan for vlan in ucs_group_vlans if vlan not in aci_vlans]
if ucs_group_vlans_not_needed: 
  print(f"Removing unneeded VLANs from VLAN Group \"{vlan_group}\": {ucs_group_vlans_not_needed}")
  ucsm_dom.remove_vlan_from_group(ucs_group_vlans_not_needed, vlan_group)