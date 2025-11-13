#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析签到数据的模块
根据签到任务状态和类型调用相应的签到函数
"""

from verify_optimized import send_code_optimized_with_pool, send_radar, send_code_hybrid, send_code_original


def rc_type(rollcall):
    """判断签到类型"""
    if rollcall.get('is_number', False):
        return 'code'
    elif rollcall.get('is_radar', False):
        return 'radar'
    else:
        return 'unknown'


def parse_rollcalls(rollcalls_data, verified_cookies=None):
    """
    解析签到任务数据
    根据签到状态和类型调用相应的签到函数

    Args:
        rollcalls_data: 从API获取的签到任务数据
        verified_cookies: 验证后的cookies（可选）

    Returns:
        list: 包含每个签到任务的处理结果的列表
    """
    results = []
    success = False
    message = ""

    # 遍历所有签到任务
    for i, rollcall in enumerate(rollcalls_data.get('rollcalls', [])):
        rollcall_id = rollcall.get('rollcall_id')
        course_name = rollcall.get('course_title', '未知课程')
        # 使用course_id字段，如果不存在则设为None
        course_id = rollcall.get('course_id') or None

        # 检查签到状态 - 优先使用status，否则使用rollcall_status
        status = rollcall.get('status') or rollcall.get('rollcall_status')

        if status == 'absent':  # 需要签到
            print(f"[解析器] 发现需要签到的任务 {i+1}: 课程={course_name}, 类型={rc_type(rollcall)}")

            # 根据签到类型调用相应函数
            if rc_type(rollcall) == 'code':
                print(f"[解析器] 调用数字签到函数，课程: {course_name}")
                #success = send_code_optimized_with_pool(rollcall_id, verified_cookies, course_name, course_id) #多线程并发
                #success = send_code_original(rollcall_id, verified_cookies) #异步IO并发
                success = send_code_hybrid(rollcall_id, verified_cookies, course_name, course_id)#多线程+异步IO并发
            elif rc_type(rollcall) == 'radar':
                print(f"[解析器] 调用雷达签到函数，课程: {course_name}")
                success = send_radar(rollcall_id, verified_cookies, course_name, course_id)
            else:
                print(f"[解析器] 未知签到类型: {rollcall.get('rollcall_type')}")
                success = False
                message = "未知签到类型"

        elif status == 'on_call_fine':  # 已经签到
            print(f"[解析器] 任务 {i+1} 已签到: {course_name}")
            success = True
            message = "已签到"

        else:
            print(f"[解析器] 任务 {i+1} 状态未知: {status}")
            success = False
            message = "状态未知"

        results.append({
            'index': i,
            'rollcall_id': rollcall_id,
            'course_name': course_name,
            'course_id': course_id,
            'status': status,
            'success': success,
            'message': message
        })

    return results
