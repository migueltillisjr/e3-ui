from dotenv import load_dotenv
import requests
import time
import os
import json
import csv
from ai.agents.NaturalLanguageDatabase import ask_db
from ai.agents.NaturalLanguageDatabase import postgress_sql
import os

# Load environment variables from .env
load_dotenv()
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")  # Replace with your actual API key
NEVERBOUNCE_CUSTOM_APP_API_KEY = os.getenv("NEVERBOUNCE_CUSTOM_APP_API_KEY")
DOMAIN=os.getenv("NEVERBOUNCE_DOMAIN")

output_dir = os.path.join(os.path.dirname(__file__), '..', 'contacts')
output_path = os.path.join(output_dir, "contacts.tsv.validated")

def validate_email(email):
    """
    Validate an email address using NeverBounce API.
    
    :param email: The email address to validate.
    :return: The validation result (valid, invalid, disposable, etc.).
    """
    url = "https://api.neverbounce.com/v4/single/check"
    payload = {
        "key": NEVERBOUNCE_CUSTOM_APP_API_KEY,
        "email": email
    }

    response = requests.post(url, json=payload)
    data = response.json()

    if "result" in data:
        return data["result"]  # Possible values: valid, invalid, disposable, unknown
    else:
        return "error"


def get_all_file_paths(directory):
    return [
        os.path.realpath(os.path.join(directory, filename))
        for filename in os.listdir(directory)
        if filename.endswith('chunked.tsv') and os.path.isfile(os.path.join(directory, filename))
    ]


def extract_name_email_list(filepath):
    results = []

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', 'NONE').strip()
            email = row.get('email', '').strip()

            if first_name and email:
                full_name = f"{first_name} {last_name}".strip()
                results.append([full_name, email])

    return results


def get_validated_paths(directory):
    return [
        os.path.realpath(os.path.join(directory, filename))
        for filename in os.listdir(directory)
        if filename.endswith('.vjob') and os.path.isfile(os.path.join(directory, filename))
    ]

def update_nldb(output_dir):
    validate_files = get_validated_paths(output_dir)

    for vfile in validate_files:
        with open(vfile, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')

            for row in reader:
                name = row['name'].strip()
                email = row['email'].strip()
                validated = row['validated'].strip()
                sql_query = ""
                if validated.lower() == "true":
                    print(f"Updating {email} in db, validated = True")
                    sql_query = """
                    INSERT INTO crm_contacts (first_name, email, validated)
                    VALUES (:name, :email, :validated)
                    ON CONFLICT (email) DO UPDATE
                    SET first_name = EXCLUDED.first_name,
                        validated = EXCLUDED.validated,
                        last_validated = now();
                    """
                    postgress_sql(sql_query, {
                                        'name': name,
                                        'email': email,
                                        'validated': validated  # Convert to Boolean
                                    })

                if validated.lower() != "true":
                    print(f"Removing {email} from db, validated NOT equal to True")
                    sql_query = """
                    DELETE FROM crm_contacts
                    WHERE email = :email;
                    """
                    postgress_sql(sql_query, {'email': email })

                print(f"Cleaning up contacts where last_validated is not null and validated is False")
                sql_query = """
                DELETE FROM crm_contacts
                WHERE last_validated IS NOT NULL
                AND validated = FALSE;
                """
                postgress_sql(sql_query)
                
    return "Validation and db update complete."



def batch_validate_emails(query: str):
    """
    Uses Mailgun's Bulk Validation API to validate a list of emails.

    Args:
        email_list (list): List of email addresses to validate.

    Returns:
        dict: Response data containing validation results.
    """
    chunked_emails = get_all_file_paths(output_dir)

    for chunked_file_path in chunked_emails:
        url = "https://api.neverbounce.com/v4/jobs/create"
        headers = {"Content-Type": "application/json"}
        data = {
            "key": NEVERBOUNCE_CUSTOM_APP_API_KEY,
            "input_location": "supplied",
            "auto_start": 1,
            "auto_parse": 1,
            "input": extract_name_email_list(filepath=chunked_file_path)
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            resp = response.json()  # Print JSON response
            print(resp)
            print(f"Checking validation status for job {resp['status']}")
            get_validation_status(job_id=resp['job_id'], output_file_path=output_path)
            print("Updating nldb with validated contacts...")

        else:
            print(f"Error: {response.status_code}, {response.text}")

    update_nldb(output_dir=output_dir)

    return f"Emails with satisfying query: {query} successfully validated."



def write_to_tsv(data, output_path):
    # Decode bytes to string
    decoded_data = data.decode('utf-8').strip()

    # Split into lines
    lines = decoded_data.splitlines()

    rows = []
    for line in lines:
        # Split CSV-style fields
        parts = [p.strip().replace('"', '') for p in line.split(',')]
        
        # Clean status
        if parts[-1].lower() == 'invalid':
            parts[-1] = 'False'
        elif parts[-1].lower() == 'valid':
            parts[-1] = 'True'

        rows.append(parts)

    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["name", "email", "validated"])  # Header row
        writer.writerows(rows)


def download_job_results(api_key: str, job_id: str, output_file: str):
    url = f"https://api.neverbounce.com/v4/jobs/download?key={api_key}&job_id={job_id}"
    
    response = requests.get(url)

    if response.status_code == 200:
        write_to_tsv(data=response.content, output_path=output_file + f".{job_id}.vjob")
        print(f"Job results downloaded successfully to {output_file}")
    else:
        print(f"Error: {response.status_code}, {response.text}")



def get_validation_status(job_id: str, output_file_path: str):
    # api_key = NEVERBOUNCE_CUSTOM_APP_API_KEY
    url = f"https://api.neverbounce.com/v4/jobs/status?key={NEVERBOUNCE_CUSTOM_APP_API_KEY}&job_id={job_id}"

    while True:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print(data)  # Print JSON response
            
            if data.get("status") == "success":
                if data.get("job_status") == "complete":
                    print("Job completed successfully!")
                    download_job_results(api_key=NEVERBOUNCE_CUSTOM_APP_API_KEY, job_id=job_id, output_file=output_file_path)
                    return data  # Return the response data
                if data.get("job_status") == "failed":
                    raise Exception("Error" + str(data))
            print("Job not yet completed, retrying...")
        else:
            print(f"Error: {response.status_code}, {response.text}")
        
        time.sleep(10)  # Wait for 10 seconds before retrying