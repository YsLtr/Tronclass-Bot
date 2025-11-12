import json
import os
import requests
from datetime import datetime, timedelta

class CookieManager:
    def __init__(self, cookie_file="cookies.json"):
        self.cookie_file = cookie_file
        self.api_url = "https://lnt.xmu.edu.cn/api/radar/rollcalls"
    
    def save_cookies(self, cookies):
        """保存cookies到文件"""
        try:
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cookies': cookies,
                    'saved_time': datetime.now().isoformat()
                }, f)
            return True
        except Exception as e:
            print(f"保存cookies失败: {e}")
            return False
    
    def load_cookies(self):
        """从文件加载cookies"""
        if not os.path.exists(self.cookie_file):
            return None
        
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('cookies')
        except Exception as e:
            print(f"加载cookies失败: {e}")
            return None
    
    def get_saved_time(self):
        """获取cookies的保存时间"""
        if not os.path.exists(self.cookie_file):
            return None
        
        try:
            with open(self.cookie_file, 'r') as f:
                data = json.load(f)
                saved_time_str = data.get('saved_time')
                if saved_time_str:
                    return datetime.fromisoformat(saved_time_str)
        except Exception as e:
            print(f"获取保存时间失败: {e}")
        
        return None
    
    def is_cookie_expired(self, max_hours=24):
        """检查cookies是否过期（默认24小时）"""
        saved_time = self.get_saved_time()
        if not saved_time:
            return True
        
        return datetime.now() - saved_time > timedelta(hours=max_hours)
    
    def is_cookie_valid(self, cookies):
        """检查cookies是否有效（通过发送请求验证）"""
        if not cookies:
            return False
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            }
            response = requests.get(self.api_url, cookies=cookies, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"验证cookies有效性时出错: {e}")
            return False
    
    def get_valid_cookies(self, force_check=False):
        """获取有效的cookies，如果无效则返回None"""
        cookies = self.load_cookies()
        
        if not cookies:
            return None
        
        # 检查是否过期
        if self.is_cookie_expired():
            print("Cookies已过期")
            return None
        
        # 如果需要强制检查，则发送请求验证
        if force_check:
            if not self.is_cookie_valid(cookies):
                print("Cookies无效")
                return None
        
        print("使用已保存的有效cookies")
        return cookies
    
    def clear_cookies(self):
        """清除cookies文件"""
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['cookies'] = None
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False