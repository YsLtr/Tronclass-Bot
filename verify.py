import uuid
import requests
import json
import time
import asyncio
import aiohttp

def pad(i):
    return str(i).zfill(4)

def send_code(rollcall_id, verified_cookies):
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies = verified_cookies
    print("正在遍历签到码...")
    t00 = time.time()

    async def put_request(i, session, stop_flag, url, headers, sem):
        async with sem:
            if stop_flag.is_set():
                return None
            payload = {
                "deviceId": str(uuid.uuid4()),
                "numberCode": pad(i)
            }
            try:
                async with session.put(url, json=payload, timeout=5) as r:
                    if r.status == 200:
                        stop_flag.set()
                        return pad(i)
            except Exception:
                pass
            return None

    async def main():
        jar = aiohttp.CookieJar()
        for k, v in cookies.items():
            jar.update_cookies({k: v})
        stop_flag = asyncio.Event()
        sem = asyncio.Semaphore(200)  # 并发量，待调试
        async with aiohttp.ClientSession(headers=headers, cookie_jar=jar) as session:
            tasks = [put_request(i, session, stop_flag, url, headers, sem) for i in range(10000)]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                if res is not None:
                    for t in tasks:
                        t.cancel()
                    print("签到码:", res)
                    t01 = time.time()
                    print("用时: %.2f 秒" % (t01 - t00))
                    return True
        t01 = time.time()
        print("失败。\n用时: %.2f 秒" % (t01 - t00))
        return False

    return asyncio.run(main())

def send_radar(rollcall_id, verified_cookies):
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer?api_version=1.76"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "accuracy": 35,
        "altitude": 0,
        "altitudeAccuracy": None,
        "deviceId": str(uuid.uuid4()),
        "heading": None,
        "latitude": 24.4378,
        "longitude": 118.0965,  # 庄汉水楼，后续会加入更多位置，目前只用得到这个
        "speed": None
    }
    res = requests.put(url, json=payload, headers=headers, cookies=verified_cookies)
    if res.status_code == 200:
        return True
    return False
