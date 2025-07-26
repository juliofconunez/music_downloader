#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import yt_dlp
import re
import glob
import json
def get_album_links_from_json(albums_dir):
    album_links = []
    for json_file in glob.glob(os.path.join(albums_dir, '*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                playlist_name = entry.get('playlist_name')
                link_id = entry.get('link')
                if playlist_name and link_id:
                    if isinstance(link_id, list):
                        for lid in link_id:
                            album_links.append({'playlist_name': playlist_name, 'link': lid})
                    else:
                        album_links.append({'playlist_name': playlist_name, 'link': link_id})
    return album_links

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

def download(link, is_playlist, audio_only, file_format, media_dir, cookies_file=None):
    outtmpl = os.path.join(media_dir, sanitize_filename('%(title)s [%(id)s].%(ext)s'))
    ydl_opts = {
        'outtmpl': outtmpl,
        # Limitar calidad de video a 720p si es video, audio igual que antes
        'format': 'bestaudio/best' if audio_only else 'bestvideo[height<=720]+bestaudio/best[height<=720]',
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
    
    # Si se proporciona un archivo de cookies, agregarlo a las opciones
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
    
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
        print("Instrucciones:\n- Pega enlaces de YouTube (uno por línea).\n- El programa detecta playlists o canciones.\n- Elige solo audio o audio+video.\n- También puedes descargar todos los álbumes definidos en la carpeta Albums.\n")
    storage = {
        "audio": {"media": os.path.expanduser("~/storage/music/Songs"), "playlists": os.path.expanduser("~/storage/music/Playlists"), "format": "opus"},
        "video": {"media": os.path.expanduser("~/storage/movies/Videos"), "playlists": os.path.expanduser("~/storage/movies/Playlists"), "format": "mp4"},
    }
    for k in storage:
        os.makedirs(storage[k]["media"], exist_ok=True)
        os.makedirs(storage[k]["playlists"], exist_ok=True)

    # Verificar si existe archivo de cookies para YouTube Premium
    cookies_file = os.path.expanduser("~/cookies.txt")
    if not os.path.exists(cookies_file):
        cookies_file = None
    else:
        print(f"Usando cookies de YouTube Premium: {cookies_file}")

    albums_dir = os.path.expanduser("~/discos")
    print(f"Buscando álbumes en: {albums_dir}")
    if not os.path.isdir(albums_dir):
        print(f"La carpeta 'discos' no existe en: {albums_dir}")
        print("Por favor crea la carpeta y agrega archivos .json de álbumes.")
        return

    while True:
        print("¿Qué deseas hacer?")
        print("1) Ingresar links manualmente")
        print("2) Descargar todos los álbumes de la carpeta discos")
        opcion = input("Elige una opción [1/2]: ").strip()
        if opcion == "2":
            album_links = get_album_links_from_json(albums_dir)
            if not album_links:
                print("No se encontraron álbumes en la carpeta discos.")
                continue
            modo = input("¿Solo audio o audio+video? (1) Solo audio, (2) Audio+Video [1/2]: ").strip()
            key = "audio" if modo == "1" else "video"
            p = storage[key]
            for album in album_links:
                playlist_name, playlist_link = album['playlist_name'], album['link']
                print(f"Procesando álbum: {playlist_name}")
                album_dir = os.path.join(storage["audio"]["media"], sanitize_filename(playlist_name))
                os.makedirs(album_dir, exist_ok=True)
                files = []
                # Si es playlist de YouTube
                if is_youtube_playlist(playlist_link):
                    yt_playlist_name, yt_ids = get_yt_playlist_info(playlist_link)
                    for yt_id in yt_ids:
                        fpath = find_file_by_id(album_dir, yt_id)
                        if not fpath:
                            download(f"https://www.youtube.com/watch?v={yt_id}", False, True, storage["audio"]["format"], album_dir, cookies_file)
                            fpath = find_file_by_id(album_dir, yt_id)
                        if fpath:
                            files.append(fpath)
                # Si es una lista de videos individuales
                elif isinstance(playlist_link, list):
                    for video_link in playlist_link:
                        print(f"Procesando video: {video_link}")
                        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                            info = ydl.extract_info(video_link, download=False)
                            yt_id = info['id']
                        fpath = find_file_by_id(album_dir, yt_id)
                        if not fpath:
                            download(video_link, False, True, storage["audio"]["format"], album_dir, cookies_file)
                            fpath = find_file_by_id(album_dir, yt_id)
                        if fpath:
                            files.append(fpath)
                # Si es un solo link de video individual
                else:
                    print(f"Procesando video: {playlist_link}")
                    with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                        info = ydl.extract_info(playlist_link, download=False)
                        yt_id = info['id']
                    fpath = find_file_by_id(album_dir, yt_id)
                    if not fpath:
                        download(playlist_link, False, True, storage["audio"]["format"], album_dir, cookies_file)
                        fpath = find_file_by_id(album_dir, yt_id)
                    if fpath:
                        files.append(fpath)
                create_m3u_playlist(p["playlists"], playlist_name, files)
                print(f"Playlist .m3u creada en: {os.path.join(p['playlists'], playlist_name)}.m3u\n")
            print("Descarga de álbumes finalizada.\n")
            continue
        elif opcion != "1":
            print("Opción no válida. Intenta de nuevo.\n")
            continue
        # Modo manual (igual que antes)
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
                    download(f"https://www.youtube.com/watch?v={yt_id}", False, key == "audio", p["format"], p["media"], cookies_file)
                    fpath = find_file_by_id(p["media"], yt_id)
                if fpath:
                    files.append(fpath)
            create_m3u_playlist(p["playlists"], playlist_name, files)
            print(f"Playlist .m3u creada en: {os.path.join(p['playlists'], playlist_name)}.m3u\n")
        # Variables para la lógica de playlist individual
        crear_playlist_individual = False
        playlist_name_individual = None
        canciones_files = []
        # Si hay más de un link individual, pregunta si se quiere crear una playlist
        if len(canciones) > 1:
            resp = input("¿Quieres crear una playlist con estos archivos individuales? (s/n): ").strip().lower()
            if resp == "s":
                # Solicita el nombre de la playlist hasta que sea válido (no vacío)
                while True:
                    playlist_name_individual = input("Nombre para la playlist: ").strip()
                    if playlist_name_individual:
                        break
                    print("Por favor ingresa un nombre válido para la playlist.")
                crear_playlist_individual = True
        # Descarga los archivos individuales y guarda sus rutas para la playlist si corresponde
        for link in canciones:
            print(f"Procesando: {link}")
            with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(link, download=False)
                yt_id = info['id']
            fpath = find_file_by_id(p["media"], yt_id)
            if not fpath:
                download(link, False, key == "audio", p["format"], p["media"], cookies_file)
                fpath = find_file_by_id(p["media"], yt_id)
            if fpath:
                canciones_files.append(fpath)
        if canciones:
            print("Descarga finalizada para canciones/videos sueltos.\n")
            # Si el usuario eligió crear la playlist, se genera el archivo .m3u
            if crear_playlist_individual and playlist_name_individual:
                create_m3u_playlist(p["playlists"], playlist_name_individual, canciones_files)
                print(f"Playlist .m3u creada en: {os.path.join(p['playlists'], playlist_name_individual)}.m3u\n")

if __name__ == "__main__":
    main()