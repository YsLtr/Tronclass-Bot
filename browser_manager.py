#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理器 - 支持多浏览器驱动
为项目添加Firefox驱动支持，同时保持Chrome兼容性
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException

class BrowserManager:
    """浏览器管理器 - 支持Chrome和Firefox"""
    
    def __init__(self, config=None):
        """
        初始化浏览器管理器
        
        Args:
            config: 浏览器配置字典，包含browser_type, headless等选项
        """
        self.config = config or {}
        self.driver = None
        self.browser_type = self.config.get('browser_type', 'chrome').lower()
        self.headless = self.config.get('headless', True)
        self.window_size = self.config.get('window_size', (1920, 1080))
        self.user_agent = self.config.get('user_agent', 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 检查驱动可用性
        self._check_driver_availability()
    
    def _check_driver_availability(self):
        """检查浏览器驱动是否可用"""
        self.available_browsers = []
        
        # 检查Chrome
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless=new')  # 使用新的headless模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            
            # Linux环境下特殊配置
            if os.name == 'posix':  # Linux/Unix系统
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-setuid-sandbox')
                chrome_options.add_argument('--single-process')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                chrome_options.add_argument('--disable-renderer-backgrounding')
            
            test_driver = webdriver.Chrome(options=chrome_options)
            test_driver.quit()
            self.available_browsers.append('chrome')
            self.logger.info("Chrome驱动可用")
        except (WebDriverException, SessionNotCreatedException, Exception) as e:
            self.logger.warning(f"Chrome驱动不可用: {e}")
        
        # 检查Firefox
        try:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')
            
            # Linux环境下特殊配置
            if os.name == 'posix':  # Linux/Unix系统
                firefox_options.set_preference("webdriver.log.file", "/dev/null")
                firefox_options.set_preference("marionette.log.level", "FATAL")
            
            firefox_options.set_preference("general.useragent.override", self.user_agent)
            test_driver = webdriver.Firefox(options=firefox_options)
            test_driver.quit()
            self.available_browsers.append('firefox')
            self.logger.info("Firefox驱动可用")
        except (WebDriverException, SessionNotCreatedException, Exception) as e:
            self.logger.warning(f"Firefox驱动不可用: {e}")
        
        if not self.available_browsers:
            raise RuntimeError("未找到可用的浏览器驱动！请安装Chrome或Firefox浏览器及其驱动。")
        
        # 如果配置的浏览器不可用，选择第一个可用的
        if self.browser_type not in self.available_browsers:
            self.browser_type = self.available_browsers[0]
            self.logger.warning(f"配置的浏览器 {self.browser_type} 不可用，自动切换到: {self.browser_type}")
    
    def _setup_chrome_driver(self):
        """配置Chrome浏览器驱动"""
        options = ChromeOptions()
        
        # 基本配置
        if self.headless:
            options.add_argument('--headless=new')  # 使用新的headless模式
        
        # 稳定性配置 - 特别针对Linux环境
        if os.name == 'posix':  # Linux/Unix系统
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--single-process')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
        else:
            # Windows/macOS配置
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
        
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # 禁用图片加载以提高速度
        
        # 性能优化
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # 用户代理
        options.add_argument(f'--user-agent={self.user_agent}')
        
        # 窗口大小
        options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
        
        # 日志级别
        options.add_argument('--log-level=3')
        
        # 防止自动化检测
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 初始化驱动
        try:
            driver = webdriver.Chrome(options=options)
            # 隐藏自动化属性
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.logger.error(f"启动Chrome失败: {e}")
            raise
    
    def _setup_firefox_driver(self):
        """配置Firefox浏览器驱动"""
        options = FirefoxOptions()
        
        # 基本配置
        if self.headless:
            options.add_argument('--headless')
        
        # Linux环境特定配置
        if os.name == 'posix':  # Linux/Unix系统
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.log.level = "trace"  # 更详细的日志记录
        
        # 用户代理
        options.set_preference("general.useragent.override", self.user_agent)
        
        # 窗口大小
        options.add_argument(f'--width={self.window_size[0]}')
        options.add_argument(f'--height={self.window_size[1]}')
        
        # 性能优化
        options.set_preference("network.http.pipelining", True)
        options.set_preference("network.http.pipelining.maxrequests", 8)
        options.set_preference("content.notify.interval", 500000)
        options.set_preference("content.notify.ontimer", True)
        options.set_preference("content.switch.threshold", 250000)
        options.set_preference("browser.cache.memory.capacity", 65536)
        
        # 禁用图片加载
        options.set_preference("permissions.default.image", 2)
        options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
        
        # 防止自动化检测
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        # 初始化驱动
        try:
            driver = webdriver.Firefox(options=options)
            # 隐藏自动化属性
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.logger.error(f"启动Firefox失败: {e}")
            raise
    
    def get_driver(self):
        """
        获取浏览器驱动实例
        
        Returns:
            webdriver: Selenium WebDriver实例
        """
        if self.driver is None:
            self.logger.info(f"启动浏览器: {self.browser_type}")
            
            if self.browser_type == 'chrome':
                self.driver = self._setup_chrome_driver()
            elif self.browser_type == 'firefox':
                self.driver = self._setup_firefox_driver()
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.logger.info(f"{self.browser_type.capitalize()} 浏览器启动成功")
        
        return self.driver
    
    def quit_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("浏览器驱动已关闭")
            except Exception as e:
                self.logger.warning(f"关闭浏览器时发生错误: {e}")
            finally:
                self.driver = None
    
    def restart_driver(self):
        """重启浏览器驱动"""
        self.logger.info("重启浏览器驱动...")
        self.quit_driver()
        return self.get_driver()
    
    def get_browser_info(self):
        """获取浏览器信息"""
        driver = self.get_driver()
        return {
            'browser_type': self.browser_type,
            'headless': self.headless,
            'window_size': self.window_size,
            'user_agent': self.user_agent,
            'title': driver.title,
            'current_url': driver.current_url,
            'available_browsers': self.available_browsers
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.quit_driver()

# 工厂函数，便于创建浏览器管理器
def create_browser_manager(browser_type='chrome', headless=True, **kwargs):
    """
    创建浏览器管理器实例
    
    Args:
        browser_type: 浏览器类型 ('chrome' 或 'firefox')
        headless: 是否无头模式
        **kwargs: 其他配置选项
    
    Returns:
        BrowserManager: 浏览器管理器实例
    """
    config = {
        'browser_type': browser_type,
        'headless': headless,
        **kwargs
    }
    return BrowserManager(config)

# 兼容性函数 - 模拟原有的webdriver接口
def create_driver(browser_type='chrome', headless=True, **kwargs):
    """
    创建浏览器驱动（兼容性函数）
    
    保持与原有代码的兼容性
    
    Args:
        browser_type: 浏览器类型
        headless: 是否无头模式
        **kwargs: 其他配置选项
    
    Returns:
        webdriver: Selenium WebDriver实例
    """
    manager = create_browser_manager(browser_type, headless, **kwargs)
    return manager.get_driver()