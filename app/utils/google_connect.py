import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    def __init__(self, client_secrets_file, api_service_name, api_version, scopes, video_folder):
        self.client_secrets_file = client_secrets_file
        self.api_service_name = api_service_name
        self.api_version = api_version
        self.scopes = scopes
        self.video_folder = video_folder
        self.youtube = self.get_authenticated_service()

    def get_authenticated_service(self):
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, self.scopes)
        credentials = flow.run_console()
        return build(self.api_service_name, self.api_version, credentials=credentials)

    def upload_video(self, file_name, title, description, category_id, keywords, privacy_status):
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': keywords,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }
        upload_file_path = os.path.join(self.video_folder, file_name)
        media = MediaFileUpload(upload_file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
        request = self.youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        print(f"Upload Complete. Video ID: {response['id']}")

# Usage example:
if __name__ == "__main__":
    uploader = YouTubeUploader(
        client_secrets_file='client_secrets.json',
        api_service_name='youtube',
        api_version='v3',
        scopes=['https://www.googleapis.com/auth/youtube.upload'],
        video_folder='translated'
    )
    uploader.upload_video(
        file_name='your_video.mp4',
        title='Your Video Title',
        description='Your video description',
        category_id='22',  # Example category ID
        keywords=['keyword1', 'keyword2'],
        privacy_status='private'  # or 'public' or 'unlisted'
    )