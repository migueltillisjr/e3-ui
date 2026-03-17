from ai.agents.NaturalLanguageEmailer_Mailgun import send_simple_message
from ai.agents.NaturalLanguageEmailer_Mailgun import get_stats_account_totals
from ai.agents.NaturalLanguageEmailer_Mailgun import send_scheduled_message
from ai.agents.NaturalLanguageEmailer_Mailgun import create_data_structure
from ai.agents.NaturalLanguageEmailer_Mailgun import upload_html_design_to_bucket
import csv
import json
import os
import glob
from dotenv import load_dotenv

load_dotenv()
DOMAIN=os.getenv("NEVERBOUNCE_DOMAIN")
CONTACTS_DIR = os.getenv("CONTACTS_DIR")
EMAIL_DESIGN_DIR = os.getenv("EMAIL_DESIGN_DIR")

def get_chunked_tsv_files():
    base_dir = os.path.dirname(__file__)
    contacts_dir = CONTACTS_DIR
    chunked_contacts_tsv_pattern = os.path.join(contacts_dir, 'contacts_chunk_*.tsv')

    return  glob.glob(chunked_contacts_tsv_pattern)

def get_tsv_files():
    base_dir = os.path.dirname(__file__)
    contacts_dir = CONTACTS_DIR
    truth_contacts_tsv_pattern = os.path.join(contacts_dir, 'contacts.tsv')

    return  glob.glob(truth_contacts_tsv_pattern)


def read_tsv_in_chunks(filepath, chunk_size=200):
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)  # Skip header row
        chunk = []
        for row in reader:
            if len(row) < 4:
                continue
            name = row[1].strip()
            email = row[3].strip()
            if name and email:
                chunk.append([name, email])
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk


def write_chunks_to_disk(filepath, chunk_size=200):
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    output_dir = CONTACTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    for idx, chunk in enumerate(read_tsv_in_chunks(filepath, chunk_size), start=1):
        output_path = os.path.join(output_dir, f"{base_name}_chunk_{idx}.tsv")
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["name", "email"])  # header
            writer.writerows(chunk)
        print(f"✅ Wrote {len(chunk)} rows to {output_path}")


def extract_name_email(filepath):
    results = []

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)  # Skip header row

        for row in reader:
            if len(row) < 2:  # Skip bad rows
                continue

            results.append(row)

    return results


def delete_all_but(filepath_to_keep):
    directory = os.path.dirname(filepath_to_keep)
    filename_to_keep = os.path.basename(filepath_to_keep)

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if filename == filename_to_keep:
            continue  # Skip the file we want to keep

        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted {file_path}")


def initiate_email_send(design_name: str, html_email_design: str, subject: str, preview: str, from_data: str, tracking: str, send_date: str):
    print("debug info: Intiating email send...")
    html_url=upload_html_design_to_bucket(file_name=EMAIL_DESIGN_DIR + "/" + os.path.basename(html_email_design))
    
    # get files in contact dir
    tsv_files = get_tsv_files()
    source_contact_file = tsv_files[0]
    delete_all_but(source_contact_file)
    # Split into chunks of other files
    write_chunks_to_disk(tsv_files[0], chunk_size=200)
    # os.remove(source_contact_file)

    # list tsv files again
    chunked_tsv_files = get_chunked_tsv_files()

    for f in chunked_tsv_files:
        base_dir = os.path.dirname(__file__)  # current script dir
        contacts_dir = CONTACTS_DIR
        full_contacts_path = os.path.realpath(contacts_dir)
        contacts = extract_name_email(filepath=full_contacts_path + '/' + str(os.path.basename(f)))
        email_send_payload = create_data_structure(
            design_name=design_name,
            send_date=send_date,
            html_url=html_url,
            contacts=contacts,
            subject=subject,
            preview=preview,
            from_data=from_data,
            tracking=tracking)

        with open(f + ".payload.json", "w") as file:
            file.write(json.dumps(email_send_payload, indent=4))
            print(f"✅ Created mailgun payload file {f + ".payload.json"}")


        print(send_simple_message(email_send_payload=email_send_payload))



