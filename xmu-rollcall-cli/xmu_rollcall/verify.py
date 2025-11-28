import uuid
import time
import asyncio
import aiohttp

base_url = "https://lnt.xmu.edu.cn"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://ids.xmu.edu.cn/authserver/login",
}

LATITUDE = ""
LONGITUDE = ""

def set_location(lat, lon):
    """设置全局位置信息"""
    global LATITUDE, LONGITUDE
    LATITUDE = lat
    LONGITUDE = lon

def pad(i):
    return str(i).zfill(4)

def send_code(in_session, rollcall_id):
    """发送数字签到码"""
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    print("Trying number code...")
    t00 = time.time()

    async def put_request(i, session, stop_flag, answer_url, sem, timeout):
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
                async with session.put(answer_url, json=payload) as r:
                    if r.status == 200:
                        stop_flag.set()
                        return pad(i)
            except Exception:
                pass
            return None

    async def main():
        stop_flag = asyncio.Event()
        cookies = {cookie.name: cookie.value for cookie in in_session.cookies}
        connector = aiohttp.TCPConnector(limit=800)
        timeout = aiohttp.ClientTimeout(total=30)
        sem = asyncio.Semaphore(800)

        async with aiohttp.ClientSession(
            connector=connector,
            cookies=cookies,
            headers=headers,
            timeout=timeout
        ) as session:
            tasks = [put_request(i, session, stop_flag, url, sem, timeout) for i in range(10000)]
            results = await asyncio.gather(*tasks)
            for result in results:
                if result:
                    print(f"Success! Code: {result}, Time elapsed: {time.time() - t00:.2f}s")
                    return True
        return False

    try:
        return asyncio.run(main())
    except Exception as e:
        print(f"Error in send_code: {e}")
        return False

def send_radar(in_session, rollcall_id):
    """发送雷达签到"""
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer_radar_rollcall"
    print("Trying radar rollcall...")

    payload = {
        "accuracy": 35,
        "altitude": 0,
        "altitudeAccuracy": None,
        "deviceId": str(uuid.uuid4()),
        "heading": None,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "speed": None
    }

    try:
        response = in_session.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Radar rollcall success!")
            return True
        else:
            print(f"Radar rollcall failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error in send_radar: {e}")
        return False

