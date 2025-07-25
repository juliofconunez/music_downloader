#!/data/data/com.termux/files/usr/bin/bash
# Script para instalar/actualizar el comando ejecutable de music_downloader en Termux

# Ruta al script fuente
SCRIPT_SRC="$(pwd)/md.py"
# Nombre del comando que quieres usar
CMD_NAME="md"
# Ruta destino en binarios de Termux
BIN_DIR="$PREFIX/bin"
BIN_PATH="$BIN_DIR/$CMD_NAME"



# Instalar dependencias necesarias
echo "Instalando dependencias necesarias..."
pkg install -y python ffmpeg
pip3 install --upgrade yt-dlp ffmpeg-python

# Copia el script y da permisos de ejecución
cp "$SCRIPT_SRC" "$BIN_PATH"
chmod +x "$BIN_PATH"

echo "Comando '$CMD_NAME' actualizado. Puedes ejecutarlo desde cualquier lugar con: $CMD_NAME"
