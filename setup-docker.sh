#!/usr/bin/env bash
# Setup Docker permissions for current user
# This allows running Docker commands without sudo

echo "Setting up Docker permissions for current user..."
echo ""
echo "This script will add your user ($USER) to the docker group."
echo "You may be asked for your password (sudo)."
echo ""

# Add user to docker group
sudo usermod -aG docker "$USER"

echo "✓ User added to docker group"
echo ""
echo "To activate the new group membership, run one of the following:"
echo ""
echo "Option 1 (Recommended): Log out and log back in"
echo ""
echo "Option 2: Run this command in your current session:"
echo "  newgrp docker"
echo ""
echo "Option 3: Run this command in your current session:"
echo "  exec su -l \$USER"
echo ""
echo "After that, you can run Docker commands without sudo:"
echo "  docker ps"
echo "  ./run-dev.sh"
echo ""
