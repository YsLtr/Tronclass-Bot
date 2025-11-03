# 厦大数字化教学平台自动签到机器人 V1.0
# by KrsMt-0113
import time
import json
import requests
from tkinter import Tk, Label
from PIL import ImageTk, Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from parse_rollcalls import parse_rollcalls
from login import login

with open("config.json") as f:
    config = json.load(f)
    username = config["username"]
    password = config["password"]

api_url = "https://lnt.xmu.edu.cn/api/radar/rollcalls"
interval = 1.5
# fetch_script = """
# const url = arguments[0];
# const callback = arguments[arguments.length - 1];
# fetch(url, {credentials: 'include'})
#   .then(resp => resp.text().then(text => callback({status: resp.status, ok: resp.ok, text: text})))
#   .catch(err => callback({error: String(err)}));
# """

chrome_options = Options()
# chrome_options.add_argument("--start-maximized")   # 有头调试
chrome_options.add_argument("--headless")  # 无头运行

print("正在初始化...")
driver = webdriver.Chrome(options=chrome_options)

# 访问登录页面,不开VPN好像连不上
driver.get("https://lnt.xmu.edu.cn")
print("已连接到厦大数字化教学平台。")

ts = int(time.time() * 1000)
temp_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"}
temp_url = f"https://ids.xmu.edu.cn/authserver/checkNeedCaptcha.htl?username={username}&_={ts}"
res_data = requests.get(temp_url, cookies={c['name']: c['value'] for c in driver.get_cookies()}, headers=temp_header).json()

login_status, verified_cookies = login(api_url, driver, res_data['isNeed'], username, password)
if not login_status:
    print("登录失败，程序终止。")
    driver.quit()
    exit()

print("登录成功！")
print(f"签到监控启动。")
start = time.time()
temp_data = {'rollcalls': []}
while True:
    res = requests.get(api_url, cookies=verified_cookies)
    if res.status_code == 200:
        data = res.json()
        try:
            if temp_data == data:
                continue
            else:
                temp_data = data
                if len(temp_data['rollcalls']) > 0:
                    if not parse_rollcalls(temp_data, verified_cookies):
                        temp_data = {'rollcalls': []}
        except Exception as e:
            print(time.strftime("%H:%M:%S", time.localtime()), ":发生错误",e)

    elif res.status_code != 200:
        print("失去连接，请重新登录。")
        break
    time.sleep(interval)

driver.quit()
