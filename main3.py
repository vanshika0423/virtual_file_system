import os
import json
from metadata.db import upsert_metadata
from cloud.gdrive_backup import (
    upload_file,
    download_file,
    delete_file,
    restore_all_files,
    sync_folder
)


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
    parts = path.strip('/').split('/')
    parent = get_nested(parts, create_missing=True)
    parent[parts[-1]] = ""
    os.makedirs(os.path.join(*parts[:-1]), exist_ok=True)
    full_path = os.path.join(*parts)
    open(full_path, 'w').close()

    upload_file(full_path)
    upsert_metadata(full_path, parts[-1], os.path.getsize(full_path))


    save_to_disk()
    print(f"File created at {path}")

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
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            os.rmdir(full_path)

        # NOTE: No deletion on Google Drive here (as requested)

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
