import json
import requests
import os
import logging
from pathlib import Path
from tqdm import tqdm  

# Config bits
API_CREDENTIALS_FILE = "api_creds.json"  
AIPS_JSON_FILE = "uploaded.json" 
LOG_FILE = "download_log.txt" 
DOWNLOAD_DIR = "/Users/Daniel/Desktop" 

#log stuff
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # for the log file
        logging.StreamHandler()  # for the console
    ]
)
#load the creds
def load_api_credentials():
  
    try:
        with open(API_CREDENTIALS_FILE, "r") as f:
            credentials = json.load(f)
            return credentials["username"], credentials["api_key"]
    except FileNotFoundError:
        logging.error(f"API credentials file '{API_CREDENTIALS_FILE}' not found.")
        exit(1)
    except KeyError:
        logging.error(f"Invalid format in '{API_CREDENTIALS_FILE}'. Expected 'username' and 'api_key'.")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in '{API_CREDENTIALS_FILE}'.")
        exit(1)

#load the AIPS
def load_aips():
   
    try:
        with open(AIPS_JSON_FILE, "r") as f:
            data = json.load(f)
            logging.debug(f"Loaded AIPs data: {data}")  # Debug statement
            return data
    except FileNotFoundError:
        logging.error(f"AIPs file '{AIPS_JSON_FILE}' not found.")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in '{AIPS_JSON_FILE}'.")
        exit(1)


#Download an AIP using its UUID and save it with the name from current_path
def download_aip(uuid, current_path, username, api_key):
   
    # Get filename from the current_path
    filename = current_path.split("/")[-1]
    download_url = f"https://viu1.coppul.archivematica.org:8000/api/v2/file/{uuid}/download/"
    headers = {"Authorization": f"ApiKey {username}:{api_key}"}

    # check the dir
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    # Check if the file already exists
    if os.path.exists(file_path):
        # Get the current size of the file
        current_size = os.path.getsize(file_path)
        headers["Range"] = f"bytes={current_size}-"  # Request remaining bytes
    else:
        current_size = 0

    # Download AIP (with a progres bar!)
    try:
        response = requests.get(download_url, headers=headers, stream=True, verify=True)  # Enable SSL verification
        response.raise_for_status()  # Raise an error for bad status codes

        # file size
        total_size = int(response.headers.get("content-length", 0)) + current_size

    
        progress_bar = tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=f"Downloading {filename}",
            ncols=100,  # Adjust the width of the progress bar
            initial=current_size  # Start from the current size
        )

        # Download the file in parts
        with open(file_path, "ab") as f:  # Open in append mode
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    progress_bar.update(len(chunk))

        progress_bar.close() 
        logging.info(f"Downloaded AIP {uuid} to {file_path}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download AIP {uuid}: {e}")
        return False

def main():
    # Load API creds
    username, api_key = load_api_credentials()

    # Load AIPs data
    aips_data = load_aips()
    aips = aips_data["objects"] 

    # Count total AIPs
    total_aips = len(aips)
    logging.info(f"Total AIPs to process: {total_aips}")

    # Process AIPs
    for index, aip in enumerate(aips, start=1):
        uuid = aip["uuid"]
        current_path = aip["current_path"]

        logging.info(f"Processing AIP {index}/{total_aips}: {uuid}")

        # Download the AIP
        success = download_aip(uuid, current_path, username, api_key)

        # Log success or failure
        if success:
            logging.info(f"Successfully processed AIP {uuid}")
        else:
            logging.error(f"Failed to process AIP {uuid}")

    logging.info("All AIPs processed.")

if __name__ == "__main__":
    main()