"""ticktick api client"""
import datetime
import json
from typing import Dict
from jsonpath_ng.ext import parse

import requests

from .const import ADD_TASK_URL, AUTH_URL, PROJECT_URL, TICKTICK_HOST


class TickTick:
    """Simple TickTick API Client"""

    _session: requests.Session

    def __init__(self):
        self._session = requests.Session()
        self._session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        }

    def login(self, username: str, password: str):
        """Log into ticktick api. ValueError is thrown when credentials are incorrect"""
        resp = self._session.post(
            f"https://{TICKTICK_HOST}{AUTH_URL}",
            json={
                "username": username,
                "password": password,
            },
            headers={
                "x-device": json.dumps(
                    {
                        "platform": "web",
                        "os": "macOS 10.15.7",
                        "device": "Chrome 92.0.4515.107",
                        "name": "",
                        "version": 3925,
                        "id": "60fdb7be711f1b6380240d3a",
                        "channel": "website",
                        "campaign": "",
                        "websocket": "",
                    }
                ),
            },
        )
        if resp.status_code != 200:
            raise ValueError("Invalid credentials")

    @staticmethod
    def datetime_to_json(dt: datetime.datetime) -> str:
        """Convert datetime object to string for TickTick"""
        # Example format: 2019-12-20T23:00:00.000+0000
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")

    def get_projects(self) -> Dict[str, str]:
        """Return a dict of all project IDs and their names"""
        resp = self._session.get(f"https://{TICKTICK_HOST}{PROJECT_URL}")
        projects = {}
        for raw_project in resp.json().get("projectProfiles"):
            projects[raw_project.get("id")] = raw_project.get("name")
        return projects

    def get_today_tasks(self) -> list:
        """Return a list of dict for all tasks due today Title and Priority"""
        resp = self._session.get(f"https://{TICKTICK_HOST}{PROJECT_URL}")
        tasks = []
        # Due date is today at midnight local time, converting to UTC
        # and converting to datetime_to_json for ticktick format
        tz_local = datetime.datetime.now().astimezone().tzinfo
        today_utc = datetime.datetime.combine(datetime.date.today(), datetime.time(), tz_local).astimezone(datetime.timezone.utc)
        print(today_utc)
        today_ticktick_format = TickTick.datetime_to_json(today_utc)
        print(today_ticktick_format)
        # Filter TickTick data to up to date tasks
        #FIXME: may miss some task being updated?
        jsonpath_expr = parse('$.syncTaskBean.update[?(@.dueDate=="'+today_ticktick_format+'")]') 
        for raw_task_today in jsonpath_expr.find(resp.json()):
            atask = {} # dict
            atask['title'] = raw_task_today.value['title']
            atask['priority'] = raw_task_today.value['priority']
            tasks.append(atask)
        return tasks

    def add_task(
        self,
        task_title: str,
        content: str = "",
        project: str = "",
        due_date: datetime.datetime = None,
    ) -> bool:
        # Create Task
        data = {
            "sortOrder": 1,
            "title": task_title,
            "content": content,
            "projectId": project,
        }
        if due_date:
            data["dueDate"] = TickTick.datetime_to_json(due_date)
        resp = self._session.post(f"https://{TICKTICK_HOST}{ADD_TASK_URL}", json=data)
        if resp.status_code == 200:
            return True
        return False
