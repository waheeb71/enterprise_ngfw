"""
Time Schedules
Time-based policy enforcement.
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional

@dataclass
class Schedule:
    name: str
    days: List[str]  # Mon, Tue, Wed...
    start_time: time
    end_time: time
    timezone: str = "UTC"

    def is_active(self, current_time: datetime) -> bool:
        # Check Day
        width_day = current_time.strftime("%a")
        if width_day not in self.days:
            return False
            
        # Check Time
        now_time = current_time.time()
        if self.start_time <= self.end_time:
            return self.start_time <= now_time <= self.end_time
        else:
            # Crosses midnight
            return now_time >= self.start_time or now_time <= self.end_time
