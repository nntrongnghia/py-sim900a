from datetime import datetime
from multiprocessing.sharedctypes import Value
import re

class SMS:
    def __init__(self, raw: str):
        self.raw = raw

        status = re.findall(r'\"(REC READ|REC UNREAD)\"', raw)
        if len(status) == 0:
            raise ValueError("No read status in raw data")
        self.is_new = "REC READ" not in status[0]

        self.phone = None
        phone = re.findall(r'READ\",\"([^\"]+)\"', raw)
        if not phone:
            raise ValueError("No phone number in raw data")
        self.phone = phone[0]

        dstr = re.search(r'(\d\d/\d\d/\d\d,\d\d:\d\d)', raw)
        if dstr is None:
            raise ValueError("No date found in raw data")
        self.datetime = datetime.strptime(dstr.group(), "%y/%m/%d,%H:%M")
        
        self.msg = re.findall(r'\d\d\"\n(.*)', raw)[0]
        
        
    def __repr__(self) -> str:
        return f"New: {self.is_new}\nFrom: {self.phone} - {self.datetime}\n{self.msg}"
