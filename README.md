# 高性能版本

### 最后一次更新时间: *2025-11-04*

使用方法在 [这里](quickstart.md)

纯净的 CLI 版本，极致的高性能。

此分支在 `verify.py` 中使用 `aiohttp` 替代 `requests` 进行异步 HTTP 请求，以提升网络操作的效率和响应速度。

运行 `main.py` 即可使用：

```bash     
python main.py
```