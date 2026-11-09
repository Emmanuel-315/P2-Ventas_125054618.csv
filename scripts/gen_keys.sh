#!/bin/bash
# Genera el par de llaves que usa el contenedor api para entrar por SSH a hadoop.
# Sin passphrase y sin contraseñas en ningún Dockerfile. Ejecutar UNA vez en el host.
set -e
mkdir -p ssh_keys
[ -f ssh_keys/api_id_ed25519 ] || ssh-keygen -q -t ed25519 -N "" -f ssh_keys/api_id_ed25519 -C api@datamart
chmod 600 ssh_keys/api_id_ed25519
echo "Llaves listas en ssh_keys/"
