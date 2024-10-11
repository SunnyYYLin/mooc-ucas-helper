# File: mooc/task_manager.py

import json
import logging
import os
from ms_todo.client import MicrosoftTodoClient

class Task:
    def __init__(self, title, due_date=None, reminder_time=None) -> None:
        self.title = title
        self.due_date = due_date
        self.reminder_time = reminder_time
        
    def __str__(self) -> str:
        return f"标题: {self.title}\n截止时间: {self.due_date}\n提醒时间: {self.reminder_time}"

class TaskManager:
    def __init__(self, config_file, token_cache_file, local_task_file='data/tasks.json', homework_list_name="Homeworks"):
        """
        初始化 TaskManager。
        
        :param config_file: Microsoft To Do API 的配置文件路径。
        :param token_cache_file: Microsoft To Do 令牌缓存文件路径。
        :param local_task_file: 本地任务缓存文件，用于保存任务状态。
        :param homework_list_name: 要管理的 To Do 列表名称。
        """
        self.todo_client = MicrosoftTodoClient.from_config_file(config_file)
        self.token_cache_file = token_cache_file
        self.local_task_file = local_task_file
        self.homework_list_name = homework_list_name
        self.homework_list_id = None
        self.local_tasks = {}  # 本地任务缓存

        self._initialize_client()
        self._load_local_tasks()

    def _initialize_client(self):
        """
        初始化 Microsoft To Do 客户端，获取访问令牌并获取作业列表 ID。
        """
        logging.info("Initializing Microsoft To Do client...")
        token = self.todo_client.load_token_cache(self.token_cache_file)

        if not token:
            logging.warning("Token cache is empty. Please authorize the application.")
            token = self.todo_client.get_access_token()
            if not token:
                raise RuntimeError("Failed to get access token. Authorization required.")
        
        self.todo_client.save_token_cache(self.token_cache_file)
        self.todo_client.get_todo_lists()
        self.homework_list_id = self.todo_client.get_list_id(self.homework_list_name)
        if not self.homework_list_id:
            raise ValueError(f"Could not find or create a list named '{self.homework_list_name}'.")

    def _load_local_tasks(self):
        """
        从本地文件加载任务数据。
        """
        try:
            with open(self.local_task_file, 'r') as f:
                self.local_tasks = json.load(f)
                logging.info(f"Loaded {len(self.local_tasks)} tasks from local cache.")
        except FileNotFoundError:
            logging.warning(f"Local task file '{self.local_task_file}' not found. Starting with an empty task list.")
            self.local_tasks = {}
        except json.JSONDecodeError:
            logging.error("Failed to decode local task file. Starting with an empty task list.")
            self.local_tasks = {}

    def save_local_tasks(self):
        """
        将当前的任务状态保存到本地文件。
        """
        with open(self.local_task_file, 'w') as f:
            json.dump(self.local_tasks, f, ensure_ascii=False, indent=4)
            logging.info(f"Saved {len(self.local_tasks)} tasks to local cache.")

    def sync_tasks(self):
        """
        同步本地任务与 Microsoft To Do 中的任务列表，仅处理以下情况：
        1. 本地有、远程没有 -> 需添加到 Microsoft To Do
        """
        logging.info("Starting task synchronization...")
        remote_tasks = self.get_homework_tasks()
        remote_task_titles = {task['title'] for task in remote_tasks}

        # 检查本地任务是否需要添加到 Microsoft To Do
        for title, task_data in self.local_tasks.items():
            if title not in remote_task_titles:
                logging.info(f"Adding new task '{title}' to Microsoft To Do.")
                self.add_homework_task(task_data['title'], task_data['due_date'], task_data.get('reminder_time'))

    def add_homework_task(self, title, due_date, reminder_time=None):
        """
        向 Microsoft To Do 中的作业列表添加新作业任务，并更新本地缓存。
        
        :param title: 作业标题
        :param due_date: 任务的截止日期（格式：YYYY-MM-DDTHH:MM:SS）
        :param reminder_time: 可选，任务的提醒时间（格式：YYYY-MM-DDTHH:MM:SS）
        """
        try:
            self.todo_client.add_task(self.homework_list_id, title, due_date, reminder_time)
            logging.info(f"Task '{title}' added to Microsoft To Do successfully.")
        except Exception as e:
            logging.error(f"Failed to add task '{title}' to the homework list: {e}")
            logging.info(f"Reset up the Microsoft To Do client...")
            self._initialize_client()
            os.sleep(5)
            self.add_homework_task(title, due_date, reminder_time)

    def get_homework_tasks(self):
        """
        获取当前 Microsoft To Do 中所有的作业任务。
        
        :return: 返回作业任务列表
        """
        tasks = self.todo_client.get_tasks(self.homework_list_id)
        if tasks:
            logging.info(f"Retrieved {len(tasks)} homework tasks from Microsoft To Do.")
        return tasks

    def find_task_by_title(self, title):
        """
        根据任务标题查找现有任务。

        :param title: 要查找的任务标题
        :return: 任务对象或 None
        """
        tasks = self.get_homework_tasks()
        for task in tasks:
            if task.get('title') == title:
                return task
        return None