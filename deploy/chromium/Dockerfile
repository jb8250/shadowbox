FROM debian:bullseye-slim

# Install required dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    x11-utils \
    xvfb \
    libnss3 \
    libatk1.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libxcb-xinerama0 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create directory for Chromium
RUN mkdir -p /opt/chromium

# Copy the .dmg file (this is a placeholder - actual extraction would be needed)
COPY ungoogled-chromium_55.0.2883.95-1_macos.dmg /opt/chromium/

# Install VNC server
RUN apt-get update && apt-get install -y \
    tiger-vnc-viewer \
    && rm -rf /var/lib/apt/lists/*

# Set up VNC
RUN mkdir -p /root/.vnc && echo "password" | vncpasswd -f > /root/.vnc/passwd && chmod 600 /root/.vnc/passwd

# Expose VNC port
EXPOSE 5901

# Start Xvfb and VNC server
CMD ["/bin/bash", "-c", "Xvfb :1 -screen 0 1280x800x24 & vncserver :1 -geometry 1280x800 -depth 24 -localhost no -rfbport 5901 && echo \"VNC server started on :1\" && tail -f /dev/null"]