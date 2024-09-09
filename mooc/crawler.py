import requests
from bs4 import BeautifulSoup as bs
import json

class Crawler:
    myspace_url = "https://i.mooc.ucas.edu.cn"
    request_notice_url = "https://notice.mooc.ucas.edu.cn/pc/notice/getNoticeList"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    def __init__(self, session: requests.Session, cookie_file: str):
        self.session = session
        self.cookie_file = cookie_file
        
    @staticmethod
    def create_from_cookies(cookie_file: str) -> 'Crawler':
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
        session = requests.Session()
        session.cookies.update(cookies)
        return Crawler(session, cookie_file)
    
    def save_cookies(self) -> None:
        with open(self.cookie_file, 'w') as f:
            json.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f, indent=4)

    def get_notice_link(self) -> str:
        """
        从个人空间页面获取通知链接
        """
        try:
            response = self.session.get(self.myspace_url, headers=self.headers)
            response.raise_for_status()
            soup = bs(response.text, 'lxml')
            notice_link_tag = soup.find('a', id='zne_tz_icon')
            if notice_link_tag:
                self.notice_link = notice_link_tag['href'].split('\'')[-2]
                return self.notice_link
            else:
                print("未找到通知链接")
                raise ValueError("未找到通知链接")
        except requests.RequestException as e:
            print(f"请求错误: {e}")
            raise ConnectionError(f"请求错误: {e}")
        except Exception as e:
            print(f"解析错误: {e}")
            raise Exception(f"解析错误: {e}")

    def get_notice_list(self) -> list:
        """
        获取通知列表的JSON数据
        """
        self.get_notice_link()
        try:
            self.session.get(self.notice_link, headers=self.headers)
            response = self.session.get(self.request_notice_url, headers=self.headers)
            response.raise_for_status()
            notice_data = response.json()
            return notice_data["notices"]["list"]
        except requests.RequestException as e:
            raise ConnectionError(f"网络请求失败: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            raise TypeError(f"解析JSON失败: {e}")