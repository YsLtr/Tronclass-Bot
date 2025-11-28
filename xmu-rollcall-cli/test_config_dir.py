#!/usr/bin/env python3
"""
测试配置目录选择逻辑
用于验证在不同环境下配置文件路径是否正确
"""

import os
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / "xmu_rollcall"))

from xmu_rollcall.config import CONFIG_DIR, CONFIG_FILE

def test_config_dir():
    print("=== XMU Rollcall Config Directory Test ===\n")

    # 显示环境变量
    env_config_dir = os.environ.get("XMU_ROLLCALL_CONFIG_DIR")
    print(f"Environment Variable XMU_ROLLCALL_CONFIG_DIR: {env_config_dir or '(not set)'}")

    # 显示选择的配置目录
    print(f"\nSelected Config Directory: {CONFIG_DIR}")
    print(f"Config File Path: {CONFIG_FILE}")

    # 检查目录是否存在
    print(f"\nDirectory exists: {CONFIG_DIR.exists()}")

    # 测试写入权限
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        test_file = CONFIG_DIR / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        print(f"Write permission: ✓ OK")
    except Exception as e:
        print(f"Write permission: ✗ FAILED ({e})")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_config_dir()

