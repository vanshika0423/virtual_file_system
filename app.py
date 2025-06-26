import os
from flask import Flask, render_template, request, jsonify
from check_metadata import fetch_metadata
import main3  # Your main backend logic
from flask import redirect  
from main3 import upload_to_drive 

app = Flask(__name__)

# Load filesystem initially
main3.load_from_disk()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/local')
def local_page():
    return render_template('local.html')

@app.route('/metadata')
def metadata_page():
    try:
        metadata = fetch_metadata()
    except Exception as e:
        metadata = [f"Error fetching metadata: {str(e)}"]
    return render_template('metadata.html', metadata=metadata)

@app.route('/cloud')
def cloud_page():
    try:
        from cloud.gdrive_backup import get_drive_service
        service = get_drive_service()
        results = service.files().list(fields="files(id, name)").execute()
        files = results.get('files', [])
        cloud_files = [{
            'name': f['name'],
            'url': f"https://drive.google.com/file/d/{f['id']}/view"
        } for f in files]
    except Exception as e:
        cloud_files = [{"name": f"Error: {str(e)}", "url": "#"}]

    return render_template('cloud.html', cloud_files=cloud_files)

def cloud_storage():
    from cloud.gdrive_backup import get_drive_service
    service = get_drive_service()
    results = service.files().list(fields="files(id, name)").execute()
    files = results.get('files', [])

    cloud_files = []
    for file in files:
        cloud_files.append({
            "name": file['name'],
            "url": f"https://drive.google.com/file/d/{file['id']}/view"
        })

    return render_template("cloud.html", cloud_files=cloud_files)

@app.route("/create-file", methods=["POST"])
def create_file():
    filename = request.form["filename"]
    content = request.form["content"]
    
    # Save locally
    local_path = f"downloads/{filename}"
    os.makedirs("downloads", exist_ok=True)  
    with open(local_path, "w") as f:
        f.write(content)
    # Upload to Google Drive
    file_id = upload_to_drive(local_path, filename)
    return redirect("/cloud")

@app.route('/filesystem')
def get_filesystem():
    main3.load_from_disk()
    return jsonify(main3.file_system)

@app.route('/create-file-api')
def create_file_api():
    path = request.args.get('path')
    if path:
        main3.create(path)
        return f"File created at {path}"
    return "Missing path", 400

@app.route('/create-folder')
def create_folder():
    path = request.args.get('path')
    if path:
        main3.mkdir(path)
        return f"Folder created at {path}"
    return "Missing path", 400

@app.route('/read-file')
def read_file():
    path = request.args.get('path')
    if path:
        parts = path.strip('/').split('/')
        node = main3.get_nested(parts)
        if node and parts[-1] in node:
            return node[parts[-1]]
    return "File not found", 404

@app.route('/write-file')
def write_file():
    path = request.args.get('path')
    content = request.args.get('content')
    if path and content is not None:
        main3.write(path, content)
        return f"{path} updated"
    return "Missing path or content", 400


@app.route('/download', methods=['POST'])
def download_file():
    path = request.args.get('path')
    if path:
        from cloud.gdrive_backup import download_file
        download_file(path, save_to='downloads')
        main3.sync_folder_to_memory('downloads') 
        return f"Downloaded {path} from cloud"
    return "Missing path", 400


@app.route('/restoreall', methods=['POST'])
def restore_all():
    from cloud.gdrive_backup import restore_all_files
    restore_all_files(save_to='restored')
    main3.sync_folder_to_memory('restored') 
    return "All files restored from cloud"


@app.route('/delete-local', methods=['POST'])
def delete_local():
    path = request.args.get('path')
    if path:
        main3.delete(path)
        return f"Deleted {path} from local"
    return "Missing path", 400

@app.route('/delete-cloud', methods=['POST'])
def delete_cloud():
    path = request.args.get('path')
    if path:
        file_name = os.path.basename(path)  
        from cloud.gdrive_backup import delete_file
        delete_file(file_name)
        return f"Deleted {file_name} from cloud"
    return "Missing path", 400



if __name__ == '__main__':
    app.run(debug=True)
