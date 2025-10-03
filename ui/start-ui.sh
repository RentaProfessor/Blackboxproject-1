#!/bin/bash
# BLACK BOX UI - Startup Script
# Launches web server and Chromium in kiosk mode

# Start FastAPI server in background
python3 /app/server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Get display environment
DISPLAY="${DISPLAY:-:0}"

# Start X server if needed
if [ ! -f /tmp/.X11-unix/X0 ]; then
    Xorg ${DISPLAY} &
    sleep 2
fi

# Start window manager
openbox &
sleep 1

# Launch Chromium in kiosk mode
chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --no-first-run \
    --disable-features=TranslateUI \
    --disable-session-crashed-bubble \
    --disable-component-update \
    --check-for-update-interval=31536000 \
    --disable-background-networking \
    --disable-sync \
    --disable-extensions \
    --window-size=1920,1080 \
    --window-position=0,0 \
    --display=${DISPLAY} \
    http://localhost:3000 &

CHROMIUM_PID=$!

# Wait for either process to exit
wait -n $SERVER_PID $CHROMIUM_PID

# Kill both processes
kill $SERVER_PID $CHROMIUM_PID 2>/dev/null

exit 0

