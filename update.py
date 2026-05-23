import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== 多个直播源地址，可以继续添加 =====
SOURCE_URLS = [
    "https://raw.githubusercontent.com/zilong7728/Collect-IPTV/refs/heads/main/best_sorted.m3u",
    "https://raw.githubusercontent.com/hujingguang/ChinaIPTV/main/cnTV_AutoUpdate.m3u8",
    "https://raw.githubusercontent.com/dongyubin/IPTV/main/iptv4.m3u",
]
# =========================================

# ===== 配置项 =====
CHECK_TIMEOUT = 5       # 检测每个地址的超时秒数
MAX_WORKERS   = 20      # 并发检测线程数
OUTPUT_FILE   = "playlist.m3u"
# ==================


def fetch_m3u(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = "utf-8"
        print(f"  ✅ 下载成功：{url}  ({len(resp.text)} 字节)")
        return resp.text
    except Exception as e:
        print(f"  ❌ 下载失败：{url}  原因：{e}")
        return ""


def parse_m3u(text):
    channels = []
    lines = text.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            name  = ""
            group = "未分类"
            if 'tvg-name="' in line:
                name = line.split('tvg-name="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if not name and "," in line:
                name = line.split(",", 1)[-1].strip()
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                if url and not url.startswith("#"):
                    channels.append({
                        "name":  name or "未知频道",
                        "group": group,
                        "url":   url,
                    })
                    i += 2
                    continue
        i += 1
    return channels


def check(url):
    try:
        r = requests.get(url, timeout=CHECK_TIMEOUT, stream=True)
        return r.status_code == 200
    except:
        return False


def check_all(channels):
    valid = []
    total = len(channels)
    done  = 0

    def task(ch):
        ok = check(ch["url"])
        return ch, ok

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(task, ch): ch for ch in channels}
        for future in as_completed(futures):
            ch, ok = future.result()
            done += 1
            if ok:
                valid.append(ch)
                print(f"  [{done}/{total}] ✅ {ch['name']}")
            else:
                print(f"  [{done}/{total}] ❌ {ch['name']}")

    return valid


def deduplicate(channels):
    seen = set()
    result = []
    for ch in channels:
        if ch["url"] not in seen:
            seen.add(ch["url"])
            result.append(ch)
    return result


def save_m3u(channels, path):
    lines = ["#EXTM3U\n"]
    for ch in sorted(channels, key=lambda x: x["group"]):
        lines.append(
            f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}\n'
        )
        lines.append(ch["url"] + "\n\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ===== 主流程 =====
print("=" * 50)
print("第1步：下载所有直播源")
print("=" * 50)
all_channels = []
for url in SOURCE_URLS:
    text = fetch_m3u(url)
    parsed = parse_m3u(text)
    print(f"       解析到 {len(parsed)} 个频道")
    all_channels.extend(parsed)

print(f"\n合计：{len(all_channels)} 个频道（含重复）")

print("\n" + "=" * 50)
print("第2步：去除重复地址")
print("=" * 50)
unique = deduplicate(all_channels)
print(f"去重后剩余：{len(unique)} 个频道")

print("\n" + "=" * 50)
print("第3步：并发检测有效性（可能需要几分钟）")
print("=" * 50)
valid = check_all(unique)

print("\n" + "=" * 50)
print("第4步：保存结果")
print("=" * 50)
save_m3u(valid, OUTPUT_FILE)
print(f"✅ 完成！有效频道：{len(valid)} / {len(unique)}")
print(f"   已保存到：{OUTPUT_FILE}")
