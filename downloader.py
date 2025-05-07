import os, json, yt_dlp, re, platform

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

def create_m3u_playlist(playlist_path, playlist_name):
    """Generate an .m3u playlist file listing all songs in the directory."""
    m3u_file = os.path.join(playlist_path, f"{playlist_name}.m3u")
    
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for file in sorted(os.listdir(playlist_path)):
            if file.endswith(".opus"):  # Only include audio files
                m3u.write(file + "\n")

def sanitize_filename(filename):
    # Replace invalid characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def download_playlist(link, playlist_name, playlists_dir="Playlists", archive_file="downloaded_archive.txt"):

    try:
        # Create directory for the playlist
        playlist_path = os.path.join(playlists_dir, playlist_name)
        os.makedirs(playlist_path, exist_ok=True)

        delete_cmd = (
            f'if exist "{os.path.join(playlist_path, "%(title)s.%(ext)s.webp")}" del /f "{os.path.join(playlist_path, "%(title)s.%(ext)s.webp")}"'
            if platform.system() == 'Windows'
            else f'rm -- "{os.path.join(playlist_path, sanitize_filename("%(title)s.%(ext)s.webp"))}"'
        )

        ydl_opts = {
            'outtmpl': os.path.join(playlist_path, sanitize_filename('%(title)s.%(ext)s')),  # Sanitize filenames
            'format': 'bestaudio[ext=webm]/bestaudio',  # Prioritizes Opus format
            'writethumbnail': True,  # Required for embedding thumbnails
            'cookiefile': 'cookies.txt',
            'download_archive': archive_file,
            'ignoreerrors': True,
            'sleep_interval': 0.1,
            'max_sleep_interval': 1,
            'postprocessors': [
                # Opus audio extraction (no quality specified = best quality)
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                },
                # Metadata embedding (uses original metadata from YouTube)
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,  # Automatically uses original metadata
                },
                # Thumbnail embedding for Opus
                {
                    'key': 'EmbedThumbnail',
                }
                #wh,
                # Cleanup thumbnail file (Windows-compatible)
                # {
                #     'key': 'ExecAfterDownload',
                #     'exec_cmd': delete_cmd,
                #     'when': 'after_move'
                # }
            ],
            # 'ffmpeg_location': 'C:/path/to/ffmpeg.exe'  # Uncomment if needed
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