import boto3
import os

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