# HAProxy Load Balancer Docker Image
FROM haproxy:2.8-alpine

# Install additional tools
RUN apk add --no-cache \
    curl \
    openssl \
    socat

# Copy configuration
COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
COPY ssl/ /etc/ssl/certs/
COPY errors/ /etc/haproxy/errors/

# Create runtime directory
RUN mkdir -p /var/run/haproxy && \
    chown -R haproxy:haproxy /var/run/haproxy

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8405/health || exit 1

# Expose ports
EXPOSE 80 443 8404 8405

# Start HAProxy
CMD ["haproxy", "-f", "/usr/local/etc/haproxy/haproxy.cfg"]