# Run Dev Script - Docker Permission Issue & Fix

## Problem

You're seeing this error:
```
unable to get image 'mongo:7': permission denied while trying to connect to the 
Docker daemon socket at unix:///var/run/docker.sock: connect: permission denied
```

This means Docker requires `sudo` to run. The updated script now handles this automatically!

---

## Solution Options

### Option 1: Run with sudo (Quick Fix - Works Right Now)
```bash
sudo ./run-dev.sh
```

**Pros:** Immediate solution, no setup needed  
**Cons:** Need to enter password, requires sudo every time

---

### Option 2: Add User to Docker Group (Permanent Fix - Recommended)

This allows running Docker without `sudo`.

```bash
# Run the setup script
chmod +x setup-docker.sh
sudo ./setup-docker.sh

# Then activate the new permissions (choose ONE):
# Option A: Log out and log back in
# Option B: Run in current session:
newgrp docker

# Verify it works:
docker ps

# Now you can run without sudo:
./run-dev.sh
```

**Pros:** Permanent solution, no sudo needed, works every time  
**Cons:** One-time setup required

---

## How the Updated Script Handles Docker

The `run-dev.sh` script now automatically:

1. **Checks if Docker needs sudo:**
   - Tries: `docker ps`
   - If it fails, uses: `sudo docker...`

2. **Starts MongoDB with appropriate permissions:**
   - Automatically detects sudo requirement
   - Uses correct command to start MongoDB

3. **Better error messages:**
   - Explains what went wrong
   - Provides solutions

---

## Quick Commands Reference

```bash
# With Docker permissions fixed (recommended):
./run-dev.sh

# With sudo (if you don't want to set up permissions):
sudo ./run-dev.sh

# Using Makefile (also handles Docker):
make -f Makefile.dev dev
# or with sudo:
sudo make -f Makefile.dev dev

# Manual MongoDB startup if needed:
sudo docker compose up mongo -d
```

---

## Test Docker Access

Before running the dev script, test if Docker is accessible:

```bash
# Test without sudo:
docker ps

# If it fails, you need option 2 above or use sudo
```

---

## What to Do Now

**Quickest way to get started:**
```bash
sudo ./run-dev.sh
```

**For permanent setup (so you don't need sudo every time):**
```bash
sudo usermod -aG docker $USER
newgrp docker
./run-dev.sh  # Now works without sudo!
```

---

## Services After Startup

Once running, you'll have:
- 📱 Frontend: http://localhost:5173
- 🔧 Backend: http://localhost:8000
- 🗄️ MongoDB: mongodb://localhost:27017
