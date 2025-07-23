import os
import yt_dlp
import re

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

def create_m3u_playlist(m3u_dir, playlist_name, media_files):
    m3u_file = os.path.join(m3u_dir, f"{playlist_name}.m3u")
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for media_path in media_files:
            rel_path = os.path.relpath(media_path, start=m3u_dir)
            m3u.write(f"{rel_path}\n")

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_valid_option(prompt, options):
    while True:
        value = input(prompt).strip()
        if value in options:
            return value
        print(f"Opción no válida. Opciones válidas: {', '.join(options)}")

def get_links():
    print("Pega los enlaces de YouTube (uno por línea). Deja vacío y presiona Enter para terminar:")
    links = []
    while True:
        link = input().strip()
        if not link:
            break
        links.append(link)
    return links

def is_youtube_playlist(link):
    return "playlist?list=" in link or "&list=" in link

def get_yt_playlist_info(playlist_url):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        entries = info.get('entries', info.get('items', []))
        playlist_title = info.get('title', 'playlist')
        yt_ids = [entry['id'] for entry in entries if 'id' in entry]
        return sanitize_filename(playlist_title), yt_ids

def find_files_by_ids(media_dir, yt_ids, file_format):
    files = []
    for fname in os.listdir(media_dir):
        if fname.endswith(f".{file_format}"):
            for yt_id in yt_ids:
                if yt_id in fname:
                    files.append(os.path.join(media_dir, fname))
                    break
    return files

def remove_leftover_images(media_dir):
    for fname in os.listdir(media_dir):
        if fname.lower().endswith(('.jpg', '.jpeg', '.webp', '.png')):
            try:
                os.remove(os.path.join(media_dir, fname))
            except Exception:
                pass

def download(link, is_playlist, audio_only, file_format, media_dir, archive_file):
    try:
        outtmpl = os.path.join(media_dir, '%(title)s [%(id)s].%(ext)s')
        if audio_only:
            ydl_opts = {
                'outtmpl': outtmpl,
                'format': f'bestaudio[ext=webm]/bestaudio',
                'download_archive': archive_file,
                'ignoreerrors': True,
                'sleep_interval': 0.1,
                'max_sleep_interval': 1,
                'noplaylist': not is_playlist,
                'writethumbnail': True,
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': file_format},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                    {'key': 'EmbedThumbnail'},
                ],
            }
        else:
            ydl_opts = {
                'outtmpl': outtmpl,
                'format': 'bestvideo+bestaudio/best',
                'download_archive': archive_file,
                'ignoreerrors': True,
                'sleep_interval': 0.1,
                'max_sleep_interval': 1,
                'noplaylist': not is_playlist,
                'merge_output_format': file_format,
                'writethumbnail': True,
                'postprocessors': [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat': file_format},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                    {'key': 'EmbedThumbnail'},
                ],
            }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        remove_leftover_images(media_dir)
    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Error al descargar {link}: {e}")

def get_downloaded_files(media_dir, before_files, file_format):
    after_files = set(os.listdir(media_dir))
    new_files = after_files - before_files
    ext = f".{file_format}"
    return [os.path.join(media_dir, f) for f in sorted(new_files) if f.endswith(ext)]

def clean_archive_for_missing_files(media_dir, archive_file, file_format, yt_ids):
    """Elimina del archive SOLO los IDs de yt_ids que no tienen archivo en disco."""
    if not os.path.exists(archive_file):
        return
    with open(archive_file, "r", encoding="utf-8") as f:
        archived_ids = [line.strip() for line in f if line.strip()]
    ids_missing = []
    for yt_id in yt_ids:
        if yt_id in archived_ids:
            found = False
            for fname in os.listdir(media_dir):
                if fname.endswith(f".{file_format}") and yt_id in fname:
                    found = True
                    break
            if not found:
                ids_missing.append(yt_id)
    # Si hay IDs a eliminar, reescribe el archive sin ellos
    if ids_missing:
        with open(archive_file, "w", encoding="utf-8") as f:
            for id_line in archived_ids:
                if id_line not in ids_missing:
                    f.write(id_line + "\n")

def main():
    print("=== Descargador de música/videos de YouTube ===")
    print("Escribe 'help' para ver instrucciones o presiona Enter para continuar.")
    if input().strip().lower() == "help":
        print("""
Instrucciones:
- Puedes pegar uno o varios enlaces de YouTube (uno por línea).
- El programa detecta automáticamente si cada enlace es playlist o canción.
- Elige si quieres solo audio o audio+video.
        """)
    songs_dir = os.path.expanduser("~/storage/music/Songs")
    songs_playlists_dir = os.path.expanduser("~/storage/music/Playlists")
    videos_dir = os.path.expanduser("~/storage/movies/Videos")
    videos_playlists_dir = os.path.expanduser("~/storage/movies/Playlists")
    os.makedirs(songs_dir, exist_ok=True)
    os.makedirs(songs_playlists_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(videos_playlists_dir, exist_ok=True)
    songs_archive_file = "downloaded_songs_archive.txt"
    videos_archive_file = "downloaded_videos_archive.txt"
    while True:
        links = get_links()
        if not links:
            print("¡Hasta luego!")
            break
        modo = get_valid_option("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ", ["1", "2"])
        audio_only = modo == "1"
        file_format = "opus" if audio_only else "mp4"
        media_dir = songs_dir if audio_only else videos_dir
        playlists_dir = songs_playlists_dir if audio_only else videos_playlists_dir
        archive_file = songs_archive_file if audio_only else videos_archive_file
        playlists = []
        canciones = []
        for link in links:
            if is_youtube_playlist(link):
                playlists.append(link)
            else:
                canciones.append(link)
        # Procesar playlists
        for playlist_link in playlists:
            playlist_name, yt_ids = get_yt_playlist_info(playlist_link)
            print(f"Descargando playlist: {playlist_link}")
            clean_archive_for_missing_files(media_dir, archive_file, file_format, yt_ids)
            download(playlist_link, True, audio_only, file_format, media_dir, archive_file)
            all_files = find_files_by_ids(media_dir, yt_ids, file_format)
            create_m3u_playlist(playlists_dir, playlist_name, all_files)
            print(f"Playlist .m3u creada en: {os.path.join(playlists_dir, playlist_name)}.m3u\n")
        # Procesar canciones/videos individuales
        if canciones:
            for link in canciones:
                print(f"Descargando: {link}")
                # Si quieres la misma lógica para canciones individuales, primero obtén el ID:
                # yt_id = ... (puedes extraerlo usando yt_dlp.extract_info(link, download=False)['id'])
                # clean_archive_for_missing_files(media_dir, archive_file, file_format, [yt_id])
                download(link, False, audio_only, file_format, media_dir, archive_file)
            print("Descarga finalizada para canciones/videos sueltos.\n")

if __name__ == "__main__":
    main()