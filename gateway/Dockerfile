# ============================================================
# Nginx Gateway — Dockerfile
# ============================================================
FROM nginx:1.27-alpine

# Security: run as non-root
RUN addgroup -S nginx-app && adduser -S nginx-app -G nginx-app

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom config
COPY nginx.conf /etc/nginx/conf.d/gateway.conf

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl && \
    chown -R nginx-app:nginx-app /etc/nginx/ssl

# Create log directory
RUN mkdir -p /var/log/nginx && \
    chown -R nginx-app:nginx-app /var/log/nginx

# Health check dependency
RUN apk add --no-cache curl

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
