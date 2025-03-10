from typing import List
from pydantic import BaseModel, Field


class DailyWorkInfo(BaseModel):
    date: str = Field(description="報告日")
    start_at: str = Field(description="開始時刻")
    end_at: str = Field(description="終了時刻")
    rest_time: str = Field(description="休憩時間")
    work_time: str = Field(description="業務時間")
    work_details: str = Field(description="業務内容")
    notes: List[str] = Field(description="その他")
