import os

from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv('GDRIVE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GDRIVE_CLIENT_SECRET')
TOKEN_PATH = os.getenv('GDRIVE_TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.getenv('GDRIVE_CREDENTIALS_PATH', 'credentials.json')
FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID')


from flask import Flask, render_template, request, redirect
import json
from metadata.db import upsert_metadata
from cloud.gdrive_backup import (
    upload_file,
    download_file,
    delete_file,
    restore_all_files,
    sync_folder
)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
app = Flask(__name__)

# Authenticate using your service account
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds)

# Upload file to Drive (called whenever a file is created)
def upload_to_drive(local_filepath, filename):
    service = get_drive_service()
    file_metadata = {'name': filename}
    media = MediaFileUpload(local_filepath, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # Make file public
    service.permissions().create(
        fileId=file['id'],
        body={'role': 'reader', 'type': 'anyone'},
    ).execute()

    return file['id']

file_system = {}

def save_to_disk():
    with open('filesystem.json', 'w') as f:
        json.dump(file_system, f)

def load_from_disk():
    global file_system
    if os.path.exists('filesystem.json'):
        with open('filesystem.json', 'r') as f:
            file_system = json.load(f)

def get_nested(path_parts, create_missing=False):
    current = file_system
    for part in path_parts[:-1]:
        if part not in current:
            if create_missing:
                current[part] = {}
            else:
                return None
        current = current[part]
        if not isinstance(current, dict):
            return None
    return current

def mkdir(path):
    parts = path.strip('/').split('/')
    parent = get_nested(parts, create_missing=True)
    if parts[-1] not in parent:
        parent[parts[-1]] = {}
        os.makedirs(os.path.join(*parts), exist_ok=True)
        save_to_disk()
        print(f"Directory created at {path}")
    else:
        print(f"Directory already exists: {path}")

def create(path):
    try:
        parts = path.strip('/').split('/')
        dir_parts = parts[:-1]
        file_name = parts[-1]

        # Validate file name
        if not file_name or '.' not in file_name:
            print(f"Invalid file path: {path}")
            return

        parent = get_nested(parts, create_missing=True)
        if not isinstance(parent, dict):
            print(f"Invalid path: {path}")
            return

        if file_name not in parent:
            parent[file_name] = ""

        os.makedirs(os.path.join(*dir_parts), exist_ok=True)
        full_path = os.path.join(*parts)

        with open(full_path, 'w') as f:
            pass

        upload_file(full_path)
        from metadata.db import upsert_metadata
        upsert_metadata(full_path, file_name, os.path.getsize(full_path))

        save_to_disk()
        print(f"File created at {path}")
    except Exception as e:
        print(f"Error in create(): {e}")


def write(path, content):
    parts = path.strip('/').split('/')
    parent = get_nested(parts)
    if parent and parts[-1] in parent:
        parent[parts[-1]] = content
        full_path = os.path.join(*parts)
        with open(full_path, 'w') as f:
            f.write(content)

        upload_file(full_path)
        upsert_metadata(full_path, parts[-1], os.path.getsize(full_path))


        save_to_disk()
        print(f"Written to {path}")
    else:
        print(f"File not found in memory: {path}")

def append(path, content):
    parts = path.strip('/').split('/')
    parent = get_nested(parts)
    if parent and parts[-1] in parent:
        parent[parts[-1]] += content
        full_path = os.path.join(*parts)
        with open(full_path, 'a') as f:
            f.write(content)

        upload_file(full_path)
        upsert_metadata(full_path, parts[-1], os.path.getsize(full_path))

        save_to_disk()
        print(f"Appended to {path}")
    else:
        print(f"File not found in memory: {path}")


def read(path):
    parts = path.strip('/').split('/')
    parent = get_nested(parts)
    if parent and parts[-1] in parent:
        print(f"Contents of {path}: {parent[parts[-1]]}")
    else:
        print(f"File not found: {path}")

def delete(path):
    parts = path.strip('/').split('/')
    parent = get_nested(parts)
    if parent and parts[-1] in parent:
        del parent[parts[-1]]
        full_path = os.path.join(*parts)

        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                # Recursively delete folder contents
                import shutil
                shutil.rmtree(full_path)
        except Exception as e:
            print(f"Error while deleting: {e}")

        save_to_disk()
        print(f"Deleted: {path}")
    else:
        print(f"Path not found in memory: {path}")



def list_dir(path):
    parts = path.strip('/').split('/') if path.strip('/') else []
    node = file_system if not parts else get_nested(parts + [''])
    if isinstance(node, dict):
        print("Contents:", ' '.join(node.keys()))
    else:
        print(f"Not a directory: {path}")

def sync_folder_to_memory(folder_path):
    parts = folder_path.strip('/').split('/')
    current = file_system
    for part in parts:
        if part not in current:
            current[part] = {}
        current = current[part]

    for root, dirs, files in os.walk(folder_path):
        rel_path = os.path.relpath(root, folder_path)
        node = current
        if rel_path != ".":
            for part in rel_path.split(os.sep):
                node = node.setdefault(part, {})
        for d in dirs:
            node[d] = {}
        for f in files:
            file_path = os.path.join(root, f)
            try:
                with open(file_path, "r", encoding="utf-8") as file_obj:
                    node[f] = file_obj.read()
            except Exception as e:
                node[f] = "" 

        save_to_disk()

def main():
    load_from_disk()
    while True:
        command = input('> ').strip()
        if not command:
            continue
        parts = command.split()
        cmd = parts[0]

        if cmd == 'mkdir' and len(parts) == 2:
            mkdir(parts[1])
        elif cmd == 'create' and len(parts) == 2:
            create(parts[1])
        elif cmd == 'write' and len(parts) >= 3:
            write(parts[1], ' '.join(parts[2:]))
        elif cmd == 'append' and len(parts) >= 3:
            append(parts[1], ' '.join(parts[2:]))
        elif cmd == 'read' and len(parts) == 2:
            read(parts[1])
        elif cmd == 'delete' and len(parts) == 2:
            delete(parts[1])
        elif cmd == 'download' and len(parts) == 2:
            download_file(parts[1]) 
        elif cmd == 'ls' and len(parts) == 2:
            list_dir(parts[1])
        elif cmd == 'deletecloud' and len(parts) == 2:
            delete_file(parts[1])
        elif cmd == 'restoreall':
            restore_all_files()
        elif cmd == 'syncfolder' and len(parts) == 2:
            sync_folder(parts[1])
        elif cmd == 'exit':
            print("Exiting...")
            break
        else:
            print("Unknown or malformed command")

if __name__ == '__main__':
    main()
__all__ = ['fetch_metadata', 'upsert_metadata']
