FROM alpine:latest

# Install SSH client
RUN apk add --no-cache openssh-client

# Create directory for SSH keys
RUN mkdir -p /root/.ssh

# Copy SSH config and key
COPY ssh_config /root/.ssh/config
COPY id_ed25519 /root/.ssh/id_ed25519

# Set correct permissions
RUN chmod 600 /root/.ssh/id_ed25519
RUN chmod 644 /root/.ssh/config

# Create tunnel script with proper SSH options
RUN echo '#!/bin/sh' > /tunnel.sh && \
    echo 'echo "Starting SSH tunnel..."' >> /tunnel.sh && \
    echo 'while true; do' >> /tunnel.sh && \
    echo '    ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -N -L 0.0.0.0:19092:localhost:9090 -p 47295 root@213.173.105.12' >> /tunnel.sh && \
    echo '    echo "SSH tunnel disconnected, retrying in 5 seconds..."' >> /tunnel.sh && \
    echo '    sleep 5' >> /tunnel.sh && \
    echo 'done' >> /tunnel.sh

RUN chmod +x /tunnel.sh

CMD ["/tunnel.sh"]
