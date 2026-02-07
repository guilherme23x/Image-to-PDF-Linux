#!/bin/bash

# Definições de variáveis
APP_NAME="image-merger"
VERSION="1.0.0"
BUILD_DIR="image_merger_dist"
PKG_DIR="${APP_NAME}_${VERSION}"

# 1. Compilação com PyInstaller
echo "Iniciando compilação com PyInstaller..."
pyinstaller --noconsole --onefile --add-data "image.png:." image_merger.py

# 2. Criação da estrutura de diretórios Debian
echo "Criando estrutura do pacote..."
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons"

# 3. Movendo arquivos
cp "dist/image_merger" "$PKG_DIR/usr/bin/"
cp "image.png" "$PKG_DIR/usr/share/icons/image-merger.png"

# 4. Criando arquivo DEBIAN/control
cat <<EOF > "$PKG_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Usuario <contato@email.com>
Description: Interface Dash para junção e conversão de imagens.
EOF

# 5. Criando o atalho .desktop
cat <<EOF > "$PKG_DIR/usr/share/applications/image-merger.desktop"
[Desktop Entry]
Name=Image Merger Dash
Exec=/usr/bin/image_merger
Icon=/usr/share/icons/image-merger.png
Type=Application
Categories=Graphics;
Terminal=false
EOF

# 6. Construindo o pacote .deb
echo "Gerando arquivo .deb..."
dpkg-deb --build "$PKG_DIR"

echo "Processo concluído: ${PKG_DIR}.deb gerado."
