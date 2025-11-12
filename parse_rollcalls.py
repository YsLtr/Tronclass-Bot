#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析签到数据的模块
根据签到任务状态和类型调用相应的签到函数
"""

from verify_optimized import send_code_optimized_with_pool, send_radar


def rc_type(rollcall):
    """判断签到类型"""
    if rollcall.get('rollcall_type') == 'CodeRollcall':
        return 'code'
    elif rollcall.get('rollcall_type') == 'RadarRollcall':
        return 'radar'
    else:
        return 'unknown'


def parse_rollcalls(rollcalls_data):
    """
    解析签到任务数据
    根据签到状态和类型调用相应的签到函数
    
    Args:
        rollcalls_data: 从API获取的签到任务数据
    
    Returns:
        list: 包含每个签到任务的处理结果的列表
    """
    results = []
    
    # 遍历所有签到任务
    for i, rollcall in enumerate(rollcalls_data.get('rollcalls', [])):
        rollcall_id = rollcall.get('id')
        course_name = rollcall.get('course_title', '未知课程')
        # 使用course_id字段，如果不存在则设为None
        course_id = rollcall.get('course_id') or None
        
        # 检查签到状态
        status = rollcall.get('rollcall_status')
        
        if status == 'absent':  # 需要签到
            print(f"[解析器] 发现需要签到的任务 {i+1}: 课程={course_name}, 类型={rc_type(rollcall)}")
            
            # 根据签到类型调用相应函数
            if rc_type(rollcall) == 'code':
                print(f"[解析器] 调用数字签到函数，课程: {course_name}")
                result = send_code_optimized_with_pool(rollcall_id, rollcall, course_name, course_id)
            elif rc_type(rollcall) == 'radar':
                print(f"[解析器] 调用雷达签到函数，课程: {course_name}")
                result = send_radar(rollcall_id, rollcall, course_name, course_id)
            else:
                print(f"[解析器] 未知签到类型: {rollcall.get('rollcall_type')}")
                result = {'success': False, 'message': '未知签到类型'}
        
        elif status == 'on_call_fine':  # 已经签到
            print(f"[解析器] 任务 {i+1} 已签到: {course_name}")
            result = {'success': True, 'message': '已签到'}
        
        else:
            print(f"[解析器] 任务 {i+1} 状态未知: {status}")
            result = {'success': False, 'message': '状态未知'}
        
        results.append({
            'index': i,
            'rollcall_id': rollcall_id,
            'course_name': course_name,
            'course_id': course_id,
            'status': status,
            'result': result
        })
    
    return results
