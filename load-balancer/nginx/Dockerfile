# Nginx Load Balancer Docker Image
FROM nginx:1.25-alpine

# Install additional tools
RUN apk add --no-cache \
    curl \
    openssl \
    apache2-utils

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY ssl/ /etc/ssl/
COPY scripts/ /usr/local/bin/

# Create cache directory
RUN mkdir -p /var/cache/nginx/visey && \
    chown -R nginx:nginx /var/cache/nginx

# Create htpasswd file for admin endpoints
RUN htpasswd -cb /etc/nginx/.htpasswd admin changeme123

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/nginx_health || exit 1

# Expose ports
EXPOSE 80 443 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]