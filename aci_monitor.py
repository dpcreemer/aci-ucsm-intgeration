import requests
requests.packages.urllib3.disable_warnings()
import ssl
import websocket
import time
from datetime import datetime, timedelta
from getpass import getpass
import json

class ACI_Monitor(object):
  def __init__(self, apic, user="", password=""):
    self.debug = False
    self.apic = apic
    self.keep_monitoring = True
    self.subscription_timeout = 60
    self.__session_id = None
    self.__session_expiration = None
    self.__token = ""
    self.__web_socket = None
    self.__subscriptions = {}
    self.__session = requests.Session()
    self.session.verify = False
    self.__authenticated = self.auth(user, password)
    if not self.authenticated: raise Exception("Authentication failed")
    self.create_wsocket()

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
  def web_socket(self):
    return self.__web_socket

  @property
  def subscriptions(self):
    return self.__subscriptions
  
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
  
  def auth(self, user, password):
    url = f"{self.base_url}aaaLogin.json"
    payload = {"aaaUser": {"attributes": {"name": user, "pwd": password}}}
    login_response = self.session.post(url, json=payload, verify=False)
    if login_response.ok: 
      self.__token = login_response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
      self.__session_id = login_response.json()["imdata"][0]["aaaLogin"]["attributes"]["sessionId"].replace("/", "_")
      time.sleep(2)
      self.update_session_expiration()
    return login_response.ok
  
  def update_session_expiration(self):
    url = f"{self.base_url}mo/uni/usersessext/actsession-{self.session_id}.json"
    sess_data = self.session.get(url).json()['imdata'][0]
    ts = sess_data['aaaActiveUserSession']['attributes']['expiryTime']
    self.__session_expiration = datetime.strptime(ts[:ts.find('.')] + ts[-6:], '%Y-%m-%dT%H:%M:%S%z')
  
  def refresh_session(self):
    self.session.post(f"{self.base_url}aaaRefresh.json")
    self.update_session_expiration()
  
  def create_wsocket(self):
    url = f"wss://{self.apic}/socket{self.token}"
    self.__web_socket = websocket.create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})

  def subscribe(self, name, object, target="self", filter=""):
    url = f"{self.base_url}class/{object}.json"
    url += "?subscription=yes"
    url += f"&refresh-timeout={self.subscription_timeout}"
    url += f"&query-target={target}"
    if filter:
      url += f"&query-target-filter={filter}"
    response = self.session.get(url, verify=False)
    if self.debug: print(json.dumps(response.json(), indent=2))
    self.__subscriptions[name] = response.json()["subscriptionId"]
  
  def refresh_subscription(self, subscription_id):
    url = f"{self.base_url}subscriptionRefresh.json?id={subscription_id}"
    response = self.session.get(url, verify=False)
    if self.debug: print(url + "\n" + json.dumps(response.json(), indent=2))

  def refresh_all_subscriptions(self):
    for key in self.subscriptions.keys():
      self.refresh_subscription(self.subscriptions[key])

  def subscription_name(self, subscription_id):
    return {self.subscriptions[key]: key for key in self.subscriptions.keys()}[subscription_id]

  def printWSData(self):
    try: 
      data = json.loads(self.web_socket.recv())
      print(f"### {self.subscription_name(data["subscriptionId"][0])} ###")
      print(json.dumps(data, indent=2)) 
    except Exception as e:
      print("#" * 32)
      print(f"An unexpected error occurred: {e}")
      print("#" * 32)

  def monitor_threads(self):
    start = time.clock_gettime(time.CLOCK_REALTIME)
    while self.keep_monitoring:
      if self.debug: print(f"Before: {int(time.clock_gettime(time.CLOCK_REALTIME) - start)} s") 
      self.printWSData()
      if self.debug: print(f"After: {int(time.clock_gettime(time.CLOCK_REALTIME) - start)} s") 
  
  def maintain_subscriptions(self):
    while self.keep_monitoring:
      time.sleep(self.subscription_timeout/2)
      if self.debug:
        msg = "refreshing subscriptions"
        print("*" * (24 + len(msg)))
        print("*" * 10 + "  " + msg + "  " + ("*" * 10))
        print("*" * (24 + len(msg)))
      self.refresh_all_subscriptions()
      if self.session_expiration - datetime.now().astimezone() < timedelta(seconds=90):
        if self.debug: print("Refreshing Session")
        self.refresh_session()