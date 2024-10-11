# File: complete.py

import logging
from datetime import datetime
from mooc.sparser import Sparser
from mooc.task_manager import TaskManager

# 配置文件路径
MS_GRAPH_CONFIG = "config/ms_graph.json"
TOKEN_CACHE_FILE = "config/token_cache.json"
LOCAL_TASK_FILE = "data/tasks.json"
COOKIE_FILE = "config/cookies.json"

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 初始化 TaskManager
    task_manager = TaskManager(MS_GRAPH_CONFIG, TOKEN_CACHE_FILE, LOCAL_TASK_FILE)
    
    # 初始化 Sparser
    sparser = Sparser()

    # 检查作业状态
    for homework in sparser.homeworks:
        if homework.end < datetime.now():
            logging.info(f"作业已过期: {homework.name}")
            continue

        # 检查是否需要添加作业到 Microsoft To Do
        task_title = f"{homework.course}: {homework.name}"
        if not task_manager.find_task_by_title(task_title):
            task_manager.add_homework_task(task_title, homework.task.due_date, homework.task.reminder_time)

    # 保存本地任务状态
    task_manager._save_local_tasks()