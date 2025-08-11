import datetime
from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan
from ucsmsdk.mometa.fabric.FabricNetGroup import FabricNetGroup
from ucsmsdk.mometa.fabric.FabricPooledVlan import FabricPooledVlan

log_file_root = "pyUCSM"

class UCSM(object):
  def __init__(self, address, user, password):
    self.__address = address
    self.__handle = UcsHandle(address, user, password)
    self.debug_level = 0
    if not self.login():
      raise Exception("Authentication failed")
  
  @property
  def handle(self):
    return self.__handle
  
  @property
  def address(self):
    return self.__address
  
  @property
  def logfile(self):
    return f"{log_file_root}-[{datetime.datetime.now().strftime("%Y-%m-%d")}].log"
  
  @property
  def vlans(self):
    return self.query_classid("fabricVlan")
  
  @property
  def vlan_groups(self):
    return self.query_classid("fabricNetGroup")
  
  def notate(self, note):
    if self.debug_level >= 1:
      with open(self.logfile, "w+") as f:
        f.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%:D')}]")
        f.write(note)
    if self.debug_level >= 2:
      print(note)
  
  def login(self):
    auth_status = self.handle.login()
    self.notate(f"Authentication {"successful" if auth_status else "failed"}")
    return auth_status
  
  def add_mo(self, mo):
    self.notate(f"Object {mo.name} of type {mo.get_class_id()} added")
    self.handle.add_mo(mo)

  def remove_mo(self, mo):
    self.notate(f"Object {mo.name} of type {mo.get_class_id()} removed")
    self.handle.remove_mo(mo)
  
  def commit(self):
    self.notate("Commiting changes")
    self.handle.commit()

  def query_classid(self, class_name, filter=""):
    return self.handle.query_classid(class_name, filter_str=filter)
  
  def query_dn(self, dn):
    return self.handle.query_dn(dn)
  
  def query_children(self, mo, class_id=""):
    return self.handle.query_children(mo, class_id=class_id)
  
  def vlan_mo(self, vlan):
    if type(vlan) is int or vlan.isnumeric():
      vlan_objects = self.query_classid("fabricVlan", filter=f"(id, \"{vlan}\", type=\"eq\")")
      if len(vlan_objects) < 1:
        raise Exception(f"VLAN {vlan} was not found in this domain.")
      if len(vlan_objects) > 1:
        raise Exception(f"Multiple VLANs matched that query {vlan}.  Please try again using the VLAN Name.")
      return vlan_objects[0]
    vlan_objects = self.query_dn(f"fabric/lan/net-{vlan}")
    if not vlan_objects:
      raise Exception(f"VLAN {vlan} not found.")
    return vlan_objects

  def create_vlan(self, vlan_name, vlan_id):
    vlan = FabricVlan(parent_mo_or_dn="fabric/lan", name=vlan_name, id=str(vlan_id))
    self.add_mo(vlan)
    self.commit()

  def delete_vlan(self, vlan):
    vlan_mo = self.vlan_mo(vlan)
    self.remove_mo(vlan_mo)
    self.commit()

  def create_vlan_group(self, vlan_group):
    vlan_group_mo = FabricNetGroup(parent_mo_or_dn="fabric/lan", name=vlan_group)
    self.add_mo(vlan_group_mo)
    self.commit()

  def delete_vlan_group(self, vlan_group):
    vlan_group_mo = self.query_dn("fabric/lan/net-group-" + vlan_group)
    self.remove_mo(vlan_group_mo)
    self.commit()

  def add_vlan_to_group(self, vlans, group):
    vlan_group_mo = self.query_dn("fabric/lan/net-group-" + group)
    if not type(vlans) is list:
      vlans = [vlans]
    for vlan in vlans:
      if type(vlan) is FabricVlan:
        vlan_mo = vlan
      elif type(vlan) is int or vlan.isnumeric():
        vlan_mo = self.query_classid("fabricVlan", filter = f"(id, \"{vlan}\", type=\"eq\")")[0]
      else:
        vlan_mo = self.query_dn("fabric/lan/net-" + vlan)
      fpv = FabricPooledVlan(parent_mo_or_dn = vlan_group_mo, name = vlan_mo.name)
      self.add_mo(fpv)
    self.commit()

  def remove_vlan_from_group(self, vlans, group):
    vlan_group_mo = self.query_dn("fabric/lan/net-group-" + group)
    if not vlan_group_mo: raise Exception(f"VLAN Group \"group\" not found.")
    if not type(vlans) is list:
      vlans = [vlans]
    for vlan in vlans:
      if type(vlan) is int or vlan.isnumeric():
        vlan_mo = self.query_classid("fabricVlan", filter = f"(id, \"{vlan}\", type=\"eq\")")[0]
      else:
        vlan_mo = self.query_dn("fabric/lan/net-" + vlan)
      fpv = self.query_dn(f"{vlan_group_mo.dn}/net-{vlan_mo.name}")
      self.remove_mo(fpv)
    self.commit()

  def get_vlan_group_vlans(self, vg_name):
    vg = self.query_dn("fabric/lan/net-group-" + vg_name)
    group_members = self.query_children(vg, class_id="fabricPooledVlan")
    vlan_list = self.query_classid("fabricVlan")
    vlan_dict = {vlan.name: vlan.id for vlan in vlan_list}
    vlans = [int(vlan_dict[vlan.name]) for vlan in group_members]
    vlans.sort()
    return vlans