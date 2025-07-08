# NetFlux5G Dependency Issues - Quick Solutions

## The Problem
You encountered these errors when running a Mininet topology:
```
Warning: mininet-wifi import failed: cannot import name 'fmtBps' from 'mininet.util'
ModuleNotFoundError: No module named 'containernet'
```

## Quick Solutions

### 🚀 Option 1: Immediate Fix (Recommended)
Run the quick fix script to patch the issues:
```bash
cd netflux5g-editor/
python3 quick_fix.py
```

### 🐳 Option 2: Docker Solution (Most Reliable)
Use Docker to run topologies without dependency issues:
```bash
cd docker/
docker build -t netflux5g-mininet .
cd ../netflux5g-editor/
./run_topology_docker.sh /path/to/your/topology.py
```

### 📦 Option 3: Full Setup
Install all dependencies properly:
```bash
cd netflux5g-editor/
python3 setup_dependencies.py
```

### 🔧 Option 4: Use Compatibility Runner
Use the enhanced topology runner that handles missing dependencies:
```bash
cd netflux5g-editor/
python3 topology_runner.py /path/to/your/topology.py
```

## What These Solutions Do

1. **Quick Fix**: Patches missing functions and creates compatibility layers
2. **Docker Solution**: Runs topologies in isolated containers with all dependencies
3. **Full Setup**: Installs Mininet-WiFi and Containernet natively
4. **Compatibility Runner**: Intelligent fallback system for different backends

## Files Created

- `setup_dependencies.py` - Full dependency installation script
- `quick_fix.py` - Immediate patches and fixes
- `topology_runner.py` - Enhanced topology runner with fallbacks
- `run_topology_docker.sh` - Docker-based topology runner
- `src/netflux5g_compat.py` - Compatibility patches

## System Requirements

- **Linux** (preferred) or WSL2/Docker on Windows/macOS
- **Python 3.7+**
- **Docker** (for Docker solution)
- **sudo access** (for native installation)

## Troubleshooting

### If Docker build fails:
```bash
# Check Docker installation
docker --version

# Ensure you're in the right directory
cd Project_5g/docker/
ls -la  # Should see Dockerfile
```

### If native installation fails:
```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get install -y git make gcc python3-dev python3-setuptools

# Then try the setup script again
python3 setup_dependencies.py
```

### If imports still fail:
```bash
# Use the compatibility runner
python3 topology_runner.py your_topology.py

# Or check what's available
python3 -c "import sys; print(sys.path)"
```

## Next Steps

1. Try the quick fix first: `python3 quick_fix.py`
2. Test with your topology file
3. If issues persist, use the Docker solution
4. For permanent setup, run the full installation

## Support

If you continue to have issues:
1. Check the generated log files
2. Verify your Python environment
3. Consider using a virtual environment
4. Use the Docker solution as a reliable fallback

The Docker solution should work regardless of your host system configuration.
