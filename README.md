# Virtual File System App

This project is a web-based Virtual File System that lets you create, edit, upload, and manage files and folders—locally and in Google Drive—right from your browser. Built with Flask and the Google Drive API, it’s designed to demonstrate cloud sync, metadata tracking, and a clean user experience for file management.

---

## Features

- **Create, rename, move, and delete files/folders** (local and cloud)
- **Real-time sync** between your machine and Google Drive
- **Upload and download files** from Google Drive with a couple of clicks
- **File metadata storage** with SQLite for tracking changes
- **Simple, intuitive web UI**—no command line required
- **RESTful API** endpoints for all major file actions

---

## Quick Demo

*Add screenshots or a GIF showing the UI here! If you want a badge for deployment status or tech stack, add them above.*

---

## Table of Contents

- [Getting Started](#getting-started)
- [Google Drive Setup](#google-drive-setup)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Getting Started

1. **Clone this repository**
   ```bash
   git clone https://github.com/vanshika0423/virtual_file_system.git
   cd virtual-file-system-app

2. **Install the dependencies**

   Make sure you have Python 3.8+ installed. It's recommended to use a virtual environment:

   ```bash
   pip install -r requirements.txt

Google Drive Setup

Go to Google Cloud Console.

Create a new project (or select an existing one).

Navigate to APIs & Services > Library, search for "Google Drive API" and enable it.

Go to APIs & Services > Credentials. Click Create Credentials > OAuth client ID.

Application type: Desktop app or Web application.

Add http://localhost as a redirect URI if required.

Download the credentials.json file and place it in your project root.

The first time you run the app, you'll be prompted for Google account authorization; this will create token.json.

4. **Environment Variables**

  a. Copy the example file to .env:

        ```bash
        cp .env.example .env

  b. Open .env and fill in your Google client credentials and Drive folder ID.

    GDRIVE_CLIENT_ID=your-client-id-here
    GDRIVE_CLIENT_SECRET=your-client-secret-here
    GDRIVE_TOKEN_PATH=token.json
    GDRIVE_CREDENTIALS_PATH=credentials.json
    GDRIVE_FOLDER_ID=your-folder-id-here


## Running Locally
 python app.py

 ```or for production-style run:

    gunicorn app:appProject Structure

The app should now be live at http://localhost:5000.


## Project Structure
    .
    ├── app.py
    ├── main3.py
    ├── check_metadata.py
    ├── cloud/
    ├── downloads/
    ├── metadata/
    ├── os2/
    ├── restored/
    ├── static/
    ├── templates/
    ├── token.json
    ├── credentials.json
    ├── .env
    ├── .env.example
    ├── .gitignore
    ├── requirements.txt
    └── README.md


## Deployment
    This app can be deployed on platforms like Render, Railway, Heroku, or any cloud VM with Python support.

    Deployment steps:
       - Set your environment variables/secrets on the platform (never commit them).

       - If using Gunicorn, add a Procfile with:
          -  web: gunicorn app:app

       - Push your repo and connect it to the deployment platform.

       - Set up required environment variables in the platform dashboard.

## Troubleshooting
    -OAuth or Drive errors?
        Double-check your credentials, redirect URIs, and that the Drive API is enabled.

    -App crashes on start?
        Make sure all environment variables are set and all required files (credentials.json, .env) are present.

    -File operations not reflected on Google Drive?
        Verify the GDRIVE_FOLDER_ID is correct and the app has access.

Author
    Built by Vanshika Dixit.
    If you find this useful, a star on GitHub is appreciated!