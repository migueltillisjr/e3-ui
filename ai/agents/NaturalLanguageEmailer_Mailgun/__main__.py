from .entrypoint import initiate_email_send
from . import get_metrics
import sys
import json


if __name__ == '__main__':
    DOMAIN="e3.hawaiiapsi.org"
    kwargs = {
        "design_name": "email_design1.html",
        "html_email_design": "https://e3-designs.s3.amazonaws.com/email_design1.html",
        "subject": "This is a test!",
        "preview": "This is a test!",
        "from_data": "Jennie < jennie@e3.hawaiiapsi.org >",
        "tracking": "yes",
        "send_date": "2025-09-02"
    }

    # if str(sys.argv[2]).strip():
    #     kwargs = json.loads(str(sys.argv[2]))

    if str(sys.argv[1]).lower() == "send":
        print(kwargs)
        initiate_email_send(**kwargs)

    import os

    cwd = os.getcwd()
    print(cwd)

    METRICS_PATH = f'{cwd}/backend/storage/metrics/email_metrics_current.png'

    if str(sys.argv[1]).lower() == "metrics":
        metrics = get_metrics(saved_metrics_path=METRICS_PATH)
        print(metrics)


