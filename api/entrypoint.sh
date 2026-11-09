#!/bin/sh
set -e
# Copia la llave privada montada a ~/.ssh con permisos correctos (ssh es estricto)
if [ -f /keys/id_ed25519 ]; then
  mkdir -p /root/.ssh && chmod 700 /root/.ssh
  cp /keys/id_ed25519 /root/.ssh/id_ed25519 && chmod 600 /root/.ssh/id_ed25519
  printf 'Host hadoop\n  User hadoop\n  StrictHostKeyChecking accept-new\n' > /root/.ssh/config
fi
exec "$@"
