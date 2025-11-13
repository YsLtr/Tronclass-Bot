# 畅课平台签到助手 V1.0
# by KrsMt-0113
import time
import json
import requests
from parse_rollcalls import parse_rollcalls
from login import login
from cookie_manager import CookieManager
from browser_manager import BrowserManager

with open("config.json", encoding='utf-8') as f:
    config = json.load(f)
    username = config["username"]
    password = config["password"]
    
    # 浏览器配置
    browser_config = config.get('browser', {})
    browser_type = browser_config.get('type', 'chrome')
    headless = browser_config.get('headless', True)
    window_size = tuple(browser_config.get('window_size', [1920, 1080]))
    user_agent = browser_config.get('user_agent', 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # 性能配置
    performance_config = config.get('performance', {})
    page_load_timeout = performance_config.get('page_load_timeout', 30)
    implicit_wait = performance_config.get('implicit_wait', 10)

api_url = "https://lnt.xmu.edu.cn/api/radar/rollcalls"

# 初始化cookie管理器和浏览器管理器
cookie_manager = CookieManager()

print("正在初始化浏览器...")
try:
    # 创建浏览器管理器
    browser_manager = BrowserManager({
        'browser_type': browser_type,
        'headless': headless,
        'window_size': window_size,
        'user_agent': user_agent
    })
    
    # 获取浏览器驱动
    driver = browser_manager.get_driver()
    print(f"✓ {browser_type.capitalize()} 浏览器初始化成功")
    
except Exception as e:
    print(f"✗ 浏览器初始化失败: {e}")
    print("请检查是否安装了Chrome或Firefox浏览器，以及对应的WebDriver")
    exit(1)

# 尝试使用已保存的cookies
verified_cookies = cookie_manager.get_valid_cookies()
login_status = False

if verified_cookies:
    print("使用已保存的cookies，跳过登录")
    login_status = True
else:
    print("未找到有效cookies，需要重新登录")
    # 访问登录页面,不开VPN好像连不上
    driver.get("https://lnt.xmu.edu.cn")

    ts = int(time.time() * 1000)
    temp_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"}
    captcha_url = f"https://ids.xmu.edu.cn/authserver/checkNeedCaptcha.htl?username={username}&_={ts}"
    res_data = requests.get(captcha_url, headers=temp_header).json()

    login_status, verified_cookies = login(api_url, driver, res_data['isNeed'], username, password)
    if login_status:
        # 保存登录后的cookies
        cookie_manager.save_cookies(verified_cookies)
        print("Cookies已保存")

if not login_status:
    print("登录失败，程序终止。")
    browser_manager.quit_driver()
    exit()

print(time.strftime("%H:%M:%S", time.localtime()), "登录成功！签到监控启动。")

start = time.time()
temp_data = {'rollcalls': []}
count = 0
relogin_attempts = 0
max_relogin_attempts = 3

while True:
    # 每30次请求刷新一次cookies
    if count % 30 == 0:
        # 如果有driver实例，则从driver获取cookies
        if 'driver' in locals() and driver:
            driver.get(api_url)
            verified_cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            # 更新保存的cookies
            cookie_manager.save_cookies(verified_cookies)
    
    res = requests.get(api_url, cookies=verified_cookies)
    if res.status_code == 200:
        data = res.json()
        try:
            if temp_data != data:
                temp_data = data
                if len(temp_data['rollcalls']) > 0:
                    results = parse_rollcalls(temp_data, verified_cookies)
                    # 检查是否有签到失败的记录
                    failed_count = sum(1 for r in results if not r['success'])
                    if failed_count > 0:
                        print(f"签到完成，失败任务数: {failed_count}")
                    temp_data = {'rollcalls': []}
        except Exception as e:
            print(time.strftime("%H:%M:%S", time.localtime()), ":发生错误", e)

    elif res.status_code != 200:
        print("失去连接，尝试重新登录...")
        relogin_attempts += 1
        
        if relogin_attempts <= max_relogin_attempts:
            # 清除无效的cookies
            cookie_manager.clear_cookies()
            
            # 重新登录
            print(f"正在进行第{relogin_attempts}次重新登录尝试...")
            driver.get("https://lnt.xmu.edu.cn")
            
            ts = int(time.time() * 1000)
            temp_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"}
            captcha_url = f"https://ids.xmu.edu.cn/authserver/checkNeedCaptcha.htl?username={username}&_={ts}"
            res_data = requests.get(captcha_url, headers=temp_header).json()
            
            login_status, verified_cookies = login(api_url, driver, res_data['isNeed'], username, password)
            
            if login_status:
                # 保存新的cookies
                cookie_manager.save_cookies(verified_cookies)
                print("重新登录成功，cookies已更新")
                relogin_attempts = 0  # 重置重试计数器
                print(time.strftime("%H:%M:%S", time.localtime()), "重新登录成功！签到监控继续。")
                continue  # 跳过本次循环的剩余部分，直接进入下一次循环
            else:
                print(f"第{relogin_attempts}次重新登录失败")
                if relogin_attempts >= max_relogin_attempts:
                    print("已达到最大重新登录尝试次数，程序终止。")
                    break
        else:
            print("已达到最大重新登录尝试次数，程序终止。")
            break
    
    count += 1
    time.sleep(1)
    if count % 5 == 0:
        time.sleep(3)

browser_manager.quit_driver()
