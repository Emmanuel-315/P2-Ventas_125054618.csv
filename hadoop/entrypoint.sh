#!/bin/bash
set -e
# Llaves de host del servidor SSH (se generan al arrancar, no van en la imagen)
ssh-keygen -A
SSH_DIR=/home/hadoop/.ssh
mkdir -p "$SSH_DIR"

# Llave propia de hadoop -> permite "ssh localhost" sin contraseña
if [ ! -f "$SSH_DIR/id_ed25519" ]; then
  ssh-keygen -q -t ed25519 -N "" -f "$SSH_DIR/id_ed25519" -C hadoop@hadoop
fi
cat "$SSH_DIR/id_ed25519.pub" > "$SSH_DIR/authorized_keys"
# Llave pública de la api -> permite "ssh hadoop@hadoop" desde el contenedor api
[ -f /keys/api.pub ] && cat /keys/api.pub >> "$SSH_DIR/authorized_keys"

printf 'Host *\n  StrictHostKeyChecking accept-new\n' > "$SSH_DIR/config"
chown -R hadoop:hadoop "$SSH_DIR"
chmod 700 "$SSH_DIR"; chmod 600 "$SSH_DIR/authorized_keys" "$SSH_DIR/config" "$SSH_DIR/id_ed25519"

exec /usr/sbin/sshd -D -e
