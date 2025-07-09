"""
NetFlux5G Compatibility Patches
This module provides compatibility patches for missing functions and modules
"""

def fmtBps(bps):
    """
    Format bandwidth in bits per second.
    Compatibility function for missing mininet.util.fmtBps
    """
    if bps is None:
        return "None"
    
    if bps < 1e3:
        return f"{bps:.2f} bps"
    elif bps < 1e6:
        return f"{bps/1e3:.2f} Kbps"
    elif bps < 1e9:
        return f"{bps/1e6:.2f} Mbps"
    elif bps < 1e12:
        return f"{bps/1e9:.2f} Gbps"
    else:
        return f"{bps/1e12:.2f} Tbps"

def patch_mininet_util():
    """Patch missing fmtBps function in mininet.util"""
    try:
        import mininet.util
        if not hasattr(mininet.util, 'fmtBps'):
            mininet.util.fmtBps = fmtBps
            print("✓ Patched mininet.util.fmtBps")
        return True
    except ImportError:
        print("⚠ mininet.util not available")
        return False

def patch_containernet():
    """Check and provide fallback for containernet"""
    try:
        import containernet
        print("✓ Containernet available")
        return True
    except ImportError:
        print("⚠ Containernet not available - will use Docker fallback")
        return False

def apply_all_patches():
    """Apply all compatibility patches"""
    print("🔧 Applying NetFlux5G compatibility patches...")
    
    mininet_patched = patch_mininet_util()
    containernet_available = patch_containernet()
    
    return {
        'mininet_patched': mininet_patched,
        'containernet_available': containernet_available
    }

# Auto-apply patches when imported
if __name__ != "__main__":
    apply_all_patches()
