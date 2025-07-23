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
            # Calcula la ruta relativa desde la carpeta de playlists
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

def download(link, is_playlist, audio_only, file_format, media_dir, archive_file):
    try:
        ext = f".{file_format}"
        outtmpl = os.path.join(media_dir, sanitize_filename('%(title)s.%(ext)s'))
        if audio_only:
            ydl_opts = {
                'outtmpl': outtmpl,
                'format': f'bestaudio[ext=webm]/bestaudio',
                'download_archive': archive_file,
                'ignoreerrors': True,
                'sleep_interval': 0.1,
                'max_sleep_interval': 1,
                'noplaylist': not is_playlist,
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': file_format},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
            }
            # Solo para descargas individuales: embebe thumbnail
            if not is_playlist:
                ydl_opts['writethumbnail'] = True
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
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
                'postprocessors': [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat': file_format},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
            }
            # Solo para descargas individuales: embebe thumbnail
            if not is_playlist:
                ydl_opts['writethumbnail'] = True
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Error al descargar {link}: {e}")

def get_downloaded_files(media_dir, before_files, file_format):
    after_files = set(os.listdir(media_dir))
    new_files = after_files - before_files
    ext = f".{file_format}"
    return [os.path.join(media_dir, f) for f in sorted(new_files) if f.endswith(ext)]

def main():
    print("=== Descargador de música/videos de YouTube ===")
    print("Escribe 'help' para ver instrucciones o presiona Enter para continuar.")
    if input().strip().lower() == "help":
        print("""
Instrucciones:
- Puedes pegar uno o varios enlaces de YouTube (uno por línea).
- El programa detecta automáticamente si cada enlace es playlist o canción.
- Elige si quieres solo audio o audio+video.
- Puedes elegir el formato de salida (audio: opus, mp3, m4a | video: mkv, mp4).
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
        if audio_only:
            file_format = input("Formato de audio (opus/mp3/m4a) [opus]: ").strip().lower()
            if file_format not in ["opus", "mp3", "m4a"]:
                file_format = "opus"
            media_dir = songs_dir
            playlists_dir = songs_playlists_dir
            archive_file = songs_archive_file
        else:
            file_format = input("Formato de video (mkv/mp4) [mp4]: ").strip().lower()
            if file_format not in ["mkv", "mp4"]:
                file_format = "mp4"
            media_dir = videos_dir
            playlists_dir = videos_playlists_dir
            archive_file = videos_archive_file
        playlists = []
        canciones = []
        for link in links:
            if is_youtube_playlist(link):
                playlists.append(link)
            else:
                canciones.append(link)
        # Procesar playlists
        for playlist_link in playlists:
            playlist_name = input(f"Nombre para la playlist (.m3u) de:\n{playlist_link}\n> ").strip()
            if not playlist_name:
                print("Debes ingresar un nombre para la playlist.")
                continue
            before_files = set(os.listdir(media_dir))
            print(f"Descargando playlist: {playlist_link}")
            download(playlist_link, True, audio_only, file_format, media_dir, archive_file)
            media_files = get_downloaded_files(media_dir, before_files, file_format)
            create_m3u_playlist(playlists_dir, playlist_name, media_files)
            print(f"Playlist .m3u creada en: {os.path.join(playlists_dir, playlist_name)}.m3u\n")
        # Procesar canciones/videos individuales
        if canciones:
            for link in canciones:
                print(f"Descargando: {link}")
                download(link, False, audio_only, file_format, media_dir, archive_file)
            print("Descarga finalizada para canciones/videos sueltos.\n")

if __name__ == "__main__":
    main()