#!/bin/bash
# Deploy Turbo Translate backend services to black-panther
#
# Usage: ./scripts/deploy-backend.sh
#
# Prerequisites:
# - VPN connection to black-panther network
# - SSH access to black-panther

set -e

SERVER="192.168.1.89"
USER="benw"
REMOTE_DIR="turbo-translate-backend"

echo "=== Turbo Translate Backend Deployment ==="
echo ""

# Check VPN connection
echo "Checking connection to black-panther..."
if ! ping -c 1 -W 2 $SERVER > /dev/null 2>&1; then
    echo "ERROR: Cannot reach $SERVER"
    echo "Please ensure VPN is connected"
    exit 1
fi
echo "✓ Connection OK"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Copy docker files
echo ""
echo "Copying Docker files to black-panther..."
ssh $USER@$SERVER "mkdir -p ~/$REMOTE_DIR"
scp -r "$PROJECT_DIR/docker/"* $USER@$SERVER:~/$REMOTE_DIR/
echo "✓ Files copied"

# Check if .env exists
echo ""
echo "Checking configuration..."
if ! ssh $USER@$SERVER "test -f ~/$REMOTE_DIR/.env"; then
    echo "Creating .env from template..."
    ssh $USER@$SERVER "cp ~/$REMOTE_DIR/.env.example ~/$REMOTE_DIR/.env"
    echo ""
    echo "IMPORTANT: You need to add your HuggingFace token to .env"
    echo "Run: ssh $USER@$SERVER 'nano ~/$REMOTE_DIR/.env'"
    echo ""
    echo "Then accept the pyannote model licenses at:"
    echo "  - https://huggingface.co/pyannote/speaker-diarization-3.1"
    echo "  - https://huggingface.co/pyannote/segmentation-3.0"
fi

# Start services
echo ""
echo "Starting Docker services..."
ssh $USER@$SERVER "cd ~/$REMOTE_DIR && docker compose pull && docker compose up -d --build"

# Wait for services
echo ""
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

check_service() {
    local name=$1
    local port=$2
    local endpoint=$3

    if curl -s -f "http://$SERVER:$port$endpoint" > /dev/null 2>&1; then
        echo "✓ $name is healthy"
        return 0
    else
        echo "✗ $name is not responding (port $port)"
        return 1
    fi
}

check_service "Whisper" 8000 "/health"
check_service "Diarization" 8001 "/health"
check_service "Translation" 8002 "/languages"
check_service "TTS" 8003 "/health"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Backend services are running on $SERVER"
echo "You can now start the client with: turbo-translate"
