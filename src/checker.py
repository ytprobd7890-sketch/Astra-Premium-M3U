import time
import subprocess
import os
import tempfile

def check_url(url, timeout=8, proxy=None, retries=1):
    """
    Check if HLS URL is live using curl (more reliable for SOCKS5 than requests)
    Returns dict: {url, is_live, http_code, size, latency_ms, error}
    """
    for attempt in range(retries + 1):
        start = time.time()
        tmp_file = tempfile.mktemp(suffix=".ts")
        tmp_header = tempfile.mktemp(suffix=".hdr")
        try:
            # Build curl command - limit download to 200KB max for raw TS check, avoid infinite stream
            cmd = ["curl", "-m", str(timeout), "-s", "-L", "-o", tmp_file, "-D", tmp_header, "-w", "%{http_code} %{size_download}", "--max-filesize", "204800"]
            if proxy:
                cmd.extend(["--proxy", proxy])
            cmd.extend(["--connect-timeout", str(min(timeout, 5))])
            cmd.append(url)

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
            out = proc.stdout.strip()
            parts = out.split()
            http_code = 0
            size = 0
            if len(parts) >= 2:
                try:
                    http_code = int(parts[0])
                    size = int(parts[1])
                except:
                    pass

            body = ""
            header_content = ""
            try:
                with open(tmp_file, "r", encoding="utf-8", errors="ignore") as f:
                    body = f.read(8000)
            except:
                pass
            try:
                with open(tmp_header, "r", encoding="utf-8", errors="ignore") as f:
                    header_content = f.read()
            except:
                pass
            try:
                os.remove(tmp_file)
                os.remove(tmp_header)
            except:
                pass

            latency = int((time.time() - start) * 1000)

            is_hls = False
            # Check for HLS playlist
            if http_code == 200 and size > 50:
                if "#EXTM3U" in body or "#EXTINF" in body or ".ts" in body or "#EXT-X-STREAM-INF" in body:
                    if "404 Not Found" not in body[:500] and "<title>404" not in body[:500]:
                        is_hls = True
                # Also consider raw TS stream as live (Astra /play/xxx without index.m3u8 returns raw MPEG-TS)
                # Raw TS has Content-Type: video/MP2T or application/octet-stream and size > 1000
                # Check header for video
                if not is_hls:
                    if size >= 1000 or size >= 188:  # 188 is one TS packet
                        # Check if Content-Type indicates video or octet-stream
                        if "video/MP2T" in header_content or "application/octet-stream" in header_content or "video/mp2t" in header_content.lower():
                            is_hls = True
                        # Or if URL is /play/xxx (raw) and got some data, consider live (Astra raw mode)
                        elif "/play/" in url and size >= 188:
                            # Additional check: not HTML
                            if "<html" not in body[:500].lower():
                                is_hls = True

            return {
                "url": url,
                "is_live": is_hls,
                "http_code": http_code,
                "size": size,
                "latency_ms": latency,
                "error": None if is_hls else f"HTTP {http_code} size {size}",
            }
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            try:
                os.remove(tmp_file)
            except:
                pass
            if attempt == retries:
                return {
                    "url": url,
                    "is_live": False,
                    "http_code": 0,
                    "size": 0,
                    "latency_ms": latency,
                    "error": str(e)[:200],
                }
            time.sleep(0.5)

def check_urls_parallel(urls, timeout=8, workers=50, proxy=None, retries=1, use_proxy_fallback=True):
    """
    Check multiple URLs in parallel using curl
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(check_url, url, timeout, proxy, retries): url for url in urls}
        for fut in as_completed(futs):
            res = fut.result()
            # Fallback to direct if proxy failed and fallback enabled
            if not res['is_live'] and proxy and use_proxy_fallback:
                direct_res = check_url(res['url'], timeout, proxy=None, retries=0)
                if direct_res['is_live']:
                    direct_res['via'] = 'direct_fallback'
                    results.append(direct_res)
                else:
                    res['via'] = 'proxy_failed'
                    results.append(res)
            else:
                res['via'] = 'proxy' if proxy else 'direct'
                results.append(res)
    return results
