# File: main.py

import time
import logging
from datetime import datetime
from mooc.crawler import Crawler
from mooc.sparser import Sparser, Homework
from mooc.task_manager import TaskManager

# 配置文件路径
COOKIE_FILE = "config/cookies.json"
API_KEY_FILE = "config/api_key.txt"
MS_GRAPH_CONFIG = "config/ms_graph.json"
TOKEN_CACHE_FILE = "config/token_cache.json"
LOCAL_TASK_FILE = "data/homeworks.json"
UPDATE_INTERVAL = 10  # (s)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 初始化爬虫、解析器和 TaskManager
    crawler = Crawler.create_from_cookies(COOKIE_FILE)
    sparser = Sparser()
    task_manager = TaskManager(MS_GRAPH_CONFIG, TOKEN_CACHE_FILE, LOCAL_TASK_FILE)

    while True:
        try:
            logging.info("Checking for new notices...")
            notice_list = crawler.get_notice_list()
            new_notices = sparser.filter_new_notices(notice_list)
            
            for ntc in new_notices:
                n = sparser.sparse_notice(ntc)
                if isinstance(n, Homework):
                    logging.info(f"New homework found: \n{n}")
                    if n.end < datetime.now():
                        logging.info(f"Homework has already expired: {n}")
                        continue
                    
                    # 更新本地缓存的作业任务
                    task_title = f"{n.course}: {n.name}"
                    task_manager.local_tasks[task_title] = {
                        "title": task_title,
                        "due_date": n.task.due_date,
                        "reminder_time": n.task.reminder_time
                    }
            task_manager.save_local_tasks()

            # 同步 Microsoft To Do 与本地任务
            logging.info("Synchronizing tasks with Microsoft To Do.")
            task_manager.sync_tasks()

            time.sleep(UPDATE_INTERVAL)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(UPDATE_INTERVAL)