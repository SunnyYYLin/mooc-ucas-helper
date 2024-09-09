import os
import json
from datetime import datetime, timedelta

class Message:
    def __init__(self, title, content) -> None:
        self.title = title
        self.content = content

class Task:
    def __init__(self, title, due_date=None, reminder_time=None) -> None:
        self.title = title
        self.due_date = due_date
        self.reminder_time = reminder_time

class Notice:
    ACC_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, title: str, content: str, creater: str, time: str):
        """
        初始化 Notice 对象
        :param title: 通知标题
        :param content: 通知内容
        :param creater: 通知创建者
        :param time: 通知完成时间
        """
        self.title = title
        self.content = content
        self.creater = creater
        self.time = datetime.strptime(time, self.ACC_DATE_FORMAT)

    def __str__(self):
        return (
            f"标题: {self.title}\n"
            f"内容: {self.content}\n"
            f"创建者: {self.creater}\n"
            f"时间: {self.time.strftime(self.ACC_DATE_FORMAT)}\n"
        )
        
    @property
    def message(self) -> Message:
        """
        返回通知简要描述，方便推送内容
        """
        return Message(self.title, self.content)

    def to_dict(self):
        """
        将 Notice 对象转换为字典
        """
        return {
            'title': self.title,
            'content': self.content,
            'creater': self.creater,
            'time': self.time.strftime(self.ACC_DATE_FORMAT)
        }

    @staticmethod
    def from_dict(data: dict):
        """
        从字典数据创建 Notice 对象
        """
        return Notice(
            title=data['title'],
            content=data['content'],
            creater=data['creater'],
            time=data['time']
        )

class Homework:
    DATE_FORMAT = "%Y-%m-%d %H:%M"
    DUE_FORMAT = "%Y-%m-%d"

    def __init__(self, course: str, name: str, start: str, end: str):
        self.course = course
        self.name = name
        self.start = datetime.strptime(start, self.DATE_FORMAT)
        self.end = datetime.strptime(end, self.DATE_FORMAT)

    def __str__(self):
        return (
            f"课程: {self.course}\n"
            f"作业: {self.name}\n"
            f"开始时间: {self.start.strftime(self.DATE_FORMAT)}\n"
            f"结束时间: {self.end.strftime(self.DATE_FORMAT)}\n"
        )

    @property
    def message(self) -> Message:
        """
        返回作业简要描述，方便推送内容
        """
        return Message(f"{self.course}：{self.name}",
                       f"{self.start.strftime(self.DATE_FORMAT)} -> \
                       {self.end.strftime(self.DATE_FORMAT)}")
        
    @property
    def task(self) -> Task:
        reminder_time = self.end - timedelta(days=1)
        reminder_time = reminder_time.replace(hour=20, minute=0, second=0)
        end = self.end.replace(hour=0, minute=0, second=0)
        return Task(f"{self.course}：{self.name}", end.strftime(self.DUE_FORMAT), reminder_time.strftime(self.DATE_FORMAT))

    def to_dict(self):
        """
        将对象转化为字典，方便序列化为 JSON
        """
        return {
            'course': self.course,
            'name': self.name,
            'start': self.start.strftime(self.DATE_FORMAT),
            'end': self.end.strftime(self.DATE_FORMAT),
        }
        
    @staticmethod
    def from_dict(data: dict) -> "Homework":
        """
        从字典创建 Homework 对象
        """
        return Homework(
            course=data['course'],
            name=data['name'],
            start=data['start'],
            end=data['end']
        )
        
    def to_json(self):
        """
        将对象转化为 JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)

class Sparser:
    DATE_FORMAT = "%Y-%m-%d %H:%M"
    ACC_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, 
                 homework_file: str = os.path.join("data", "homeworks.json"), 
                 uuid_file: str = os.path.join("data", "uuids.json")
                 ):
        self.homework_file = homework_file
        self.uuid_file = uuid_file
        self.homeworks = self._load_homeworks()
        self.uuids = self._load_uuids()
        
    def _load_uuids(self) -> list:
        """
        加载UUID数据
        """
        with open(self.uuid_file, 'r') as f:
            return json.load(f)
        
    def _load_homeworks(self) -> list:
        """
        加载作业数据
        """
        with open(self.homework_file, 'r') as f:
            homeworks = json.load(f)
        return [Homework.from_dict(hw) for hw in homeworks]

    def _update_homeworks(self, hw: Homework) -> None:
        """
        更新内部的homeworks数据并保存到文件
        """
        self.homeworks.append(hw)
        hw_json = [hw.to_dict() for hw in self.homeworks]
        with open(self.homework_file, 'w') as f:
            json.dump(hw_json, f, ensure_ascii=False, indent=4)
            
    def _update_uuids(self, current_uuids: list) -> None:
        """
        更新内部的UUID数据并保存到文件
        """
        self.uuids = current_uuids
        with open(self.uuid_file, 'w') as f:
            json.dump(self.uuids, f, ensure_ascii=False, indent=4)

    def parse_homework_notice(self, notice: dict) -> Homework:
        """
        解析作业通知并返回 Homework 对象
        """
        content = notice["content"].split('\r')
        course = content[0].removeprefix("课程名称：")
        name = content[1].removeprefix("作业名称：")
        start = content[2].removeprefix("开始时间：")
        end = content[3].removeprefix("结束时间：")

        # 创建 Homework 对象
        homework = Homework(course, name, start, end)

        # 更新作业列表并保存
        self._update_homeworks(homework)

        return homework

    def parse_general_notice(self, notice: dict) -> Notice:
        """
        解析普通通知并返回 Notice 对象
        """
        title = notice["title"]
        content = notice["content"]
        creater = notice["createrName"]
        time = notice["completeTime"]

        return Notice(title=title, content=content, creater=creater, time=time)

    def sparse_notice(self, notice: dict) -> dict:
        """
        根据通知类型选择相应的解析方式
        """
        if notice["title"].startswith("作业:"):
            return self.parse_homework_notice(notice)
        else:
            return self.parse_general_notice(notice)

    def filter_new_notices(self, notice_list: list) -> list:
        """
        过滤出新的通知（即不在当前UUID列表中的通知）
        """
        current_uuids = [notice['uuid'] for notice in notice_list]
        new_uuids = list(set(current_uuids) - set(self.uuids))

        if new_uuids:
            self._update_uuids(current_uuids)
            return [notice for notice in notice_list if notice['uuid'] in new_uuids]
        else:
            return []