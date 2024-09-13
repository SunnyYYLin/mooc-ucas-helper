import time
from datetime import datetime
import os
from bs4 import BeautifulSoup as bs
from pushbullet import PushBullet
from mooc.crawler import Crawler
from mooc.sparser import Sparser, Homework
from ms_todo.client import MicrosoftTodoClient

UPDATE_INTERVAL = 60 # (s)
COOKIE_FILE = os.path.join("config", "cookies.json")

if __name__ == '__main__':
    with open(os.path.join("config", "api_key.txt"), 'r') as f:
        api_key = f.read()
    ms_graph_config = os.path.join("config", "ms_graph.json")
    token_cache_file = os.path.join("config", "token_cache.json")
    pb = PushBullet(api_key)
    device = pb.devices[0]
    crawler = Crawler.create_from_cookies(COOKIE_FILE)
    sparser = Sparser()
    stuck_tasks = []
    
    # Microsoft To Do API
    todo_client = MicrosoftTodoClient.from_config_file(ms_graph_config)
    token = todo_client.load_token_cache(token_cache_file)
    if token:
        todo_client.save_token_cache(token_cache_file)
        todo_client.get_todo_lists()
        homework_list_id = todo_client.get_list_id('Homeworks')
    else:
        print("获取访问令牌失败")
    
    while True:
        try:
            time.sleep(UPDATE_INTERVAL)
            notice_list = crawler.get_notice_list()
            if notice_list:
                print(f"[{datetime.now()}]获取到通知列表: {len(notice_list)} 条")
            new_notices = sparser.filter_new_notices(notice_list)
            for ntc in new_notices:
                n = sparser.sparse_notice(ntc)
                if isinstance(n, Homework):
                    print(f"发现新作业: \n{n}")
                    if n.end < datetime.now():
                        print(f"作业已过期!\n")
                        continue
                    # 添加任务到 Microsoft To Do
                    try:
                        todo_client.add_task(homework_list_id, n.task.title, n.task.due_date, n.task.reminder_time)
                    except Exception as e:
                        print(f"添加任务失败: {e}")
                        device.push_note("Error", f"Failed to add task: {e}")
                        stuck_tasks.append(n.task)
                # 推送通知
                device.push_note(n.message.title, n.message.content)
            
            # 尝试添加之前失败的任务
            if stuck_tasks:
                for task in stuck_tasks:
                    try:
                        print(f"尝试添加任务: {task}")
                        todo_client.add_task(homework_list_id, task.title, task.due_date, task.reminder_time)
                        stuck_tasks.remove(task)
                    except Exception as e:
                        print(f"添加任务失败: {e}")
                        device.push_note("Error", f"Failed to add task: {e}")
        except ConnectionError as e:
            print(f"出现错误: {e}")
            time.sleep(3)
            crawler = Crawler.create_from_cookies(COOKIE_FILE)
        finally:
            device.push_note("Error", "An error occurred")