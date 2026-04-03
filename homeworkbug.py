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
    print("="*30)
    print(f"🔍 正在监控：[{TARGET_URL}]")
    print("🎯 目标区域：'作业布置' 与 '重要通知' 之间")
    print("="*30)

    while True:
        current_hw = get_homework_slice()
        
        if current_hw:
            # 读取旧记录
            last_hw = ""
            if os.path.exists(LAST_CONTENT_FILE):
                with open(LAST_CONTENT_FILE, "r", encoding="utf-8") as f:
                    last_hw = f.read()
            
            # 对比内容
            if current_hw != last_hw:
                print(f"\n✨ 【内容更新】 {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 20)
                print(current_hw)
                print("-" * 20)
                
                # 推送微信
                send_wechat_notification("作业板块有更新！", f"最新内容：\n{current_hw}")
                
                # 更新本地文件
                with open(LAST_CONTENT_FILE, "w", encoding="utf-8") as f:
                    f.write(current_hw)
            else:
                print(f"\r🕒 轮询中... 上次检查: {time.strftime('%H:%M:%S')} (未发现更新)", end="")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
