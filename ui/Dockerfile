# BLACK BOX UI - Chromium Kiosk Mode
# Senior-friendly web interface

FROM debian:bullseye-slim

LABEL maintainer="BLACK BOX Project"
LABEL description="Chromium kiosk UI for BLACK BOX assistant"

# Install Chromium and dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xorg \
    openbox \
    python3 \
    python3-pip \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for simple web server
RUN pip3 install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0

# Create application directory
WORKDIR /app

# Copy UI files
COPY index.html .
COPY styles.css .
COPY app.js .
COPY server.py .

# Expose web server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start script that launches both web server and Chromium
COPY start-ui.sh /start-ui.sh
RUN chmod +x /start-ui.sh

CMD ["/start-ui.sh"]

