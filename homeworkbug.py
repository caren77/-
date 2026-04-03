import requests
from bs4 import BeautifulSoup
import time
import os

TARGET_URL = "https://faculty.ustc.edu.cn/flowice/zh_CN/zdylm/679092/list/index.htm"
SEND_KEY = os.environ.get("SERVER_CHAN_KEY") 
CHECK_INTERVAL = 3600  # 每小时检查一次
LAST_CONTENT_FILE = "last_hw_slice.txt"

def send_wechat_notification(title, content):
    if not SEND_KEY:
        print("❌ 错误：SEND_KEY 为空，请检查环境变量！")
        return

    url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        if result.get("code") == 0:
            print("✅ 微信推送成功")
        else:
            print(f"❌ 推送失败，Server酱返回：{result.get('message')}")
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")

def get_homework_slice():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    try:
        res = requests.get(TARGET_URL, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. 抓取整个内容容器（根据你之前看到的编号[0]定位）
        # 如果 list-content 抓不到，可以直接抓 body
        container = soup.find('div', class_='list-content') or soup.find('body')
        full_text = container.get_text(separator="\n", strip=True)

        # 2. 字符串切分逻辑
        start_keyword = "作业布置"
        end_keyword = "重要通知"

        if start_keyword in full_text:
            # 截取“作业布置”之后的部分
            temp_content = full_text.split(start_keyword)[1]
            # 如果存在“重要通知”，则截取它之前的部分
            if end_keyword in temp_content:
                homework_section = temp_content.split(end_keyword)[0]
            else:
                homework_section = temp_content[:1000] # 保险起见截取1000字
            
            return homework_section.strip()
        else:
            print("⚠️ 未能在页面中找到‘作业布置’关键字")
            
    except Exception as e:
        print(f"❌ 抓取异常: {e}")
    return None

def monitor():
    print(f"🔍 正在检查更新：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    current_hw = get_homework_slice()
    
    if current_hw:
        last_hw = ""
        if os.path.exists(LAST_CONTENT_FILE):
            with open(LAST_CONTENT_FILE, "r", encoding="utf-8") as f:
                last_hw = f.read()
        
        if current_hw != last_hw:
            print("✨ 发现更新，正在推送...")
            send_wechat_notification("作业有更新！", current_hw)
            with open(LAST_CONTENT_FILE, "w", encoding="utf-8") as f:
                f.write(current_hw)
        else:
            print("🕒 内容无变化。")

if __name__ == "__main__":
    monitor() # 只跑一次，剩下的交给 GitHub 每 24 小时唤醒一次
