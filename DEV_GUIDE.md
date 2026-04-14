# Development Environment Setup

## Quick Start

### Option 1: Shell Script (Automatically handles everything)
```bash
chmod +x run-dev.sh
./run-dev.sh
```

### Option 2: Makefile (Recommended - More control & standard)
```bash
make -f Makefile.dev dev
```

---

## What's Improved

### Shell Script (`run-dev.sh`) - Fixed Issues

✅ **Port Fix**: Backend now runs on port `8000` (was hardcoded to 3000)  
✅ **MongoDB Check**: Automatically checks if MongoDB is running  
✅ **MongoDB Auto-Start**: Starts MongoDB via Docker if not running  
✅ **Backend Health Check**: Waits for backend to be ready before starting frontend  
✅ **Dependency Installation**: Runs in parallel instead of sequentially  
✅ **Better Error Handling**: Graceful failure messages  
✅ **Colored Output**: Easy-to-read logs with timestamps  
✅ **Service Status**: Shows all running services and their URLs  

### Makefile (`Makefile.dev`) - Better than Shell Script

A Makefile is **superior** to shell scripts for development because:

**Advantages:**
- ✅ **Standard Convention**: All developers know `make` commands
- ✅ **Easy Task Management**: Separate targets for different purposes
- ✅ **Parallel Execution**: Better handling of concurrent tasks
- ✅ **Easier Maintenance**: Cleaner syntax, less verbose
- ✅ **Cross-Platform**: Works on Linux, macOS, Windows (with make installed)
- ✅ **IDE Integration**: Built-in support in most editors/IDEs
- ✅ **Help Documentation**: Built-in `make help` command
- ✅ **Selective Startup**: Start only the services you need

---

## Available Commands

### Using Makefile (Recommended)

```bash
# Display all available commands
make -f Makefile.dev help

# Start everything (MongoDB + Backend + Frontend)
make -f Makefile.dev dev

# Install dependencies only
make -f Makefile.dev install

# Start individual services
make -f Makefile.dev backend       # Backend only
make -f Makefile.dev frontend      # Frontend only
make -f Makefile.dev mongo         # MongoDB only

# Stop all services
make -f Makefile.dev stop

# Clean build artifacts and node_modules
make -f Makefile.dev clean
```

### Using Shell Script

```bash
./run-dev.sh
```

---

## Service URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **MongoDB**: mongodb://localhost:27017/cicd_app

---

## What Happens During `make dev`

1. Installs dependencies (Backend & Frontend in parallel)
2. Checks if MongoDB is running
3. If MongoDB not running, starts it via Docker
4. Starts Backend on port 8000
5. Waits for Backend to be ready
6. Starts Frontend on port 5173
7. Shows status dashboard with all service URLs

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill the process using port 8000
kill -9 <PID>
```

### MongoDB connection error
```bash
# Ensure MongoDB is running
docker compose up mongo -d

# Or start manually via make
make -f Makefile.dev mongo
```

### Frontend won't connect to Backend
```bash
# Verify backend is running on port 8000
curl http://localhost:8000/

# Check vite.config.js proxy configuration
```

---

## Preference: Use Makefile

I recommend using **`Makefile.dev`** instead of the shell script because:

1. **Standard**: Unix/Linux convention
2. **Flexible**: Start services individually or together
3. **Cleaner**: Better for complex workflows
4. **Maintainable**: Less code duplication
5. **Professional**: Industry standard for development

**Simple alias for convenience** (add to ~/.bashrc or ~/.zshrc):
```bash
alias dev="make -f Makefile.dev dev"
alias dev-help="make -f Makefile.dev help"
```

Then just run: `dev`
