import json
import requests
import msal

class MicrosoftTodoClient:
    def __init__(self, client_id, client_secret, authority, scopes):
        """
        初始化 Microsoft Graph API 客户端应用程序。
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = authority
        self.scopes = scopes
        self.app = self.create_msal_app()
        self.access_token = None

    def create_msal_app(self):
        """
        创建 MSAL 的 ConfidentialClientApplication 实例。
        """
        self.token_cache = msal.SerializableTokenCache()
        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            token_cache=self.token_cache
        )

    @staticmethod
    def from_config_file(config_file):
        """
        从配置文件创建 MicrosoftTodoClient 实例。
        :param config_file: 配置文件路径
        :return: MicrosoftTodoClient 实例
        """
        with open(config_file, 'r') as f:
            parameters = json.load(f)
        
        client_id = parameters['client_id']
        client_secret = parameters['secret']
        authority = parameters['authority']
        scopes = parameters['scopes']
        
        return MicrosoftTodoClient(client_id, client_secret, authority, scopes)

    def get_access_token(self):
        """
        获取访问令牌，提示用户进行授权并返回访问令牌。
        """
        auth_url = self.app.get_authorization_request_url(scopes=self.scopes)
        print(f"请访问此 URL 并授权应用程序: {auth_url}")
        authorization_code = input("输入授权码: ")

        try:
            token_response = self.app.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=self.scopes
            )
            self.access_token = token_response.get('access_token')
        except Exception as e:
            print(f"获取访问令牌时出错: {e}")
            return None

        return self.access_token
    
    def save_token_cache(self, file_path):
        """
        将令牌缓存保存到文件。
        :param file_path: 保存令牌缓存的文件路径
        """
        with open(file_path, 'w') as f:
            f.write(self.token_cache.serialize())
            
    def load_token_cache(self, file_path):
        """
        从文件加载令牌缓存。
        :param file_path: 保存令牌缓存的文件路径
        """
        with open(file_path, 'r') as f:
            self.token_cache.deserialize(f.read())
        accounts = self.app.get_accounts()
        token_response = self.app.acquire_token_silent(self.scopes, account=accounts[0])
        self.access_token = token_response.get('access_token')
        return self.access_token

    def get_todo_lists(self):
        """
        获取当前用户的 Microsoft To Do 列表。
        """
        if not self.access_token:
            print("无效的访问令牌。")
            return None

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get("https://graph.microsoft.com/v1.0/me/todo/lists", headers=headers)

        if response.status_code == 200:
            self.todo_lists = response.json()
            return self.todo_lists
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None

    def get_list_id(self, search_term):
        """
        根据搜索词查找 To Do 列表并返回第一个匹配的列表 ID。
        :param search_term: 部分或全部列表名称
        :return: 匹配的列表的 ID 或 None
        """
        if not hasattr(self, 'todo_lists') or not self.todo_lists:
            print("无法获取 To Do 列表")
            return None

        # 遍历查找列表名称包含搜索词的列表
        for todo_list in self.todo_lists.get('value', []):
            if search_term.lower() in todo_list.get('displayName').lower():
                print(f"找到匹配的列表: {todo_list.get('displayName')}")
                return todo_list.get('id')

        print(f"未找到包含 '{search_term}' 的列表")
        return None

    def add_task(self, list_id, title, due_date=None, reminder_time=None):
        """
        向指定的 To Do 列表添加一个新任务。
        :param list_id: To Do 列表的 ID
        :param title: 任务的标题
        :param due_date: 任务的截止日期时间，格式为 'YYYY-MM-DDTHH:MM:SS', 默认为明天
        :param reminder_time: 可选，任务的提醒时间，格式为 'YYYY-MM-DDTHH:MM:SS'
        """
        if not hasattr(self, 'todo_lists') or not self.todo_lists:
            print("无法获取 To Do 列表")
            return None
        
        # 查找匹配的列表名称
        list_name = None
        for todo_list in self.todo_lists.get('value', []):
            if todo_list.get('id') == list_id:
                list_name = todo_list.get('displayName')
                break

        if not list_name:
            print("未找到对应的列表名称")
            return None

        # 准备任务数据
        task_data = {
            "title": title
        }
        
        if due_date:
            task_data["dueDateTime"] = {
                "dateTime": due_date,
                "timeZone": "UTC"
            }

        if reminder_time:
            task_data["reminderDateTime"] = {
                "dateTime": reminder_time,
                "timeZone": "UTC"
            }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # 向 Microsoft To Do API 发送 POST 请求，添加任务
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
        response = requests.post(url, headers=headers, json=task_data)

        if response.status_code == 201:
            print(f"Successfully added task '{title}' to list '{list_name}'.")
            return response.json()
        else:
            print(f"Failed to add task. Status code: {response.status_code}")
            return None

# 使用示例
if __name__ == '__main__':
    # 从配置文件创建 MicrosoftTodoClient 实例
    todo_client = MicrosoftTodoClient.from_config_file('config/ms_graph.json')

    # 获取访问令牌
    token = todo_client.load_token_cache('config/token_cache.json')

    if token:
        # 获取 Homeworks 列表的 ID
        todo_client.save_token_cache('config/token_cache.json')
        todo_client.get_todo_lists()
        homework_list_id = todo_client.get_list_id('Homeworks')

        if homework_list_id:
            # 向 Homeworks 列表添加一个新的作业
            todo_client.add_task(homework_list_id, title="Test Homework")
    else:
        print("获取访问令牌失败")
