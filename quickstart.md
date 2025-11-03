# 快速开始

1. 项目概况

    `main.py`: 主程序。主要处理登录与签到的监控。
    
    `login.py`: 用于登录的模块。

    `parse_rollcalls.py`: 用于解析签到任务的模块。

    `verify.py`: 用于数字签到、雷达签到的模块。

    `config.json`: 配置文件。存储用户账号信息。
   
    > `main.py`登录，启动监控 → 监测到签到任务 → `parse_rollcalls.py`解析任务信息 → `verify.py`遍历并发送签到码 → 完成签到。


2. 环境准备

   - `Python`版本: 建议 `3.13.*`
    
   - 安装依赖: `pip install -r requirements.txt`

   - 网络环境: 可能需要 VPN，`Selenium`存在无法直连的情况。
   
3. 配置文件

    在 `config.json` 中的对应位置填入账号、密码, 不填或填错将自动进入扫码签到。

    ```json
    {
        "username": "账号",
        "password": "密码"
    }
    ```
   
4. 运行程序
    
    CLI 模式：直接运行 `main.py` 即可。
