import os
import sys
import zipfile
import requests
from tqdm import tqdm

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_ZIP = "model.zip"
MODEL_DIR = "model"

def download_model():
    if os.path.exists(MODEL_DIR):
        print("Model directory already exists. Skipping download.")
        return

    print(f"Downloading model from {MODEL_URL}...")
    response = requests.get(MODEL_URL, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(MODEL_ZIP, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

    print("Extracting model...")
    with zipfile.ZipFile(MODEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    # Rename the extracted folder to 'model'
    extracted_folder = "vosk-model-small-en-us-0.15"
    if os.path.exists(extracted_folder):
        os.rename(extracted_folder, MODEL_DIR)
    
    os.remove(MODEL_ZIP)
    print("Model ready.")

if __name__ == "__main__":
    download_model()
