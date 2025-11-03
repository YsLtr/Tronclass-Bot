import time
from verify import send_code, send_radar

def rc_type(is_number, is_radar):
    if is_number & is_radar:
        return "数字及雷达签到"
    elif is_radar:
        return "雷达签到"
    else:
        return "数字签到"

def parse_rollcalls(data, verified_cookies):
    rollcalls = data['rollcalls']
    count = len(rollcalls)
    print(time.strftime("%H:%M:%S", time.localtime()), f"监测到 {count} 个新的签到活动。\n")
    for i in range(count):
        print(f"第 {i+1} 个，共 {count} 个：")
        print(f"课程名称：{rollcalls[i]['course_title']}")
        print(f"签到创建：{rollcalls[i]['created_by_name']}")
        print(f"签到状态：{rollcalls[i]['rollcall_status']}")
        print(f"是否计分：{rollcalls[i]['scored']}")
        print(f"出勤情况：{rollcalls[i]['status']}")
        print(f"签到类型：{rc_type(rollcalls[i]['is_number'], rollcalls[i]['is_radar'])}")

        if rollcalls[i]['status'] == 'absent':
            if rollcalls[i]['is_number']:
                if send_code(rollcalls[i]['rollcall_id'], verified_cookies):
                    print("签到成功！")
                    return True
                else:
                    print("签到失败。")
                    return False
            elif rollcalls[i]['is_radar']:
                if send_radar(rollcalls[i]['rollcall_id'], verified_cookies):
                    print("签到成功！")
                    return True
                else:
                    print("签到失败。")
                    return False
        elif rollcalls[i]['status'] == 'on_call_fine':
            print("该签到已完成。")
            return True
    else:
        return False
