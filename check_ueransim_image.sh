#!/bin/bash
echo "Testing UERANSIM Docker image availability..."
echo "================================================"

# Check if the custom built image exists
if docker image inspect adaptive/ueransim:latest &>/dev/null; then
    echo "✅ adaptive/ueransim:latest is available"
    docker images | grep adaptive/ueransim
else
    echo "❌ adaptive/ueransim:latest is NOT available"
    echo "Please build it with: docker build -t adaptive/ueransim:latest ."
fi

echo ""
echo "Available UERANSIM-related images:"
docker images | grep -i ueransim || echo "No UERANSIM images found"

echo ""
echo "NetFlux5G export script will now use adaptive/ueransim:latest as primary image"
