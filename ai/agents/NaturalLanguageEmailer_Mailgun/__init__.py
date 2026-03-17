import requests
from datetime import datetime
import json
import time
# from contacts_mgr import extract_email_and_name_columns_from_file
import csv
from urllib.parse import urljoin
import re
import requests
from email.utils import formatdate
import matplotlib.pyplot as plt
import sys
from dotenv import load_dotenv
import os 
import boto3

# Load environment variables from .env
load_dotenv()
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")  # Replace with your actual API key
NEVERBOUNCE_CUSTOM_APP_API_KEY = os.getenv("NEVERBOUNCE_CUSTOM_APP_API_KEY")
DOMAIN=os.getenv("NEVERBOUNCE_DOMAIN")


def visualize_data_with_chart(data: object, start_date: str, end_date: str, saved_metrics_path: str):
    print(f"Generating metrics chart metrics/email_metrics_current.png...")

    # Extracting metrics from data
    metrics = data['aggregates']['metrics']
    metric_labels = ['Accepted', 'Delivered', 'Opened Rate', 'Clicked Rate']
    metric_values_counts = [metrics['accepted_count'], metrics['delivered_count']]
    metric_values_rates = [float(metrics['opened_rate']), float(metrics['clicked_rate'])]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # Primary axis for counts
    bar1 = ax1.bar(metric_labels[:2], metric_values_counts, color='skyblue', label='Counts')
    ax1.set_ylabel('Count', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')
    ax1.set_ylim(0, max(metric_values_counts) * 1.2)

    # Secondary axis for rates
    ax2 = ax1.twinx()
    bar2 = ax2.bar(metric_labels[2:], metric_values_rates, color='orange', label='Rates')
    ax2.set_ylabel('Rate', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax2.set_ylim(0, max(metric_values_rates) * 1.2)

    # Title and layout
    plt.title(f"{start_date} - {end_date}")
    fig.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Save the chart
    plt.savefig(saved_metrics_path)




def get_current_time_rfc2822():
    # Get the current time in seconds since epoch
    current_time = time.time()

    # Subtract 10 minutes (600 seconds)
    adjusted_time = current_time - 60

    # Format the adjusted time in RFC 2822 format
    rfc2822_time = formatdate(timeval=adjusted_time, localtime=False, usegmt=True)
    return rfc2822_time


def get_last_week_time_rfc2822():
    # Get the current time in seconds since epoch
    current_time = time.time()

    # Subtract one week (7 days * 24 hours * 60 minutes * 60 seconds)
    adjusted_time = current_time - (7 * 24 * 60 * 60)

    # Format the adjusted time in RFC 2822 format
    rfc2822_time = formatdate(timeval=adjusted_time, localtime=False, usegmt=True)
    return rfc2822_time


def get_metrics(saved_metrics_path: str):
    url = "https://api.mailgun.net/v1/analytics/metrics"
    end_time = get_current_time_rfc2822()
    start_time = get_last_week_time_rfc2822()

    print(f"Getting metrics for time period {start_time} - {end_time}")

    payload = {
    "resolution": "month",
    "metrics": [
        "accepted_count",
        "delivered_count",
        "clicked_rate",
        "opened_rate"
    ],
    "include_aggregates": True,
    "start": start_time,
    "duration": "1m",
    "filter": {
        "AND": [
        {
            "attribute": "domain",
            "comparator": "=",
            "values": [
            {
                "label": DOMAIN,
                "value": DOMAIN
            }
            ]
        }
        ]
    },
    "dimensions": [
        "time"
    ],
    "end": end_time,
    "include_subaccounts": True
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers, auth=("api", MAILGUN_API_KEY))

    data = response.json()
    visualize_data_with_chart(
        data=data, 
        start_date=start_time, 
        end_date=end_time, 
        saved_metrics_path=saved_metrics_path)
    return data


def send_simple_message(email_send_payload: object):
    print("Sending email message...")
    # Fetch HTML content from the endpoint
    print(email_send_payload)
    print(f"Getting html content as part of email message {email_send_payload["html_email_design"]}...")
    html_response = requests.get(email_send_payload["html_email_design"])

    # Remove unnecessary whitespace, newlines, and extra spaces between tags
    # cleaned_html = re.sub(r'\s+', ' ', html_response.text).strip()
    
    if html_response.status_code == 200:
        html_content = html_response.text  # Get the HTML content as a string
        # email_send_payload["html_email_design"] = html_content
        email_send_payload["html"] = html_content
    else:
        raise Exception(f"Failed to fetch HTML content. Status code: {html_response.status_code}")
    
    # Send the email with the fetched HTML
    resp = requests.post(
        f"https://api.mailgun.net/v3/{DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data=email_send_payload,
    )

    # Check if the email sending was successful
    if resp.status_code != 200:
        print(f"Failed to send email: {resp.text}")
        sys.exit(1)
    else:
        print("Email sent successfully!")
        return resp


def send_scheduled_message(data):
    # Fetch HTML content from the provided URL
    html_response = requests.get(data['saved_email_url'])
    
    if html_response.status_code == 200:
        html_content = html_response.text  # Get the HTML content as a string
    else:
        raise Exception(f"Failed to fetch HTML content. Status code: {html_response.status_code}")
    
    # Parse the schedule date and format it for Mailgun
    schedule_date = datetime.fromisoformat(data['schedule_date']).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Send the email with the fetched HTML and scheduled delivery time
    response = requests.post(
        "https://api.mailgun.net/v3/e3.infopnr.com/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": "Excited User <miguel@infopioneer.ai>",
            "to": ["migueltillisjr@gmail.com"],
            # "to": [data['contacts_url']],  # Using the contacts URL
            "subject": data['subject'],  # Subject from input data
            "html": html_content,  # Use the fetched HTML here
            "o:deliverytime": schedule_date  # Schedule the email
        }
    )
    
    if response.status_code == 200:
        return {"message": "Email successfully scheduled.", "status": "success"}
    else:
        return {"message": "Failed to schedule email.", "status": "error", "details": response.text}


def get_stats_account_totals():
    url = "https://api.mailgun.net/v1/analytics/metrics"

    payload = {
    "resolution": "month",
    "metrics": [
        "accepted_count",
        "delivered_count",
        "clicked_rate",
        "opened_rate"
    ],
    "include_aggregates": True,
    "start": "Mon, 13 Nov 2023 20:56:50 -0600",
    "duration": "1m",
    "dimensions": [
        "time"
    ],
    "end": "Wed, 21 Jan 2025 20:56:50 -0600",
    "include_subaccounts": True
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers, auth=("api", MAILGUN_API_KEY),)

    data = response.json()
    print(data)







def convert_csv_to_tsv(output_file: str):
    """
    Converts a comma-delimited CSV file to a tab-delimited file.
    
    :param input_file: Path to the input CSV file.
    :param output_file: Path to the output tab-delimited file.
    """
    try:
        print("Converting csv to tsv file type...")
        working_file_name = output_file + '.convert_csv_to_tsv'
        os.rename(output_file, working_file_name)
        with open(working_file_name, "r", newline='', encoding="utf-8") as csv_file, \
             open(output_file, "w", newline='', encoding="utf-8") as tsv_file:
            
            csv_reader = csv.reader(csv_file)  # Read CSV file
            tsv_writer = csv.writer(tsv_file, delimiter="\t")  # Write as tab-delimited
            
            for row in csv_reader:
                tsv_writer.writerow(row)
        os.remove(working_file_name)
        
        print(f"Conversion successful: '{output_file}'")
    
    except Exception as e:
        print(f"Error during conversion: {e}")




def upload_html_design_to_bucket(file_name: str, bucket_name="e3-designs", s3_key=None):
    """
    Uploads a file to an S3 bucket and returns its public URL.
    
    :param file_name: Local file path to upload.
    :param bucket_name: S3 bucket name.
    :param s3_key: The key (path) in the S3 bucket. Defaults to file_name if not provided.
    :return: Public URL of the uploaded file.
    """
    # Initialize S3 client
    s3_client = boto3.client('s3')

    # Use the file name as S3 key if not provided
    if s3_key is None:
        s3_key = file_name.split("/")[-1]  # Extract filename from path

    # Upload file with public-read ACL
    try:
        print("Uploading html design file to bucket...")
        print(file_name)
        s3_client.upload_file(file_name, bucket_name, s3_key)

        # Construct the public URL
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{os.path.basename(file_name)}"

        print(f"File '{file_name}' uploaded successfully to '{public_url}'.")
        return public_url

    except Exception as e:
        print(f"Failed to upload {file_name}: {e}")
        return None


def list_full_file_paths(directory_path="grouped_contacts"):
    """
    Lists the full file paths of all files in the specified directory.

    Args:
        directory_path (str): Path to the directory.

    Returns:
        list: A list of full file paths.
    """
    try:
        print("Listing file paths...")
        file_paths = [
            os.path.join(directory_path, file) 
            for file in os.listdir(directory_path) 
            if os.path.isfile(os.path.join(directory_path, file))
        ]
        return file_paths
    except FileNotFoundError:
        print(f"Directory '{directory_path}' not found.")
        return []


def create_data_structure(design_name: str, html_url: str, contacts: list, subject: str, preview: str, from_data: str, tracking: str, send_date: str):
    print("Creating email request data structure...")
    return {
        "design_name": design_name,
        "subject": subject,
        "preview": preview,
        "from": from_data,
        "to": contacts,
        "html_email_design": html_url,
        "o:tracking": tracking,
        "send_date": send_date
    }