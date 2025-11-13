import time
import requests
import os
from tkinter import Tk, Label
from PIL import ImageTk, Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_element_operation(func, *args, **kwargs):
    """安全的元素操作，带重试机制"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except StaleElementReferenceException:
            if attempt < max_retries - 1:
                logger.warning(f"元素引用失效，{max_retries - attempt - 1}次重试中...")
                time.sleep(1)
                continue
            else:
                logger.error("元素操作失败，已达到最大重试次数")
                raise
        except Exception as e:
            logger.error(f"元素操作失败: {e}")
            raise

def login(url, driver, status, username, password):
    """登录函数，增强的错误处理和Linux兼容性"""
    if not status:
        print("登录无需验证,正在登录...")
        
        try:
            # 确保页面完全加载
            driver.implicitly_wait(5)
            time.sleep(2)
            
            # 安全点击用户登录选项卡
            def click_login_tab():
                tab = WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable((By.ID, "userNameLogin_a"))
                )
                tab.click()
                return True
            
            safe_element_operation(click_login_tab)
            time.sleep(2)  # 等待页面响应
            
            # 安全输入用户名
            def input_username():
                username_field = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.ID, "username"))
                )
                username_field.clear()
                time.sleep(0.5)  # 小延迟确保清除完成
                username_field.send_keys(username)
                return True
            
            safe_element_operation(input_username)
            time.sleep(1)
            
            # 安全输入密码
            def input_password():
                password_field = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.ID, "password"))
                )
                password_field.clear()
                time.sleep(0.5)
                password_field.send_keys(password)
                return True
            
            safe_element_operation(input_password)
            time.sleep(1)
            
            # 安全点击登录按钮
            def click_login_button():
                login_button = WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable((By.ID, "login_submit"))
                )
                login_button.click()
                return True
            
            safe_element_operation(click_login_button)
            
            # 等待登录处理完成
            print("等待登录处理...")
            time.sleep(5)
            
            # 重新导航到目标页面
            driver.get(url)
            time.sleep(3)
            
            # 验证登录状态
            try:
                res = requests.get(url, cookies={c['name']: c['value'] for c in driver.get_cookies()}, timeout=10)
                if res.status_code == 200:
                    verified_cookies = {c['name']: c['value'] for c in driver.get_cookies()}
                    print("✓ 登录成功!")
                    return True, verified_cookies
                else:
                    print(f"登录验证失败，HTTP状态码: {res.status_code}")
            except requests.RequestException as e:
                print(f"登录验证请求失败: {e}")
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"页面元素未找到: {e}")
        except Exception as e:
            print(f"登录过程出错: {e}")
            logger.exception("登录异常详情")

    # 企业微信扫码登录
    print("使用企业微信扫码登录。")
    try:
        # 确保cache目录存在
        os.makedirs("cache", exist_ok=True)
        
        qr_tab = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.ID, "qrLogin_a"))
        )
        qr_tab.click()
        time.sleep(2)
        
        driver.set_window_size(1920, 1080)
        
        # 尝试获取二维码图片，优先尝试qr_img，如果不存在则尝试invalid_img
        try:
            qr_img = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.ID, "qr_img"))
            )
        except TimeoutException:
            try:
                qr_img = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.ID, "invalid_img"))
                )
            except TimeoutException:
                raise Exception("无法找到二维码图片元素")
        
        # 获取二维码图片的src属性（直接下载而不是截图）
        qr_img_url = qr_img.get_attribute("src")
        if not qr_img_url:
            raise Exception("无法获取二维码图片URL")
        
        # 确保URL是完整的
        if qr_img_url.startswith("/"):
            qr_img_url = driver.current_url.rsplit("/", 2)[0] + qr_img_url
        elif not qr_img_url.startswith("http"):
            base_url = driver.current_url.rsplit("/", 1)[0]
            qr_img_url = base_url + "/" + qr_img_url
        
        # 下载二维码图片
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent;"),
            'Referer': driver.current_url
        }
        
        try:
            # 先尝试从浏览器缓存获取cookies
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            
            # 下载二维码图片
            response = requests.get(qr_img_url, cookies=cookies, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 保存二维码图片
            with open("cache/qr_code.png", "wb") as f:
                f.write(response.content)
            print("二维码已保存到 cache/qr_code.png")
            
        except requests.RequestException as e:
            print(f"下载二维码失败: {e}")
            # 如果下载失败，回退到截图方式
            print("回退到截图方式...")
            qr_img.screenshot("cache/qr_code.png")
            print("二维码已保存到 cache/qr_code.png（截图方式）")
        
        # 显示二维码（Linux环境可能不支持GUI）
        try:
            root = Tk()
            root.title("请扫描二维码登录")
            img = Image.open("cache/qr_code.png")
            tk_img = ImageTk.PhotoImage(img)
            Label(root, image=tk_img).pack()
            print("请在弹出的窗口中扫描二维码...")
            root.mainloop()
        except Exception as e:
            print(f"无法显示GUI窗口: {e}")
            print("请手动打开 cache/qr_code.png 文件扫描二维码")
            input("扫描完成后按回车键继续...")
        
        # 验证登录状态
        try:
            res = requests.get(url, cookies={c['name']: c['value'] for c in driver.get_cookies()}, timeout=10)
            if res.status_code == 200:
                verified_cookies = {c['name']: c['value'] for c in driver.get_cookies()}
                print("✓ 扫码登录成功!")
                return True, verified_cookies
        except requests.RequestException as e:
            print(f"登录验证请求失败: {e}")
            
    except Exception as e:
        print(f"扫码登录过程出错: {e}")
        logger.exception("扫码登录异常详情")

    return False, None
