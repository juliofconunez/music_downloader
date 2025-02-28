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
            'cookiefile': 'cookies.txt',
            'download_archive': archive_file,  # Prevents re-downloading
            'ignoreerrors': True,
            'sleep_interval': 0.5,  # Adds a 1-second delay between requests
            'max_sleep_interval': 3
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        # Create an .m3u playlist after downloading
        create_m3u_playlist(playlist_path, playlist_name)

    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Failed to download {link}: {e}")


def process_json_files(directory):
    """Process all JSON files in the given directory."""
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]

    if not json_files:
        print("No JSON files found in the 'Links' directory.")
        return

    for json_file in json_files:
        json_path = os.path.join(directory, json_file)

        # Extract artist name from file name (e.g., "Eminem.json" -> "Eminem")
        artist_name = os.path.splitext(json_file)[0]

        # Load JSON file
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                playlists = json.load(f)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            continue

        if not isinstance(playlists, list) or not all('link' in p and 'playlist_name' in p for p in playlists):
            print(f"Error: {json_file} must contain a list of objects with 'link' and 'playlist_name'.")
            continue

        # Create artist directory inside "Playlists"
        artist_dir = os.path.join("Playlists", artist_name)
        os.makedirs(artist_dir, exist_ok=True)

        #archive_file = os.path.join(artist_dir, "downloaded_archive.txt")  # Store archive per artist

        for playlist in playlists:
            download_playlist('https://www.youtube.com/playlist?list='+playlist['link'], 
                              playlist['playlist_name'], 
                              artist_dir 
                              #,archive_file
                              )

def main():
    links_dir = "Links"
    
    if not os.path.exists(links_dir):
        print(f"Directory '{links_dir}' not found. Creating it...")
        os.makedirs(links_dir, exist_ok=True)
        return

    process_json_files(links_dir)

if __name__ == "__main__":
    main()