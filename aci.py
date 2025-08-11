import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime

MAX_RESPONSES = 5

def mixed_range_string_to_int_list(range_str):
  l = []
  for r in range_str.split(','):
    l.extend(range(int(r.split('-')[0]), int(r.split('-')[-1])+1))
  return l

class ACI(object):
  def __init__(self, apic, user="", password=""):
    self.debug = False
    self.apic = apic
    self.responses = []
    self.__session_id = None
    self.__session_expiration = None
    self.__token = ""
    self.__session = requests.Session()
    self.session.verify = False
    self.__authenticated = self.auth(user, password)
    if not self.authenticated: raise Exception("Authentication failed")
    
  @property
  def token(self):
    return self.__token
  
  @property
  def cookies(self):
    return {"APIC-cookie": self.token}
  
  @property
  def authenticated(self):
    return self.__authenticated

  @property
  def name(self):
    return self.get_attr("fabricTopology", attr="fabricDomain")
  
  @property
  def base_url(self):
    return f"https://{self.apic}/api/"

  @property
  def session(self):
    return self.__session
  
  @property
  def session_id(self):
    return self.__session_id
  
  @property
  def session_expiration(self):
    return self.__session_expiration

  @property
  def session_time_left(self):
    return self.session_expiration - datetime.now().astimezone()
  
  @property
  def response(self):
    if len(self.responses) == 0: 
      return None
    return self.responses[-1]
  
  @response.setter
  def response(self, rsp):
    self.responses.append(rsp)
    while len(self.responses) > MAX_RESPONSES: 
      self.responses.pop(0)
  
  def auth(self, user, password):
    url = f"{self.base_url}aaaLogin.json"
    payload = {"aaaUser": {"attributes": {"name": user, "pwd": password}}}
    self.post(url, payload)
    if self.response.ok: 
      self.__token = self.response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
      sess_id = self.response.json()["imdata"][0]["aaaLogin"]["attributes"]["sessionId"]
      self.__session_id = sess_id.replace("/", "_")
      self.update_session_expiration()
    return self.response.ok
  
  def update_session_expiration(self):
    sess_data = self.get(f"uni/usersessext/actsession-{self.session_id}")["imdata"][0]
    ts = sess_data["aaaActiveUserSession"]["attributes"]["expiryTime"]
    self.__session_expiration = datetime.strptime(ts[:ts.find('.')] + ts[-6:], "%Y-%m-%dT%H:%M:%S%z")
  
  def refresh_session(self):
    self.post(f"{self.base_url}aaaRefresh.json", {})
    self.update_session_expiration()

  def get(self, path, target="", target_class="", filter=""):
    params = {}
    if path[:4].lower() != "http":
      if path.find("/") > 0 or path[:3].lower() == "uni":
        path = f"{self.base_url}mo/{path}"
      else:
        path = f"{self.base_url}class/{path}"
    if path[-5:].lower() != ".json":
      path = path + ".json"
    if target: 
      params["query-target"] = target
    if filter:
      params["query-target-filter"] = filter
    if target_class:
      params["target-subtree-class"] = target_class
    self.response = self.session.get(path, params=params)
    return self.response.json()
  
  def get_attr(self, path, attr, target="", target_class="", filter=""):
    data = self.get(path, target, target_class, filter)
    obj_key = list(data['imdata'][0].keys())[0]
    attr_list = [entry[obj_key]["attributes"][attr] for entry in data['imdata']]
    if len(attr_list) == 1: 
      return attr_list[0]
    return attr_list
  
  def post(self, path, payload="nothing"):
    if payload == "nothing":
      payload = path
      path = f"{self.base_url}mo.json"
    if path[:4].lower() != "http":
      path = f"{self.base_url}mo/{path}"
    if path[-5:].lower() != ".json":
      path = path + ".json"
    if type(payload) is dict:
      self.response = self.session.post(path, json=payload)
    else:
      self.response = self.session.post(path, data=payload)

  def interface_vlans(self, pod, node, ifc):
    oper_vlans = self.get_attr(f"topology/pod-{pod}/node-{node}/sys/phys-[{ifc}]/phys", attr="operVlans")
    if not oper_vlans: return []
    oper_vlans = mixed_range_string_to_int_list(oper_vlans)
    vlan_data = self.get(f"topology/pod-{pod}/node-{node}/sys", target="subtree", target_class="vlanCktEp")["imdata"]
    vlan_trans = {i["vlanCktEp"]["attributes"]["id"]: i["vlanCktEp"]["attributes"]["encap"].replace("vlan-", "") for i in vlan_data}
    vlans = [int(vlan_trans[str(v)]) for v in oper_vlans if str(v) in vlan_trans.keys()]
    vlans.sort()
    return vlans
