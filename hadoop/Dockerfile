FROM debian:bookworm-slim

ARG HADOOP_VERSION=3.3.6
ENV DEBIAN_FRONTEND=noninteractive

# Java (OpenJDK), Python 3, SSH y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless python3 \
        openssh-server openssh-client \
        curl ca-certificates procps tar gzip \
    && rm -rf /var/lib/apt/lists/*

# Enlace estable a JAVA_HOME (independiente de amd64/arm64)
RUN ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" /opt/java

ENV JAVA_HOME=/opt/java \
    HADOOP_HOME=/opt/hadoop
ENV PATH=$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH
# Hadoop sobre Java 17: abrir módulos que usa por reflexión
ENV HADOOP_OPTS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED"

# Hadoop en modo standalone (sin configuración extra: usa FS local)
RUN curl -fsSL "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" \
      | tar -xz -C /opt \
    && ln -s /opt/hadoop-${HADOOP_VERSION} /opt/hadoop \
    && echo "export JAVA_HOME=${JAVA_HOME}" >> /opt/hadoop/etc/hadoop/hadoop-env.sh \
    && printf 'export JAVA_HOME=%s\nexport HADOOP_HOME=%s\nexport PATH=$PATH:%s/bin\n' \
         "$JAVA_HOME" "$HADOOP_HOME" "$HADOOP_HOME" > /etc/profile.d/hadoop.sh \
    && ln -s /opt/hadoop/bin/hadoop /usr/local/bin/hadoop

# Usuario sin contraseña: '*' deshabilita password pero permite login por llave
RUN useradd -m -u 1000 -s /bin/bash hadoop && usermod -p '*' hadoop \
    && mkdir -p /data/input /data/output /run/sshd \
    && chown -R hadoop:hadoop /data/output /opt/hadoop-${HADOOP_VERSION}

# sshd: solo llaves, sin root
RUN printf 'PasswordAuthentication no\nPermitRootLogin no\nPubkeyAuthentication yes\n' >> /etc/ssh/sshd_config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
