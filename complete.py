import time
from datetime import datetime
import os
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
    crawler = Crawler.create_from_cookies(COOKIE_FILE)
    sparser = Sparser()
    
    todo_client = MicrosoftTodoClient.from_config_file(ms_graph_config)
    token = todo_client.load_token_cache(token_cache_file)
    if token:
        todo_client.save_token_cache(token_cache_file)
        todo_client.get_todo_lists()
        homework_list_id = todo_client.get_list_id('Homeworks')
    else:
        print("获取访问令牌失败")
    
    for n in sparser.homeworks:
        if n.end < datetime.now():
            print(f"作业已过期!\n")
            continue
        # 添加任务到 Microsoft To Do
        todo_client.add_task(homework_list_id, n.task.title, n.task.due_date, n.task.reminder_time)