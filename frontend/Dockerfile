# ==============================================================================
# Stage 1: Build React SPA application
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Cache package installation layer
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code
COPY . .

# Optional build-time argument for API endpoint
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

# Build optimized production bundle to /app/dist
RUN npm run build

# ==============================================================================
# Stage 2: Hardened Unprivileged Nginx Alpine Runtime
# Runs as non-root 'nginx' user (UID 101) on port 8080
# ==============================================================================
FROM nginxinc/nginx-unprivileged:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

# Healthcheck validating Nginx responds to requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
