#!/bin/bash

# Configurações
APP_NAME="image-merger-cyan"
VERSION="1.0.0"
PKG_DIR="${APP_NAME}_${VERSION}_amd64"
BINARY_NAME="image_merger"

echo "--- Iniciando processo de empacotamento ---"

# 1. Limpeza de builds anteriores
rm -rf build dist "$PKG_DIR" "${PKG_DIR}.deb"

# 2. Compilação com PyInstaller
# --collect-all PySide6 garante que os plugins de plataforma (xcb) sejam incluídos
echo "Compilando binário com PyInstaller..."
python3 -m PyInstaller --noconsole --onefile \
    --name "$BINARY_NAME" \
    --collect-all PySide6 \
    image_merger.py

if [ ! -f "dist/$BINARY_NAME" ]; then
    echo "Erro: Falha na compilação do binário."
    exit 1
fi

# 3. Criando estrutura Debian
echo "Criando estrutura do diretório .deb..."
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"

# 4. Movendo o binário
cp "dist/$BINARY_NAME" "$PKG_DIR/usr/bin/"

# 5. Criando o arquivo de controle (Dependências críticas incluídas)
# libxcb-cursor0 é vital para Qt6 no Ubuntu/Mint
cat <<EOF > "$PKG_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Usuario <contato@email.com>
Depends: libxcb-cursor0, libxcb-xinerama0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-render-util0, libxcb-shape0, libxkbcommon-x11-0
Description: Interface Cyan Engine para junção e conversão de imagens usando PySide6.
EOF

# 6. Criando o atalho no menu (Desktop Entry)
cat <<EOF > "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Name=Image Merger Cyan
Comment=High-Tech Image Processing
Exec=/usr/bin/$BINARY_NAME
Icon=image-x-generic
Type=Application
Categories=Graphics;
Terminal=false
EOF

# 7. Ajustando permissões
chmod 755 "$PKG_DIR/usr/bin/$BINARY_NAME"
chmod 644 "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"

# 8. Construindo o pacote
echo "Gerando pacote .deb..."
dpkg-deb --build "$PKG_DIR"

echo "--- Concluído: ${PKG_DIR}.deb gerado ---"
