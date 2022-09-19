from datetime import datetime
from threading import Lock


class MessageIndexer(object):
    def __init__(self) -> None:
        self.locker = Lock()
        self.last_time_index = 0
        self.max_id = 400

    def get_index(self, id: int = 0) -> int:
        current_time_index = (datetime.now() - datetime.today()).total_seconds() * 1000
        self.locker.acquire()
        if current_time_index <= self.last_time_index:
            current_time_index = self.last_time_index + 1
        self.last_time_index = current_time_index
        self.locker.release()
        return self.max_id * current_time_index + id
