from pydantic import BaseModel
from datetime import datetime

class SendEmailConfigPayload(BaseModel):
    design_name: str
    html_email_design: str
    subject: str
    preview: str
    from_data: str
    tracking: str
    send_date: str


class AIRequest(BaseModel):
    message: str


class SendEmailPayload(BaseModel):
    design_name: str
    html_email_design: str
    subject: str
    preview: str
    from_data: str
    tracking: str
    send_date: str


class CampaignScheduleIn(BaseModel):
    design_name: str
    from_data: str
    html_email_design: str
    preview: str
    tracking: str
    subject: str
    send_date: datetime

class CampaignScheduleOut(CampaignScheduleIn):
    id: str