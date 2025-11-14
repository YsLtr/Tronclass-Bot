import time
from login import login
from misc import c, a

interval = 1
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
base_url = "https://lnt.xmu.edu.cn"

rollcalls_url = f"{base_url}/api/radar/rollcalls"
c()

print("Welcome to XMU Rollcall Bot CLI!\nLogging you in...")
session = login()
if not session:
    exit(1)

temp_data = {'rollcalls': []}
query_count = 0
while True:
    c()
    print("XMU Rollcall Bot CLI is running...")
    print(f"Local time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    print(f"Query count: {query_count}")
    time.sleep(interval)
    try:
        data = session.get(rollcalls_url, headers=headers).json()
        query_count += 1
        if temp_data == data:
            continue
        else:
            temp_data = data
            if len(temp_data['rollcalls']) > 0:
                temp_data = a(temp_data, session)
    except Exception as e:
        print("An error occurred:", str(e))
        exit(1)
