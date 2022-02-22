from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json, time    

driver = webdriver.Firefox()
url = driver.command_executor._url 
driver.implicitly_wait(120)
#  driver.get("https://piano-genie-magenta.glitch.me/")
#  if driver.find_element_by_class_name('splash-main'):
#      pass
#  driver.find_element_by_id('playBtn').click()

url = driver.command_executor._url
session_id = driver.session_id   

driver = webdriver.Remote(command_executor=url,desired_capabilities={})
driver.session_id = session_id

driver.get("https://piano-genie-magenta.glitch.me/")

action_key_down_w = ActionChains(driver).key_down("a")
action_key_up_w = ActionChains(driver).key_up("a")

endtime = time.time() + 1.0

while True:
  action_key_down_w.perform()

  if time.time() > endtime:
    action_key_up_w.perform()
    break

#  delay = 20 # seconds
#  try:
#      myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'playBtn')))
#      print("Page is ready!")
#      driver.find_element_by_id("playBtn").click()
#  except TimeoutException:
#      print("Loading took too much time!")


#  def dispatchKeyEvent(driver, name, options = {}):
#    options["type"] = name
#    body = json.dumps({'cmd': 'Input.dispatchKeyEvent', 'params': options})
#    resource = "/session/%s/chromium/send_command" % driver.session_id
#    url = driver.command_executor._url + resource
#    driver.command_executor._request('POST', url, body)
#  
#  def holdKeyW(driver, duration):
#    endtime = time.time() + duration
#    options = { \
#      "code": "KeyW",
#      "key": "w",
#      "text": "w",
#      "unmodifiedText": "w",
#      "nativeVirtualKeyCode": ord("W"),
#      "windowsVirtualKeyCode": ord("W")
#    }
#  
#    while True:
#      dispatchKeyEvent(driver, "rawKeyDown", options)
#      dispatchKeyEvent(driver, "char", options)
#  
#      if time.time() > endtime:
#        dispatchKeyEvent(driver, "keyUp", options)
#        break
#  
#      options["autoRepeat"] = True
#      time.sleep(0.01)
#  
#  
#  driver = webdriver.Chrome()
#  driver.get("https://stackoverflow.com/questions")
#  
#  # set the focus on the targeted element
#  driver.find_element_by_css_selector("input[name=q]").click()
#  
#  # press the key W during a second
#  holdKeyW(driver, 1.0)
