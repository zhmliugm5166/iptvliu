import requests

# ===== 从远程 M3U 文件动态读取频道 =====
SOURCE_URL = "https://raw.githubusercontent.com/zilong7728/Collect-IPTV/refs/heads/main/best_sorted.m3u"

def parse_m3u(text):
    channels = []
    lines = text.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            name = ""
            group = "未分类"
            # 解析 tvg-name
            if 'tvg-name="' in line:
                name = line.split('tvg-name="')[1].split('"')[0]
            # 解析 group-title
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            # 如果没有 tvg-name，用逗号后面的部分
            if not name and "," in line:
                name = line.split(",", 1)[-1].strip()
            # 下一行是流地址
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                if url and not url.startswith("#"):
                    channels.append({"name": name, "group": group, "urls": [url]})
                    i += 2
                    continue
        i += 1
    return channels

def check(url):
    try:
        r = requests.get(url, timeout=5, stream=True)
        return r.status_code == 200
    except:
        return False

print("正在下载频道源...")
try:
    resp = requests.get(SOURCE_URL, timeout=15)
    resp.encoding = "utf-8"
    CHANNELS = parse_m3u(resp.text)
    print(f"共解析到 {len(CHANNELS)} 个频道，开始检测...")
except Exception as e:
    print(f"下载失败：{e}")
    CHANNELS = []

lines = ["#EXTM3U\n"]
valid = 0
for ch in CHANNELS:
    ok_url = next((u for u in ch["urls"] if check(u)), None)
    if ok_url:
        valid += 1
        lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}\n')
        lines.append(ok_url + "\n\n")
        print(f"✅ {ch['name']}")
    else:
        print(f"❌ {ch['name']} 无可用源")

with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"\n完成！有效频道：{valid} / {len(CHANNELS)}")
