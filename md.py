import os
import yt_dlp
import re

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_links():
    print("Pega los enlaces de YouTube (uno por línea). Deja vacío y presiona Enter para terminar:")
    return [l.strip() for l in iter(input, '') if l.strip()]

def is_youtube_playlist(link):
    return "playlist?list=" in link or "&list=" in link

def get_yt_playlist_info(playlist_url):
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'skip_download': True}) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        entries = info.get('entries', info.get('items', []))
        return sanitize_filename(info.get('title', 'playlist')), [e['id'] for e in entries if 'id' in e]

def find_file_by_id(media_dir, yt_id):
    for fname in os.listdir(media_dir):
        if re.search(rf'\s\[{re.escape(yt_id)}\]\.', fname):
            return os.path.join(media_dir, fname)
    return None

def remove_leftover_images(media_dir):
    for fname in os.listdir(media_dir):
        if fname.lower().endswith(('.jpg', '.jpeg', '.webp', '.png')):
            try: os.remove(os.path.join(media_dir, fname))
            except Exception: pass

def download(link, is_playlist, audio_only, file_format, media_dir):
    outtmpl = os.path.join(media_dir, '%(title)s [%(id)s].%(ext)s')
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': f'bestaudio[ext=webm]/bestaudio' if audio_only else 'bestvideo+bestaudio/best',
        'ignoreerrors': True,
        'sleep_interval': 0.1,
        'max_sleep_interval': 1,
        'noplaylist': not is_playlist,
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': file_format} if audio_only else {'key': 'FFmpegVideoConvertor', 'preferedformat': file_format},
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            {'key': 'EmbedThumbnail'},
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    remove_leftover_images(media_dir)

def create_m3u_playlist(m3u_dir, playlist_name, media_files):
    m3u_file = os.path.join(m3u_dir, f"{playlist_name}.m3u")
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for media_path in media_files:
            rel_path = os.path.relpath(media_path, start=m3u_dir)
            m3u.write(f"{rel_path}\n")

def main():
    print("=== Descargador de música/videos de YouTube ===")
    print("Escribe 'help' para ver instrucciones o presiona Enter para continuar.")
    if input().strip().lower() == "help":
        print("Instrucciones:\n- Pega enlaces de YouTube (uno por línea).\n- El programa detecta playlists o canciones.\n- Elige solo audio o audio+video.\n")
    storage = {
        "audio": {"media": os.path.expanduser("~/storage/music/Songs"), "playlists": os.path.expanduser("~/storage/music/Playlists"), "format": "opus"},
        "video": {"media": os.path.expanduser("~/storage/movies/Videos"), "playlists": os.path.expanduser("~/storage/movies/Playlists"), "format": "mp4"},
    }
    for k in storage:
        os.makedirs(storage[k]["media"], exist_ok=True)
        os.makedirs(storage[k]["playlists"], exist_ok=True)
    while True:
        links = get_links()
        if not links:
            print("¡Hasta luego!")
            break
        modo = input("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ").strip()
        key = "audio" if modo == "1" else "video"
        p = storage[key]
        playlists, canciones = [], []
        for link in links:
            (playlists if is_youtube_playlist(link) else canciones).append(link)
        for playlist_link in playlists:
            playlist_name, yt_ids = get_yt_playlist_info(playlist_link)
            print(f"Procesando playlist: {playlist_link}")
            files = []
            for yt_id in yt_ids:
                fpath = find_file_by_id(p["media"], yt_id)
                if not fpath:
                    # Descarga solo el video/canción faltante
                    download(f"https://www.youtube.com/watch?v={yt_id}", False, key == "audio", p["format"], p["media"])
                    fpath = find_file_by_id(p["media"], yt_id)
                if fpath:
                    files.append(fpath)
            create_m3u_playlist(p["playlists"], playlist_name, files)
            print(f"Playlist .m3u creada en: {os.path.join(p['playlists'], playlist_name)}.m3u\n")
        for link in canciones:
            print(f"Procesando: {link}")
            with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(link, download=False)
                yt_id = info['id']
            fpath = find_file_by_id(p["media"], yt_id)
            if not fpath:
                download(link, False, key == "audio", p["format"], p["media"])
        if canciones:
            print("Descarga finalizada para canciones/videos sueltos.\n")

if __name__ == "__main__":
    main()