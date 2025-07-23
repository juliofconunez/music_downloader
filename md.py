import os
import yt_dlp
import re
import platform

def log_failed_download(link, reason):
    with open("failed_downloads.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{link} - {reason}\n")

def create_m3u_playlist(playlist_path, playlist_name, ext):
    m3u_file = os.path.join(playlist_path, f"{playlist_name}.m3u")
    with open(m3u_file, "w", encoding="utf-8") as m3u:
        for file in sorted(os.listdir(playlist_path)):
            if file.endswith(ext):
                m3u.write(file + "\n")

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

def download(link, playlist_name, is_playlist, audio_only, file_format, playlists_dir, archive_file="downloaded_archive.txt"):
    try:
        playlist_path = os.path.join(playlists_dir, playlist_name)
        os.makedirs(playlist_path, exist_ok=True)
        ext = f".{file_format}"
        outtmpl = os.path.join(playlist_path, sanitize_filename('%(title)s.%(ext)s'))
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
        create_m3u_playlist(playlist_path, playlist_name, ext)
    except Exception as e:
        log_failed_download(link, str(e))
        print(f"Error al descargar {link}: {e}")

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
    playlists_dir = "Playlists"
    os.makedirs(playlists_dir, exist_ok=True)
    while True:
        links = get_links()
        if not links:
            print("¡Hasta luego!")
            break
        playlist_name = input("Nombre de la playlist/carpeta para guardar: ").strip()
        if not playlist_name:
            print("Debes ingresar un nombre para la playlist.")
            continue
        tipo = get_valid_option("¿Qué deseas descargar? (1) Canción/Video individual, (2) Playlist completa [1/2]: ", ["1", "2"])
        is_playlist = tipo == "2"
        modo = get_valid_option("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ", ["1", "2"])
        audio_only = modo == "1"
        if audio_only:
            file_format = get_valid_option("Formato de audio (opus/mp3/m4a): ", ["opus", "mp3", "m4a"])
        else:
            file_format = get_valid_option("Formato de video (mkv/mp4): ", ["mkv", "mp4"])
        for link in links:
            print(f"Descargando: {link}")
            download(link, playlist_name, is_playlist, audio_only, file_format, playlists_dir)
        print(f"Descarga finalizada para: {playlist_name}\n")

if __name__ == "__main__":
    main()