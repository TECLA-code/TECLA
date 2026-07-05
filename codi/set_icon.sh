#!/bin/bash
# Script per assignar la icona personalitzada al fitxer EXECUTAR_TECLA.command

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_PATH="$SCRIPT_DIR/AppIcon.png"
TARGET_FILE="$SCRIPT_DIR/EXECUTAR_TECLA.command"

if [ ! -f "$ICON_PATH" ]; then
    echo "Error: No s'ha trobat AppIcon.png"
    exit 1
fi

if [ ! -f "$TARGET_FILE" ]; then
    echo "Error: No s'ha trobat EXECUTAR_TECLA.command"
    exit 1
fi

# Convertir PNG a icns temporalment
TEMP_ICONSET="$SCRIPT_DIR/temp.iconset"
TEMP_ICNS="$SCRIPT_DIR/temp.icns"

mkdir -p "$TEMP_ICONSET"

# Crear diferents mides per l'iconset
sips -z 16 16     "$ICON_PATH" --out "$TEMP_ICONSET/icon_16x16.png" > /dev/null 2>&1
sips -z 32 32     "$ICON_PATH" --out "$TEMP_ICONSET/icon_16x16@2x.png" > /dev/null 2>&1
sips -z 32 32     "$ICON_PATH" --out "$TEMP_ICONSET/icon_32x32.png" > /dev/null 2>&1
sips -z 64 64     "$ICON_PATH" --out "$TEMP_ICONSET/icon_32x32@2x.png" > /dev/null 2>&1
sips -z 128 128   "$ICON_PATH" --out "$TEMP_ICONSET/icon_128x128.png" > /dev/null 2>&1
sips -z 256 256   "$ICON_PATH" --out "$TEMP_ICONSET/icon_128x128@2x.png" > /dev/null 2>&1
sips -z 256 256   "$ICON_PATH" --out "$TEMP_ICONSET/icon_256x256.png" > /dev/null 2>&1
sips -z 512 512   "$ICON_PATH" --out "$TEMP_ICONSET/icon_256x256@2x.png" > /dev/null 2>&1
sips -z 512 512   "$ICON_PATH" --out "$TEMP_ICONSET/icon_512x512.png" > /dev/null 2>&1
sips -z 1024 1024 "$ICON_PATH" --out "$TEMP_ICONSET/icon_512x512@2x.png" > /dev/null 2>&1

# Crear icns
iconutil -c icns "$TEMP_ICONSET" -o "$TEMP_ICNS" > /dev/null 2>&1

if [ -f "$TEMP_ICNS" ]; then
    # Assignar la icona al fitxer .command amb AppleScript
    osascript <<EOF
use framework "Foundation"
use framework "AppKit"

set sourcePath to POSIX file "$TEMP_ICNS"
set targetPath to POSIX file "$TARGET_FILE"

set imageData to (current application's NSImage's alloc()'s initWithContentsOfFile:"$TEMP_ICNS")
(current application's NSWorkspace's sharedWorkspace()'s setIcon:imageData forFile:"$TARGET_FILE" options:0)
EOF
    
    if [ $? -eq 0 ]; then
        echo "✓ Icona assignada correctament a EXECUTAR_TECLA.command"
    else
        echo "Error: No s'ha pogut assignar la icona"
        rm -rf "$TEMP_ICONSET" "$TEMP_ICNS"
        exit 1
    fi
else
    echo "Error: No s'ha pogut crear l'arxiu .icns"
    rm -rf "$TEMP_ICONSET"
    exit 1
fi

# Netejar fitxers temporals
rm -rf "$TEMP_ICONSET" "$TEMP_ICNS"

echo "✓ Procés completat"
