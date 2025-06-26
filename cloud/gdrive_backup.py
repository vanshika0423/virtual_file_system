import os
import io
import mimetypes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None
    token_path = 'cloud/token.json'
    creds_path = 'cloud/credentials.json'
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_file(file_path, folder_id=None):
    service = get_drive_service()
    file_name = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)

    # Check if file exists on Drive
    response = service.files().list(q=f"name='{file_name}'", spaces='drive').execute()
    files = response.get('files', [])

    if files:
        file_id = files[0]['id']
        print(f"File exists. Updating {file_name} on Drive...")

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        updated = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"Updated: {file_path} → Google Drive")
    else:
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path, mimetype=mime_type)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded: {file_path} → Google Drive (ID: {file.get('id')})")


def file_exists(file_name):
    service = get_drive_service()
    response = service.files().list(q=f"name='{file_name}'", spaces='drive').execute()
    return len(response.get('files', [])) > 0

def download_file(file_name, save_to='downloads'):
    service = get_drive_service()
    response = service.files().list(q=f"name='{file_name}'", spaces='drive').execute()
    files = response.get('files', [])
    if not files:
        print(f"No file named {file_name} found on Drive.")
        return

    file_id = files[0]['id']
    request = service.files().get_media(fileId=file_id)
    os.makedirs(save_to, exist_ok=True)
    file_path = os.path.join(save_to, file_name)

    with open(file_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name}: {int(status.progress() * 100)}%")
    print(f"Downloaded: {file_path}")

def restore_all_files(save_to='restored'):
    service = get_drive_service()
    results = service.files().list(pageSize=1000, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        print("No files found in Drive to restore.")
        return

    os.makedirs(save_to, exist_ok=True)
    for file in files:
        file_id = file['id']
        file_name = file['name']
        file_path = os.path.join(save_to, file_name)

        request = service.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        print(f"Restored: {file_name}")

def delete_file(file_name):
    service = get_drive_service()
    response = service.files().list(q=f"name='{file_name}'", spaces='drive').execute()
    files = response.get('files', [])
    if not files:
        print(f"No file named {file_name} found to delete.")
        return

    file_id = files[0]['id']
    service.files().delete(fileId=file_id).execute()
    print(f"Deleted from Drive: {file_name}")

def sync_folder(local_dir):
    for root, dirs, files in os.walk(local_dir):
        for filename in files:
            full_path = os.path.join(root, filename)
            upload_file(full_path)
