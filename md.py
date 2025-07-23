import os
import yt_dlp
import re
import shutil

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

def create_m3u_playlist(m3u_dir, playlist_name, song_files, meta_path=None):
    m3u_file = os.path.join(m3u_dir, f"{playlist_name}.m3u")
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        if meta_path:
            m3u.write(f"#META_THUMBNAIL={meta_path}\n")
        for song_path in song_files:
            # Ruta relativa desde la carpeta de playlists
            rel_path = os.path.relpath(song_path, start=m3u_dir)
            m3u.write(rel_path + "\n")

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

def download(link, is_playlist, audio_only, file_format, songs_dir, archive_file="downloaded_archive.txt"):
    try:
        ext = f".{file_format}"
        outtmpl = os.path.join(songs_dir, sanitize_filename('%(title)s.%(ext)s'))
        if audio_only:
            ydl_opts = {
                'outtmpl': outtmpl,
                'format': f'bestaudio[ext=webm]/bestaudio',
                'writethumbnail': True,
                'download_archive': archive_file,
                'ignoreerrors': True,
                'sleep_interval': 0.1,
                'max_sleep_interval': 1,
                'noplaylist': not is_playlist,
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
                'writethumbnail': False,
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Error al descargar {link}: {e}")

def get_downloaded_files(songs_dir, before_files, file_format):
    after_files = set(os.listdir(songs_dir))
    new_files = after_files - before_files
    ext = f".{file_format}"
    return [os.path.join(songs_dir, f) for f in sorted(new_files) if f.endswith(ext)]

def move_playlist_metadata(songs_dir, meta_dir, playlist_name):
    os.makedirs(meta_dir, exist_ok=True)
    base = sanitize_filename(playlist_name)
    thumb_path = None
    for f in os.listdir(songs_dir):
        if f.lower().endswith('.jpg') and base in f:
            src = os.path.join(songs_dir, f)
            dst = os.path.join(meta_dir, f"{base}.jpg")
            try:
                shutil.move(src, dst)
                thumb_path = dst
            except Exception:
                pass
    # Devuelve la ruta relativa al archivo de metadata (miniatura) si existe
    if thumb_path:
        return os.path.relpath(thumb_path, start=os.path.dirname(meta_dir))
    return None

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
    default_songs_dir = os.path.expanduser("~/storage/music/Songs")
    default_playlists_dir = os.path.expanduser("~/storage/music/Playlists")
    metadata_dir = os.path.join(default_playlists_dir, ".metadata")
    os.makedirs(default_songs_dir, exist_ok=True)
    os.makedirs(default_playlists_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)
    while True:
        links = get_links()
        if not links:
            print("¡Hasta luego!")
            break
        modo = get_valid_option("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ", ["1", "2"])
        audio_only = modo == "1"
        if audio_only:
            file_format = get_valid_option("Formato de audio (opus/mp3/m4a): ", ["opus", "mp3", "m4a"])
        else:
            file_format = get_valid_option("Formato de video (mkv/mp4): ", ["mkv", "mp4"])
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
            songs_dir = default_songs_dir
            m3u_dir = default_playlists_dir
            before_files = set(os.listdir(songs_dir))
            print(f"Descargando playlist: {playlist_link}")
            download(playlist_link, True, audio_only, file_format, songs_dir)
            song_files = get_downloaded_files(songs_dir, before_files, file_format)
            # Usar rutas absolutas para calcular la ruta relativa
            song_files = [os.path.abspath(f) for f in song_files]
            meta_thumb = move_playlist_metadata(songs_dir, metadata_dir, playlist_name)
            # La ruta relativa de la miniatura (si existe) respecto a la carpeta de playlists
            if meta_thumb:
                meta_thumb_rel = os.path.relpath(meta_thumb, start=m3u_dir)
            else:
                meta_thumb_rel = None
            create_m3u_playlist(m3u_dir, playlist_name, song_files, meta_thumb_rel)
            print(f"Descarga y playlist .m3u finalizadas para: {playlist_name}\n")
        # Procesar canciones individuales
        if canciones:
            use_custom_folder = get_valid_option("¿Guardar canciones sueltas en carpeta personalizada? (s/n): ", ["s", "n"])
            if use_custom_folder == "s":
                carpeta = input("Nombre de la carpeta para guardar las canciones sueltas: ").strip()
                if not carpeta:
                    print("Debes ingresar un nombre para la carpeta.")
                    continue
                songs_dir = os.path.join(default_songs_dir, carpeta)
            else:
                songs_dir = default_songs_dir
            os.makedirs(songs_dir, exist_ok=True)
            for link in canciones:
                print(f"Descargando: {link}")
                download(link, False, audio_only, file_format, songs_dir)
            print("Descarga finalizada para canciones sueltas.\n")

if __name__ == "__main__":
    main()