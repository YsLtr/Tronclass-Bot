import uuid
import requests
import time
import threading
import random
import json
import os
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from checkin_recorder import CheckinRecorder


def pad(i):
    return str(i).zfill(4)

def send_code_optimized(rollcall_id, verified_cookies):
    """
    优化后的数字签到函数
    使用多线程并发，每个线程负责不同范围的随机请求
    """
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies = verified_cookies
    print("正在使用优化算法遍历签到码...")
    t00 = time.time()
    
    # 全局变量，用于线程间通信
    stop_event = threading.Event()
    found_code = [None]  # 使用列表以便在多线程中修改
    
    # 创建线程锁，确保不会重复选取相同的值
    lock = threading.Lock()
    used_codes = set()  # 记录已使用的签到码
    
    def worker_thread(thread_id, start_range, end_range):
        """
        工作线程函数
        thread_id: 线程ID
        start_range: 该线程负责的起始范围
        end_range: 该线程负责的结束范围
        """
        # 生成该线程负责范围内的所有可能的签到码
        possible_codes = list(range(start_range, end_range + 1))
        random.shuffle(possible_codes)  # 随机打乱顺序
        
        for i in possible_codes:
            # 检查是否已经找到正确的签到码
            if stop_event.is_set():
                return None
                
            # 使用锁确保不会重复选取相同的值
            with lock:
                if i in used_codes:
                    continue  # 如果该签到码已被其他线程使用，跳过
                used_codes.add(i)  # 标记为已使用
                
            code = pad(i)
            payload = {
                "deviceId": str(uuid.uuid4()),
                "numberCode": code
            }
            
            try:
                response = requests.put(url, json=payload, headers=headers, cookies=cookies, timeout=5)
                if response.status_code == 200:
                    # 找到正确的签到码
                    stop_event.set()
                    found_code[0] = code
                    print(f"线程 {thread_id} 找到签到码: {code}")
                    return code
            except Exception:
                pass  # 忽略异常，继续尝试下一个签到码
                
        return None
    
    # 计算每个线程负责的范围
    total_codes = 10000  # 0000-9999
    num_threads = min(200, total_codes)  # 最多200个线程
    codes_per_thread = total_codes // num_threads
    
    threads = []
    
    # 创建并启动线程
    for i in range(num_threads):
        start = i * codes_per_thread
        end = (i + 1) * codes_per_thread - 1
        # 最后一个线程负责剩余的所有签到码
        if i == num_threads - 1:
            end = total_codes - 1
            
        thread = threading.Thread(target=worker_thread, args=(i, start, end))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成或找到正确的签到码
    for thread in threads:
        thread.join()
    
    t01 = time.time()
    if found_code[0]:
        print(f"签到成功! 签到码: {found_code[0]}")
        print(f"用时: {t01 - t00:.2f} 秒")
        
        # 记录成功的签到
        try:
            recorder = CheckinRecorder()
            recorder.add_record(
                course_name=course_name or "未知课程",
                course_id=course_id,
                rollcall_id=str(rollcall_id),
                checkin_code=found_code[0],
                checkin_type="数字签到",
                success=True
            )
        except Exception as e:
            print(f"[记录器] 记录签到信息时出错: {str(e)}")
        
        return True
    else:
        print(f"签到失败。用时: {t01 - t00:.2f} 秒")
        
        # 记录失败的签到
        try:
            recorder = CheckinRecorder()
            recorder.add_record(
                course_name=course_name or "未知课程",
                course_id=course_id,
                rollcall_id=str(rollcall_id),
                checkin_code=None,
                checkin_type="数字签到",
                success=False
            )
        except Exception as e:
            print(f"[记录器] 记录签到信息时出错: {str(e)}")
        
        return False

def send_code_optimized_with_pool(rollcall_id, verified_cookies, course_name=None, course_id=None):
    """
    使用线程池优化后的数字签到函数
    使用ThreadPoolExecutor管理线程池
    
    Args:
        rollcall_id: 签到活动ID
        verified_cookies: 验证后的cookies
        course_name: 课程名称（可选）
        course_id: 课程ID（可选）
    """
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies = verified_cookies
    print("正在使用线程池优化算法遍历签到码...")
    t00 = time.time()
    
    # 全局变量，用于线程间通信
    stop_event = threading.Event()
    found_code = [None]  # 使用列表以便在多线程中修改
    
    # 创建线程锁，确保不会重复选取相同的值
    lock = threading.Lock()
    used_codes = set()  # 记录已使用的签到码
    
    def worker_task(thread_id, start_range, end_range):
        """
        工作任务函数
        thread_id: 线程ID
        start_range: 该线程负责的起始范围
        end_range: 该线程负责的结束范围
        """
        # 生成该线程负责范围内的所有可能的签到码
        possible_codes = list(range(start_range, end_range + 1))
        random.shuffle(possible_codes)  # 随机打乱顺序
        
        for i in possible_codes:
            # 检查是否已经找到正确的签到码
            if stop_event.is_set():
                return None
                
            # 使用锁确保不会重复选取相同的值
            with lock:
                if i in used_codes:
                    continue  # 如果该签到码已被其他线程使用，跳过
                used_codes.add(i)  # 标记为已使用
                
            code = pad(i)
            payload = {
                "deviceId": str(uuid.uuid4()),
                "numberCode": code
            }
            
            try:
                response = requests.put(url, json=payload, headers=headers, cookies=cookies, timeout=5)
                if response.status_code == 200:
                    # 找到正确的签到码
                    stop_event.set()
                    found_code[0] = code
                    print(f"线程 {thread_id} 找到签到码: {code}")
                    return code
            except Exception:
                pass  # 忽略异常，继续尝试下一个签到码
                
        return None
    
    # 计算每个线程负责的范围
    total_codes = 10000  # 0000-9999
    num_threads = min(200, total_codes)  # 最多200个线程
    codes_per_thread = total_codes // num_threads
    
    # 使用线程池
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        
        # 提交任务到线程池
        for i in range(num_threads):
            start = i * codes_per_thread
            end = (i + 1) * codes_per_thread - 1
            # 最后一个线程负责剩余的所有签到码
            if i == num_threads - 1:
                end = total_codes - 1
                
            future = executor.submit(worker_task, i, start, end)
            futures.append(future)
        
        # 等待任务完成
        try:
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    # 找到正确的签到码，取消其他任务
                    for f in futures:
                        f.cancel()
                    break
        except Exception:
            pass
    
    t01 = time.time()
    if found_code[0]:
        print(f"签到成功! 签到码: {found_code[0]}")
        print(f"用时: {t01 - t00:.2f} 秒")
        
        # 记录成功的签到
        try:
            recorder = CheckinRecorder()
            recorder.add_record(
                course_name=course_name or "未知课程",
                course_id=course_id,
                rollcall_id=str(rollcall_id),
                checkin_code=found_code[0],
                checkin_type="数字签到",
                success=True
            )
        except Exception as e:
            print(f"[记录器] 记录签到信息时出错: {str(e)}")
        
        return True
    else:
        print(f"签到失败。用时: {t01 - t00:.2f} 秒")
        
        # 记录失败的签到
        try:
            recorder = CheckinRecorder()
            recorder.add_record(
                course_name=course_name or "未知课程",
                course_id=course_id,
                rollcall_id=str(rollcall_id),
                checkin_code=None,
                checkin_type="数字签到",
                success=False
            )
        except Exception as e:
            print(f"[记录器] 记录签到信息时出错: {str(e)}")
        
        return False

def send_radar(rollcall_id, verified_cookies, course_name=None, course_id=None):
    """
    雷达签到函数
    从coordinates.json文件加载坐标，默认使用id=1的坐标
    如果一个id中有多个坐标，按顺序使用直到签到成功
    
    Args:
        rollcall_id: 签到活动ID
        verified_cookies: 验证后的cookies
        course_name: 课程名称（可选）
        course_id: 课程ID（可选）
    """
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    coordinates_file = os.path.join(script_dir, 'coordinates.json')
    
    try:
        # 读取坐标文件
        with open(coordinates_file, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except FileNotFoundError:
        print(f"坐标文件未找到: {coordinates_file}")
        return False
    except json.JSONDecodeError:
        print(f"坐标文件格式错误")
        return False
    
    # 默认使用id=1的坐标，如果没有找到则使用第一个
    selected_location = None
    for location in locations:
        if location.get('id') == 1:
            selected_location = location
            break
    
    # 如果没有找到id=1的位置，使用第一个位置
    if selected_location is None and locations:
        selected_location = locations[0]
        print(f"未找到id=1的位置，使用位置: {selected_location['name']}")
    else:
        print(f"使用位置: {selected_location['name']}")
    
    if not selected_location or 'coordinates' not in selected_location:
        print("无效的位置数据")
        return False
    
    coordinates = selected_location['coordinates']
    if not coordinates:
        print("没有可用的坐标")
        return False
    
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer?api_version=1.76"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    
    # 按顺序尝试每个坐标
    for i, coord in enumerate(coordinates):
        latitude, longitude = coord
        
        payload = {
            "accuracy": 35,
            "altitude": 0,
            "altitudeAccuracy": None,
            "deviceId": str(uuid.uuid4()),
            "heading": None,
            "latitude": latitude,
            "longitude": longitude,
            "speed": None
        }
        
        try:
            print(f"尝试坐标 {i+1}/{len(coordinates)}: ({latitude}, {longitude})")
            res = requests.put(url, json=payload, headers=headers, cookies=verified_cookies, timeout=5)
            
            # 解析响应中的距离数据
            distance = None
            if res.status_code == 200:
                try:
                    response_data = res.json()
                    distance = response_data.get('distance')
                    if distance is not None:
                        print(f"  距离: {distance:.2f} 米")
                except Exception:
                    print("  无法解析响应数据")
                
                print(f"雷达签到成功! 使用坐标: ({latitude}, {longitude})")
                
                # 记录成功的签到
                try:
                    recorder = CheckinRecorder()
                    recorder.add_record(
                        course_name=course_name or "未知课程",
                        course_id=course_id,
                        rollcall_id=str(rollcall_id),
                        checkin_code=None,  # 雷达签到没有签到码
                        checkin_type="雷达签到",
                        latitude=latitude,
                        longitude=longitude,
                        success=True,
                        distance=distance
                    )
                except Exception as e:
                    print(f"[记录器] 记录签到信息时出错: {str(e)}")
                
                return True
            else:
                # 尝试解析错误响应的距离数据
                try:
                    error_data = res.json()
                    distance = error_data.get('distance')
                    if distance is not None:
                        print(f"  距离: {distance:.2f} 米 (超出范围)")
                except Exception:
                    pass
                
                print(f"坐标 ({latitude}, {longitude}) 签到失败: HTTP {res.status_code}")
                
                # 记录失败的尝试
                try:
                    recorder = CheckinRecorder()
                    recorder.add_record(
                        course_name=course_name or "未知课程",
                        course_id=course_id,
                        rollcall_id=str(rollcall_id),
                        checkin_code=None,
                        checkin_type="雷达签到",
                        latitude=latitude,
                        longitude=longitude,
                        success=False,
                        distance=distance
                    )
                except Exception as e:
                    print(f"[记录器] 记录失败尝试时出错: {str(e)}")
                
        except Exception as e:
            print(f"坐标 ({latitude}, {longitude}) 请求失败: {str(e)}")
            
            # 记录请求失败的尝试
            try:
                recorder = CheckinRecorder()
                recorder.add_record(
                    course_name=course_name or "未知课程",
                    course_id=course_id,
                    rollcall_id=str(rollcall_id),
                    checkin_code=None,
                    checkin_type="雷达签到",
                    latitude=latitude,
                    longitude=longitude,
                    success=False,
                    distance=None
                )
            except Exception as record_error:
                print(f"[记录器] 记录请求失败时出错: {str(record_error)}")
            
            continue
    
    print("所有坐标尝试完毕，雷达签到失败")
    
    return False

# 保留原始的异步版本作为备份
def send_code_original(rollcall_id, verified_cookies):
    """原始的异步版本，作为备份"""
    import asyncio
    import aiohttp
    
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies = verified_cookies
    print("正在遍历签到码...")
    t00 = time.time()

    async def put_request(i, session, stop_flag, url, headers, sem, timeout):
        if stop_flag.is_set():
            return None
        async with sem:
            if stop_flag.is_set():
                return None
            payload = {
                "deviceId": str(uuid.uuid4()),
                "numberCode": pad(i)
            }
            try:
                async with session.put(url, json=payload, timeout=timeout) as r:
                    if r.status == 200:
                        stop_flag.set()
                        return pad(i)
            except Exception:
                pass
            return None

    async def main():
        stop_flag = asyncio.Event()
        sem = asyncio.Semaphore(200)
        timeout = aiohttp.ClientTimeout(total=5)
        # 直接传 cookies，避免 CookieJar 行为差异
        async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
            # 创建 Task 而不是原始协程
            tasks = [asyncio.create_task(put_request(i, session, stop_flag, url, headers, sem, timeout)) for i in range(10000)]
            try:
                for coro in asyncio.as_completed(tasks):
                    res = await coro
                    if res is not None:
                        # 取消其余未完成的 Task
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        print("签到码:", res)
                        t01 = time.time()
                        print("用时: %.2f 秒" % (t01 - t00))
                        return True
            finally:
                # 确保所有 task 结束
                for t in tasks:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        t01 = time.time()
        print("失败。\n用时: %.2f 秒" % (t01 - t00))
        return False

    return asyncio.run(main())


def send_code_hybrid(rollcall_id, verified_cookies, course_name=None, course_id=None):
    """
    多线程+异步IO混合并发签到函数
    10个线程，每个线程负责1000个数字，每条线程内部并发数为20，总并发数不超过200
    
    Args:
        rollcall_id: 签到活动ID
        verified_cookies: 验证后的cookies
        course_name: 课程名称（可选）
        course_id: 课程ID（可选）
    """
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies = verified_cookies
    
    print("正在使用多线程+异步IO混合算法遍历签到码...")
    print("配置: 10个线程 × 20异步并发 = 200总并发")
    t00 = time.time()
    
    # 全局停止标志和结果存储
    global_stop_event = threading.Event()
    found_code = [None]  # 使用列表以便在多线程中修改
    
    def pad(number):
        """将数字转换为4位字符串，不足补0"""
        return str(number).zfill(4)
    
    async def async_worker(session, code, thread_id, local_stop_event, semaphore):
        """
        异步工作函数 - 单个请求
        """
        # 检查停止标志
        if global_stop_event.is_set() or local_stop_event.is_set():
            return None
            
        async with semaphore:
            # 再次检查停止标志
            if global_stop_event.is_set() or local_stop_event.is_set():
                return None
                
            payload = {
                "deviceId": str(uuid.uuid4()),
                "numberCode": pad(code)
            }
            
            try:
                async with session.put(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        # 找到正确签到码
                        print(f"线程 {thread_id} 找到签到码: {pad(code)}")
                        return pad(code)
            except Exception as e:
                # 忽略错误，继续尝试
                pass
                
            return None
    
    async def async_thread_main(thread_id, codes_to_try, local_stop_event):
        """
        单个线程的异步主函数 - 负责1000个数字
        """
        # 创建该线程的异步资源
        semaphore = asyncio.Semaphore(20)  # 每个线程内部并发数限制为20
        
        # 直接传cookies，避免CookieJar行为差异
        async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
            # 随机打乱代码顺序，避免模式化请求
            random.shuffle(codes_to_try)
            
            # 创建任务列表
            tasks = []
            for code in codes_to_try:
                if global_stop_event.is_set() or local_stop_event.is_set():
                    break
                    
                task = asyncio.create_task(
                    async_worker(session, code, thread_id, local_stop_event, semaphore)
                )
                tasks.append(task)
            
            # 等待第一个成功的结果
            try:
                for coro in asyncio.as_completed(tasks):
                    if global_stop_event.is_set() or local_stop_event.is_set():
                        break
                        
                    result = await coro
                    if result is not None:
                        # 找到正确签到码
                        found_code[0] = result
                        global_stop_event.set()  # 通知所有线程停止
                        local_stop_event.set()   # 通知本线程停止
                        return result
            finally:
                # 清理未完成的任务
                for task in tasks:
                    if not task.done():
                        task.cancel()
                # 等待所有任务结束
                await asyncio.gather(*tasks, return_exceptions=True)
        
        return None
    
    def thread_worker(thread_id, codes_to_try):
        """
        线程工作函数 - 运行异步事件循环
        """
        # 创建线程本地停止标志
        local_stop_event = threading.Event()
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 运行异步主函数
            result = loop.run_until_complete(
                async_thread_main(thread_id, codes_to_try, local_stop_event)
            )
            
            if result is not None:
                print(f"线程 {thread_id} 成功完成任务")
            else:
                if global_stop_event.is_set():
                    print(f"线程 {thread_id} 被其他线程中断")
                else:
                    print(f"线程 {thread_id} 完成所有尝试，未找到正确签到码")
                    
            return result
        except Exception as e:
            print(f"线程 {thread_id} 发生异常: {e}")
            return None
        finally:
            loop.close()
    
    # 分配任务范围给10个线程
    total_codes = 10000  # 0000-9999
    num_threads = 10
    codes_per_thread = total_codes // num_threads
    
    # 准备每个线程要尝试的代码范围
    thread_tasks = []
    for i in range(num_threads):
        start_code = i * codes_per_thread
        end_code = (i + 1) * codes_per_thread - 1
        
        # 最后一个线程处理剩余所有代码
        if i == num_threads - 1:
            end_code = total_codes - 1
            
        # 生成该线程负责的所有代码
        codes = list(range(start_code, end_code + 1))
        thread_tasks.append((i, codes))
    
    # 使用线程池执行
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交任务到线程池
        future_to_thread = {
            executor.submit(thread_worker, thread_id, codes): thread_id
            for thread_id, codes in thread_tasks
        }
        
        # 等待第一个成功的结果
        try:
            for future in as_completed(future_to_thread):
                result = future.result()
                if result is not None:
                    # 找到正确签到码，设置全局停止标志
                    global_stop_event.set()
                    
                    # 取消其他未完成的任务
                    for f in future_to_thread:
                        if not f.done():
                            f.cancel()
                    break
        except Exception as e:
            print(f"线程池执行异常: {e}")
    
    t01 = time.time()
    
    # 处理结果
    if found_code[0]:
        print(f"🎉 签到成功! 签到码: {found_code[0]}")
        print(f"⏱️  总用时: {t01 - t00:.2f} 秒")
        
        # 记录成功的签到
        try:
            recorder = CheckinRecorder()
            recorder.add_record(
                course_name=course_name or "未知课程",
                course_id=course_id,
                rollcall_id=str(rollcall_id),
                checkin_code=found_code[0],
                checkin_type="数字签到",
                success=True
            )
        except Exception as e:
            print(f"[记录器] 记录签到信息时出错: {str(e)}")
        
        return True
    else:
        print(f"❌ 签到失败")
        print(f"⏱️  总用时: {t01 - t00:.2f} 秒")
        
        # 记录失败的签到
        try:
            recorder = CheckinRecorder()
            recorder.add_record(
                course_name=course_name or "未知课程",
                course_id=course_id,
                rollcall_id=str(rollcall_id),
                checkin_code=None,
                checkin_type="数字签到",
                success=False
            )
        except Exception as e:
            print(f"[记录器] 记录签到信息时出错: {str(e)}")
        
        return False