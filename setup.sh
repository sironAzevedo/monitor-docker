#!/bin/bash

set -e  # Encerra se qualquer comando falhar

APP_NAME="DockerMonitor"
APP_DEST="/opt/$APP_NAME"
DESKTOP_FILE="monitor-docker.desktop"
DESKTOP_DEST="$HOME/.local/share/applications/$DESKTOP_FILE"
VENV_DIR=".venv-build"

echo "1. Criando ambiente virtual Python isolado em '$VENV_DIR'..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "2. Instalando dependências para build..."
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || echo "Aviso: requirements.txt não encontrado."

echo "3. Executando setup.py para build..."
python setup.py build

echo "4. Removendo instalação anterior em $APP_DEST (se existir)..."
if [ -d "$APP_DEST" ]; then
    sudo rm -rf "$APP_DEST"
    echo "Versão anterior removida."
fi

echo "5. Movendo binário gerado para $APP_DEST..."
# Caminho do binário gerado
BIN_SOURCE="build/$APP_NAME"
BIN_DEST="$APP_DEST/$APP_NAME"

# Move binário novo
sudo mv "$BIN_SOURCE" "$APP_DEST"

echo "6. Dando permissão de execução ao app..."
sudo chmod +x "$BIN_DEST"

echo "7. Instalando atalho na interface gráfica (se necessário)..."
if [ ! -f "$DESKTOP_DEST" ]; then
    cat > "$DESKTOP_DEST" <<EOF
[Desktop Entry]
Version=1.0
Name=Monitor Docker
Comment=Aplicação responsável por gerenciar imagens e containers Docker
Exec=$BIN_DEST
Icon=$APP_DEST/assets/app-icon.png
Terminal=false
Type=Application
Categories=Utility;System;
EOF

    chmod +x "$DESKTOP_DEST"

    echo "Atalho criado em $DESKTOP_DEST"
    update-desktop-database ~/.local/share/applications || true
else
    echo "Atalho já existe. Pulando passo 4."
fi

echo "8. Limpando ambiente virtual de build..."
deactivate
rm -rf "$VENV_DIR"

echo "9. Removendo a pasta build..."
sudo rm -rf "build"
echo "pasta build removida."

echo "✔️ Instalação concluída com sucesso!"
