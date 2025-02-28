import os
import json
import yt_dlp

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

def create_m3u_playlist(playlist_path, playlist_name):
    """Generate an .m3u playlist file listing all songs in the directory."""
    m3u_file = os.path.join(playlist_path, f"{playlist_name}.m3u")
    
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for file in sorted(os.listdir(playlist_path)):
            if file.endswith(".mp3"):  # Only include audio files
                m3u.write(file + "\n")

def download_playlist(link, playlist_name, playlists_dir="Playlists", archive_file="downloaded_archive.txt"):
    try:
        # Create directory for the playlist
        playlist_path = os.path.join(playlists_dir, playlist_name)
        os.makedirs(playlist_path, exist_ok=True)

        ydl_opts = {
            'outtmpl': os.path.join(playlist_path, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': 'cookies.txt',  # Use cookies to bypass restrictions
            'noplaylist': True,  # Ensures each entry is treated as a playlist
            'download_archive': archive_file,  # Prevents re-downloading
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        # Create an .m3u playlist after downloading
        create_m3u_playlist(playlist_path, playlist_name)

    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Failed to download {link}: {e}")

def main():
    json_file = "links.json"  # Change this to the actual JSON file path

    # Load the JSON file
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            playlists = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return

    if not isinstance(playlists, list) or not all('link' in p and 'playlist_name' in p for p in playlists):
        print("Error: JSON must be a list of objects with 'link' and 'playlist_name'.")
        return
    
    os.makedirs("Playlists", exist_ok=True)
    archive_file = "downloaded_archive.txt"

    for playlist in playlists:
        download_playlist(playlist['link'], playlist['playlist_name'], archive_file=archive_file)

if __name__ == "__main__":
    main()
