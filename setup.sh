#!/bin/bash

set -e  # Encerra se qualquer comando falhar

APP_NAME="DockerMonitor"
APP_DEST="/opt/$APP_NAME"
DESKTOP_FILE="monitor-docker.desktop"
DESKTOP_DEST="$HOME/.local/share/applications/$DESKTOP_FILE"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/$DESKTOP_FILE"
FOLDER_LOG_CONFIG="$HOME/docker_monitor"
VENV_DIR=".venv-build"

# Função para instalar o sistema
instalar_sistema() {
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

  echo "8. Verificando autostart..."
  mkdir -p "$AUTOSTART_DIR"
  if [ ! -f "$AUTOSTART_FILE" ]; then
      cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Monitor Docker
Comment=Aplicação responsável por gerenciar imagens e containers Docker
Exec=$BIN_DEST monitoramento
Icon=$APP_DEST/assets/app-icon.png
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Categories=Utility;System;
EOF

      chmod +x "$AUTOSTART_FILE"
  else
      echo "Autostart já existe. Pulando passo 10."
  fi

  echo "9. Limpando ambiente virtual de build..."
  deactivate
  rm -rf "$VENV_DIR"

  echo "10. Removendo a pasta build..."
  sudo rm -rf "build"
  echo "pasta build removida."

  echo "✔️ Instalação concluída com sucesso!"
}

# Função para remover o sistema
remover_sistema() {
    echo "Removendo sistema..."

    sudo rm -rf "$APP_DEST"
    sudo rm -rf "$FOLDER_LOG_CONFIG"
    rm -f "$DESKTOP_DEST"
    rm -f "$AUTOSTART_FILE"

    echo "Sistema removido com sucesso!"
}

# Menu de escolha
echo "Deseja instalar ou remover o sistema?"
select opcao in "Instalar" "Remover" "Cancelar"; do
    case $opcao in
        "Instalar")
            instalar_sistema
            break
            ;;
        "Remover")
            remover_sistema
            break
            ;;
        "Cancelar")
            echo "Operação cancelada."
            break
            ;;
        *)
            echo "Opção inválida. Escolha 1, 2 ou 3."
            ;;
    esac
done