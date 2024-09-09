import time
from datetime import datetime
import os
from bs4 import BeautifulSoup as bs
from pushbullet import PushBullet
from mooc.crawler import Crawler
from mooc.sparser import Sparser, Homework
from ms_todo.client import MicrosoftTodoClient

UPDATE_INTERVAL = 1 # (s)
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
            new_notices = sparser.filter_new_notices(notice_list)
            for ntc in new_notices:
                n = sparser.sparse_notice(ntc)
                if isinstance(n, Homework):
                    print(f"发现新作业: \n{n}")
                    if n.end < datetime.now():
                        print(f"作业已过期!\n")
                        continue
                    todo_client.add_task(homework_list_id, n.task.title, n.task.due_date, n.task.reminder_time)
                device.push_note(n.message.title, n.message.content)
        except ConnectionError as e:
            print(f"出现错误: {e}")
            time.sleep(3)
            crawler = Crawler.create_from_cookies(COOKIE_FILE)