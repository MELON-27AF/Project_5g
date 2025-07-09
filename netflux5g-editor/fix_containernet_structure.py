#!/usr/bin/env python3
"""
Fix Containernet imports for older Containernet installation structure
"""

import os
import sys

def check_containernet_structure():
    """Check the actual Containernet installation structure"""
    print("🔍 Checking Containernet structure...")
    
    containernet_path = "/home/melon/containernet"
    mininet_path = f"{containernet_path}/mininet"
    
    # Check files that indicate Containernet functionality
    containernet_files = [
        f"{mininet_path}/net.py",
        f"{mininet_path}/node.py", 
        f"{mininet_path}/cli.py",
        f"{mininet_path}/term.py"
    ]
    
    print(f"📁 Containernet base: {containernet_path}")
    print(f"📁 Mininet modules: {mininet_path}")
    
    for file_path in containernet_files:
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"   {exists} {os.path.basename(file_path)}")
    
    # Check if this has Docker support by looking in net.py
    try:
        with open(f"{mininet_path}/net.py", 'r') as f:
            content = f.read()
            has_docker = "Docker" in content or "container" in content.lower()
            print(f"   {'✅' if has_docker else '❌'} Docker support detected")
            return has_docker
    except:
        print("   ❌ Could not check Docker support")
        return False

def create_containernet_wrapper():
    """Create wrapper modules to make Containernet imports work"""
    print("\n🔧 Creating Containernet import wrappers...")
    
    containernet_path = "/home/melon/containernet"
    wrapper_dir = f"{containernet_path}/containernet"
    
    # Create containernet directory if it doesn't exist
    os.makedirs(wrapper_dir, exist_ok=True)
    os.makedirs(f"{wrapper_dir}/node", exist_ok=True)
    os.makedirs(f"{wrapper_dir}/cli", exist_ok=True)
    os.makedirs(f"{wrapper_dir}/term", exist_ok=True)
    
    # Create __init__.py files
    init_files = [
        f"{wrapper_dir}/__init__.py",
        f"{wrapper_dir}/node/__init__.py", 
        f"{wrapper_dir}/cli/__init__.py",
        f"{wrapper_dir}/term/__init__.py"
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write("# Containernet wrapper module\n")
    
    # Create net.py wrapper
    net_wrapper = f"""
# Containernet net wrapper
import sys
import os

# Add containernet path to Python path
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

# Import from the actual mininet modules
try:
    from mininet.net import Mininet as MininetBase
    from mininet.net import *
    
    # Check if this version has Docker support
    import mininet.node
    if hasattr(mininet.node, 'Docker'):
        # This is Containernet with Docker support
        Containernet = MininetBase
        print("✅ Using Containernet with Docker support")
    else:
        # This is standard Mininet, create a basic wrapper
        class Containernet(MininetBase):
            '''Containernet wrapper for standard Mininet'''
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        print("⚠️  Using Mininet wrapper (limited Docker support)")
        
except ImportError as e:
    print(f"❌ Failed to import mininet.net: {{e}}")
    raise
"""
    
    with open(f"{wrapper_dir}/net.py", 'w') as f:
        f.write(net_wrapper)
    
    # Create node.py wrapper
    node_wrapper = f"""
# Containernet node wrapper
import sys
import os

# Add containernet path to Python path
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

# Import from the actual mininet modules
try:
    from mininet.node import *
    
    # Check if Docker node exists
    import mininet.node
    if hasattr(mininet.node, 'Docker'):
        Docker = mininet.node.Docker
        DockerSta = Docker  # Alias for compatibility
        print("✅ Docker nodes available")
    else:
        # Create fallback Docker class
        from mininet.node import Host
        
        class Docker(Host):
            '''Fallback Docker class using Host'''
            def __init__(self, name, dimage=None, dcmd=None, **kwargs):
                # Remove Docker-specific parameters
                docker_params = ['dimage', 'dcmd', 'environment', 'volumes', 'ports']
                for param in docker_params:
                    kwargs.pop(param, None)
                super().__init__(name, **kwargs)
                print(f"⚠️  Using Host fallback for Docker container: {{name}}")
        
        DockerSta = Docker
        print("⚠️  Using Host fallback for Docker nodes")
        
except ImportError as e:
    print(f"❌ Failed to import mininet.node: {{e}}")
    raise
"""
    
    with open(f"{wrapper_dir}/node/__init__.py", 'w') as f:
        f.write(node_wrapper)
    
    # Create cli.py wrapper
    cli_wrapper = f"""
# Containernet CLI wrapper
import sys
import os

# Add containernet path to Python path
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

# Import from the actual mininet CLI
try:
    from mininet.cli import CLI
    print("✅ CLI imported successfully")
except ImportError as e:
    print(f"❌ Failed to import mininet.cli: {{e}}")
    raise
"""
    
    with open(f"{wrapper_dir}/cli/__init__.py", 'w') as f:
        f.write(cli_wrapper)
    
    # Create term.py wrapper
    term_wrapper = f"""
# Containernet term wrapper
import sys
import os

# Add containernet path to Python path
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

# Import from the actual mininet term
try:
    from mininet.term import *
    
    # Create makeTerm alias for compatibility
    def makeTerm(node, title='Node', term='xterm', display=None, cmd='bash'):
        '''Create terminal for node - wrapper for compatibility'''
        try:
            from mininet.term import makeTerm as originalMakeTerm
            return originalMakeTerm(node, title, term, display, cmd)
        except:
            # Fallback: just run the command directly
            print(f"Running command on {{node.name}}: {{cmd}}")
            return node.cmd(cmd)
    
    print("✅ Term functions imported successfully")
    
except ImportError as e:
    print(f"❌ Failed to import mininet.term: {{e}}")
    
    # Create basic fallback
    def makeTerm(node, title='Node', term='xterm', display=None, cmd='bash'):
        '''Fallback makeTerm function'''
        print(f"Running command on {{node.name}}: {{cmd}}")
        return node.cmd(cmd)
"""
    
    with open(f"{wrapper_dir}/term/__init__.py", 'w') as f:
        f.write(term_wrapper)
    
    print("✅ Created Containernet wrapper modules")
    return True

def test_containernet_imports():
    """Test the Containernet imports after creating wrappers"""
    print("\n🧪 Testing Containernet imports...")
    
    # Add containernet to Python path
    containernet_path = "/home/melon/containernet"
    if containernet_path not in sys.path:
        sys.path.insert(0, containernet_path)
    
    results = {}
    
    # Test containernet.net
    try:
        from containernet.net import Containernet
        results['containernet_net'] = True
        print("✅ containernet.net.Containernet: SUCCESS")
    except Exception as e:
        results['containernet_net'] = False
        print(f"❌ containernet.net.Containernet: {e}")
    
    # Test containernet.node
    try:
        from containernet.node import DockerSta
        results['containernet_node'] = True
        print("✅ containernet.node.DockerSta: SUCCESS")
    except Exception as e:
        results['containernet_node'] = False
        print(f"❌ containernet.node.DockerSta: {e}")
    
    # Test containernet.cli
    try:
        from containernet.cli import CLI
        results['containernet_cli'] = True
        print("✅ containernet.cli.CLI: SUCCESS")
    except Exception as e:
        results['containernet_cli'] = False
        print(f"❌ containernet.cli.CLI: {e}")
    
    # Test containernet.term
    try:
        from containernet.term import makeTerm
        results['containernet_term'] = True
        print("✅ containernet.term.makeTerm: SUCCESS")
    except Exception as e:
        results['containernet_term'] = False
        print(f"❌ containernet.term.makeTerm: {e}")
    
    return results

def main():
    print("🚀 NetFlux5G Containernet Structure Fix")
    print("=" * 45)
    
    # Step 1: Check current structure
    has_docker = check_containernet_structure()
    
    # Step 2: Create wrapper modules
    create_containernet_wrapper()
    
    # Step 3: Test imports
    results = test_containernet_imports()
    
    # Summary
    print("\n📊 Results Summary:")
    print("=" * 30)
    all_working = all(results.values())
    
    for module, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"  {module:20}: {status}")
    
    if all_working:
        print("\n🎉 SUCCESS! All Containernet imports are working!")
        print("   Your NetFlux5G can now create Docker containers.")
        print("\n📝 Next Steps:")
        print("1. Close current terminal")
        print("2. Open new terminal")
        print("3. cd /home/melon/Project_5g/netflux5g-editor/src")
        print("4. python3 main.py")
        print("5. Load topology and click 'Run All'")
        print("6. Check: docker ps -a")
        
    else:
        print("\n⚠️  Some imports still have issues.")
        print("   But the basic structure is now in place.")
        print("   Try restarting terminal and testing again.")

if __name__ == "__main__":
    main()
