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
DOWNLOAD_DIR = "/Volumes/LaCie/archCoppul" 

#log stuff
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE), 
        logging.StreamHandler()  
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
def get_file_size(uuid, username, api_key):
    #Get the expected file size from the server without downloading.

    size_url = f"https://viu1.coppul.archivematica.org:8000/api/v2/file/{uuid}/download/"
    headers = {"Authorization": f"ApiKey {username}:{api_key}"}
    
    try:
        # Get size
        response = requests.head(size_url, headers=headers, verify=True)
        response.raise_for_status()
        return int(response.headers.get("content-length", 0))
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get file size for AIP {uuid}: {e}")
        return None

def download_aip(uuid, current_path, username, api_key):
    # Get filename
    filename = current_path.split("/")[-1]
    download_url = f"https://viu1.coppul.archivematica.org:8000/api/v2/file/{uuid}/download/"
    headers = {"Authorization": f"ApiKey {username}:{api_key}"}

    # Check the dir . . .
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    #  if the file already exists
    if os.path.exists(file_path):
        # Get the current size of file
        local_size = os.path.getsize(file_path)
        
        # Get expected size from server
        expected_size = get_file_size(uuid, username, api_key)
        
        if expected_size is not None and local_size == expected_size:
            logging.info(f"File {filename} already exists with correct size ({local_size} bytes). Skipping download.")
            return True
        else:
            logging.info(f"File {filename} exists but size may be incorrect (local: {local_size}, expected: {expected_size or 'unknown'}). Re-downloading.")
    
    # Download AIP (with a progress bar!)
    try:
        response = requests.get(download_url, headers=headers, stream=True, verify=True)
        response.raise_for_status()

        # File size
        total_size = int(response.headers.get("content-length", 0))

        progress_bar = tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=f"Downloading {filename}",
            ncols=100  # Progress bar width
        )

        # Download the file in parts
        with open(file_path, "wb") as f:
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

        # Log success
        if success:
            logging.info(f"Successfully processed AIP {uuid}")
        else:#l
            logging.error(f"Failed to process AIP {uuid}")

    logging.info("All AIPs processed.")

if __name__ == "__main__":
    main()