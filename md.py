import os
import yt_dlp
import re

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

def create_m3u_playlist(m3u_dir, playlist_name, song_files):
    m3u_file = os.path.join(m3u_dir, f"{playlist_name}.m3u")
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for song_path in song_files:
            m3u.write(song_path + "\n")

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

def main():
    print("=== Descargador de música/videos de YouTube ===")
    print("Escribe 'help' para ver instrucciones o presiona Enter para continuar.")
    if input().strip().lower() == "help":
        print("""
Instrucciones:
- Puedes pegar uno o varios enlaces de YouTube (uno por línea).
- Elige si quieres descargar una canción/video individual o una playlist completa.
- Elige si quieres solo audio o audio+video.
- Puedes elegir el formato de salida (audio: opus, mp3, m4a | video: mkv, mp4).
        """)
    default_songs_dir = "Music/Songs"
    default_playlists_dir = "Music/Playlists"
    os.makedirs(default_songs_dir, exist_ok=True)
    os.makedirs(default_playlists_dir, exist_ok=True)
    while True:
        links = get_links()
        if not links:
            print("¡Hasta luego!")
            break
        tipo = get_valid_option("¿Qué deseas descargar? (1) Canción/Video individual, (2) Playlist completa [1/2]: ", ["1", "2"])
        is_playlist = tipo == "2"
        if is_playlist:
            playlist_name = input("Nombre de la playlist para el archivo .m3u: ").strip()
            if not playlist_name:
                print("Debes ingresar un nombre para la playlist.")
                continue
            songs_dir = default_songs_dir
            m3u_dir = default_playlists_dir
        else:
            use_custom_folder = get_valid_option("¿Quieres guardar en una carpeta personalizada? (s/n): ", ["s", "n"])
            if use_custom_folder == "s":
                playlist_name = input("Nombre de la carpeta para guardar la canción: ").strip()
                if not playlist_name:
                    print("Debes ingresar un nombre para la carpeta.")
                    continue
                songs_dir = os.path.join(default_songs_dir, playlist_name)
                m3u_dir = None
            else:
                playlist_name = "CancionesSueltas"
                songs_dir = default_songs_dir
                m3u_dir = None
            os.makedirs(songs_dir, exist_ok=True)
        modo = get_valid_option("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ", ["1", "2"])
        audio_only = modo == "1"
        if audio_only:
            file_format = get_valid_option("Formato de audio (opus/mp3/m4a): ", ["opus", "mp3", "m4a"])
        else:
            file_format = get_valid_option("Formato de video (mkv/mp4): ", ["mkv", "mp4"])
        if is_playlist:
            before_files = set(os.listdir(songs_dir))
            for link in links:
                print(f"Descargando: {link}")
                download(link, is_playlist, audio_only, file_format, songs_dir)
            # Detectar los archivos nuevos descargados
            song_files = get_downloaded_files(songs_dir, before_files, file_format)
            # Guardar el .m3u en la carpeta de playlists, con rutas relativas a la carpeta de playlists
            rel_song_files = [os.path.relpath(f, start=default_playlists_dir) for f in song_files]
            create_m3u_playlist(m3u_dir, playlist_name, rel_song_files)
            print(f"Descarga y playlist .m3u finalizadas para: {playlist_name}\n")
        else:
            for link in links:
                print(f"Descargando: {link}")
                download(link, is_playlist, audio_only, file_format, songs_dir)
            print(f"Descarga finalizada para: {playlist_name}\n")

if __name__ == "__main__":
    main()