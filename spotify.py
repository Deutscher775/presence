import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from typing import Optional, Dict
import yt_dlp
import os


class SpotifyHandler:
    """Simple Spotify handler to get song picture and video information."""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Spotify handler with credentials.
        
        Args:
            client_id: Spotify API client ID
            client_secret: Spotify API client secret
        """
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
    
    def get_song_picture(self, track_id: str) -> Optional[str]:
        """
        Get the album artwork URL for a song.
        
        Args:
            track_id: Spotify track ID or URI
            
        Returns:
            URL of the highest quality album artwork, or None if not found
        """
        try:
            track = self.sp.track(track_id)
            album = track.get('album', {})
            images = album.get('images', [])
            
            if images:
                # Return the highest quality image (first one)
                return images[0]['url']
            return None
        except Exception as e:
            print(f"Error getting song picture: {e}")
            return None
    
    def get_song_video(self, track_id: str, output_dir: str = "videos") -> Dict[str, Optional[str]]:
        """
        Download a 30-second clip from YouTube video starting at second 20.
        Searches YouTube and downloads the video segment as MP4.
        
        Args:
            track_id: Spotify track ID or URI
            output_dir: Directory to save the video file (default: "videos")
            
        Returns:
            Dictionary with video information including local MP4 file path
        """
        try:
            track = self.sp.track(track_id)
            track_name = track.get('name', '')
            artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Search YouTube for the song using yt-dlp
            search_query = f"ytsearch1:{artists} - {track_name} official video"
            
            # Sanitize filename
            safe_filename = f"{artists} - {track_name}".replace('/', '-').replace('\\', '-').replace(':', '-')
            output_path = os.path.join(output_dir, f"{safe_filename}_clip.mp4")
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4][height<=144]/bestvideo[height<=144]/bestvideo',  # Video only, max 144p for speed
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                'download_ranges': yt_dlp.utils.download_range_func(None, [(30, 45)]),  # 30-45 seconds (15 sec duration)
                'force_keyframes_at_cuts': True,
            }
            
            youtube_url = None
            video_title = None
            video_duration = None
            video_thumbnail = None
            downloaded_file = None
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(search_query, download=True)
                
                if result and 'entries' in result and len(result['entries']) > 0:
                    video = result['entries'][0]
                    video_id = video.get('id')
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_title = video.get('title')
                    video_duration = video.get('duration')
                    video_thumbnail = video.get('thumbnail')
                    
                    # Check if file was downloaded
                    if os.path.exists(output_path):
                        downloaded_file = output_path
            
            return {
                'track_name': track_name,
                'artists': artists,
                'youtube_url': youtube_url,
                'video_title': video_title,
                'video_duration': video_duration,
                'video_thumbnail': video_thumbnail,
                'spotify_url': track.get('external_urls', {}).get('spotify'),
                'downloaded_file': downloaded_file,
                'clip_start': 30,
                'clip_duration': 15
            }
        except Exception as e:
            print(f"Error getting song video info: {e}")
            import traceback
            traceback.print_exc()
            return {
                'track_name': None,
                'artists': None,
                'youtube_url': None,
                'video_title': None,
                'spotify_url': None,
                'downloaded_file': None,
                'error': str(e)
            }
    
    def get_song_info(self, track_id: str) -> Dict:
        """
        Get comprehensive song information including picture and video.
        
        Args:
            track_id: Spotify track ID or URI
            
        Returns:
            Dictionary with song information, picture URL, and video info
        """
        try:
            track = self.sp.track(track_id)
            
            return {
                'name': track.get('name'),
                'artists': [artist['name'] for artist in track.get('artists', [])],
                'album': track.get('album', {}).get('name'),
                'picture_url': self.get_song_picture(track_id),
                'video_info': self.get_song_video(track_id),
                'duration_ms': track.get('duration_ms'),
                'preview_url': track.get('preview_url'),
                'spotify_url': track.get('external_urls', {}).get('spotify')
            }
        except Exception as e:
            print(f"Error getting song info: {e}")
            return {'error': str(e)}
