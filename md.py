import os
import yt_dlp
import re
import shutil

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

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

def remove_leftover_images(media_dir):
    for fname in os.listdir(media_dir):
        if fname.lower().endswith(('.jpg', '.jpeg', '.webp', '.png')):
            try: os.remove(os.path.join(media_dir, fname))
            except Exception: pass

def clean_archive_for_missing_files(media_dir, archive_file, file_format, yt_ids):
    if not os.path.exists(archive_file): return
    with open(archive_file, "r", encoding="utf-8") as f:
        archived_ids = [line.strip() for line in f if line.strip()]
    ids_missing = []
    for yt_id in yt_ids:
        if yt_id in archived_ids and not any(yt_id in fname and fname.endswith(f".{file_format}") for fname in os.listdir(media_dir)):
            ids_missing.append(yt_id)
    if ids_missing:
        with open(archive_file, "w", encoding="utf-8") as f:
            for id_line in archived_ids:
                if id_line not in ids_missing:
                    f.write(id_line + "\n")

def download(link, is_playlist, audio_only, file_format, media_dir, archive_file):
    outtmpl = os.path.join(media_dir, '%(title)s [%(id)s].%(ext)s')
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': f'bestaudio[ext=webm]/bestaudio' if audio_only else 'bestvideo+bestaudio/best',
        'download_archive': archive_file,
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
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        remove_leftover_images(media_dir)
    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Error al descargar {link}: {e}")

def move_all_files(src_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    for fname in os.listdir(src_dir):
        src_path = os.path.join(src_dir, fname)
        dst_path = os.path.join(dst_dir, fname)
        if os.path.isfile(src_path):
            shutil.move(src_path, dst_path)

def create_m3u_playlist(m3u_dir, playlist_name, media_files):
    m3u_file = os.path.join(m3u_dir, f"{playlist_name}.m3u")
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for media_path in media_files:
            rel_path = os.path.relpath(media_path, start=m3u_dir)
            m3u.write(f"{rel_path}\n")

def remove_empty_dir(directory):
    try:
        if os.path.isdir(directory) and not os.listdir(directory):
            os.rmdir(directory)
    except Exception:
        pass

def main():
    print("=== Descargador de música/videos de YouTube ===")
    print("Escribe 'help' para ver instrucciones o presiona Enter para continuar.")
    if input().strip().lower() == "help":
        print("Instrucciones:\n- Pega enlaces de YouTube (uno por línea).\n- El programa detecta playlists o canciones.\n- Elige solo audio o audio+video.\n")
    # Rutas locales
    base_dir = os.path.abspath(os.path.dirname(__file__))
    local = {
        "audio": {"media": os.path.join(base_dir, "Songs"), "playlists": os.path.join(base_dir, "Playlists"), "archive": os.path.join(base_dir, "downloaded_songs_archive.txt"), "format": "opus"},
        "video": {"media": os.path.join(base_dir, "Videos"), "playlists": os.path.join(base_dir, "VideoPlaylists"), "archive": os.path.join(base_dir, "downloaded_videos_archive.txt"), "format": "mp4"},
    }
    # Rutas destino memoria interna
    storage = {
        "audio": {"media": os.path.expanduser("~/storage/music/Songs"), "playlists": os.path.expanduser("~/storage/music/Playlists")},
        "video": {"media": os.path.expanduser("~/storage/movies/Videos"), "playlists": os.path.expanduser("~/storage/movies/Playlists")},
    }
    for k in local:
        os.makedirs(local[k]["media"], exist_ok=True)
        os.makedirs(local[k]["playlists"], exist_ok=True)
    while True:
        links = get_links()
        if not links:
            print("¡Hasta luego!")
            break
        modo = input("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ").strip()
        key = "audio" if modo == "1" else "video"
        p = local[key]
        playlists, canciones = [], []
        for link in links:
            (playlists if is_youtube_playlist(link) else canciones).append(link)
        for playlist_link in playlists:
            playlist_name, yt_ids = get_yt_playlist_info(playlist_link)
            print(f"Descargando playlist: {playlist_link}")
            clean_archive_for_missing_files(p["media"], p["archive"], p["format"], yt_ids)
            download(playlist_link, True, key == "audio", p["format"], p["media"], p["archive"])
            files = [os.path.join(p["media"], f) for f in os.listdir(p["media"]) if any(yt_id in f for yt_id in yt_ids) and f.endswith(f".{p['format']}")]
            create_m3u_playlist(p["playlists"], playlist_name, files)
            print(f"Playlist .m3u creada en: {os.path.join(p['playlists'], playlist_name)}.m3u\n")
        for link in canciones:
            print(f"Descargando: {link}")
            with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(link, download=False)
                yt_id = info['id']
            clean_archive_for_missing_files(p["media"], p["archive"], p["format"], [yt_id])
            download(link, False, key == "audio", p["format"], p["media"], p["archive"])
        if canciones:
            print("Descarga finalizada para canciones/videos sueltos.\n")
        # Mover todo al final del ciclo
        move_all_files(p["media"], storage[key]["media"])
        move_all_files(p["playlists"], storage[key]["playlists"])
        # Eliminar directorios locales si están vacíos
        remove_empty_dir(p["media"])
        remove_empty_dir(p["playlists"])
        print("Archivos movidos a la memoria interna.")

if __name__ == "__main__":
    main()