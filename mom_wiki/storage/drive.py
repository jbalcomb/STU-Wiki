"""Google Drive storage module for large binary files."""

import json
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DriveStorage:
    """Google Drive integration for storing large binary files."""

    def __init__(self, credentials_file: str = "config/google-credentials.json"):
        self.credentials_file = Path(credentials_file)
        self._service = None
        self._folder_id: Optional[str] = None

    def _get_service(self):
        """Get or create Google Drive API service."""
        if self._service is not None:
            return self._service

        if not self.credentials_file.exists():
            logger.warning(f"Google credentials not found: {self.credentials_file}")
            return None

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = None
            token_file = self.credentials_file.parent / "token.json"

            if token_file.exists():
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())

            self._service = build('drive', 'v3', credentials=creds)
            return self._service

        except ImportError:
            logger.error("Google API libraries not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            return None

    def _get_or_create_folder(self, folder_name: str = "MoMWikiCorpus") -> Optional[str]:
        """Get or create the corpus folder in Drive."""
        if self._folder_id:
            return self._folder_id

        service = self._get_service()
        if not service:
            return None

        try:
            # Check if folder exists
            results = service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])
            if files:
                self._folder_id = files[0]['id']
                return self._folder_id

            # Create folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            self._folder_id = folder.get('id')
            return self._folder_id

        except Exception as e:
            logger.error(f"Failed to get/create folder: {e}")
            return None

    def upload_file(self, file_path: str, mime_type: str = "application/octet-stream") -> Optional[str]:
        """
        Upload a file to Google Drive.
        Returns the file ID if successful.
        """
        service = self._get_service()
        if not service:
            logger.warning("Drive service not available, skipping upload")
            return None

        folder_id = self._get_or_create_folder()
        if not folder_id:
            return None

        try:
            from googleapiclient.http import MediaFileUpload

            file_path = Path(file_path)
            file_metadata = {
                'name': file_path.name,
                'parents': [folder_id]
            }

            media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = file.get('id')
            logger.info(f"Uploaded {file_path.name} to Drive: {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    def get_share_link(self, file_id: str) -> Optional[str]:
        """
        Make a file publicly readable and return its share link.
        """
        service = self._get_service()
        if not service:
            return None

        try:
            # Make file publicly readable
            service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()

            # Get the web view link
            file = service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()

            return file.get('webViewLink')

        except Exception as e:
            logger.error(f"Failed to get share link: {e}")
            return None

    def download_file(self, file_id: str, destination: str) -> bool:
        """
        Download a file from Google Drive.
        """
        service = self._get_service()
        if not service:
            return False

        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            with open(destination, 'wb') as f:
                f.write(fh.getvalue())

            return True

        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive."""
        service = self._get_service()
        if not service:
            return False

        try:
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def list_files(self) -> list[dict]:
        """List all files in the corpus folder."""
        service = self._get_service()
        if not service:
            return []

        folder_id = self._get_or_create_folder()
        if not folder_id:
            return []

        try:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name, mimeType, size, createdTime)'
            ).execute()

            return results.get('files', [])

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def is_available(self) -> bool:
        """Check if Drive integration is available."""
        return self._get_service() is not None
