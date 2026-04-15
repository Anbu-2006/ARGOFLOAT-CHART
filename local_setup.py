"""
FloatChart - Local Setup Script
One-click setup for running FloatChart locally.

Usage:
    python local_setup.py           # Full setup + launch menu
    python local_setup.py --quick   # Skip to app launch
"""

import os
import sys
import subprocess
import shutil
import webbrowser
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🌊  FloatChart - Local Setup                                ║
║       Ocean Intelligence Platform                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}""")

def print_step(step, total, message):
    print(f"\n{Colors.BLUE}[{step}/{total}]{Colors.END} {Colors.BOLD}{message}{Colors.END}")

def print_success(message):
    print(f"  {Colors.GREEN}✓{Colors.END} {message}")

def print_warning(message):
    print(f"  {Colors.WARNING}⚠{Colors.END} {message}")

def print_error(message):
    print(f"  {Colors.FAIL}✗{Colors.END} {message}")

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error(f"Python 3.9+ required. You have {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_pip():
    """Check if pip is available."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print_success("pip is available")
        return True
    except:
        print_error("pip not found")
        return False

def create_env_file(project_root):
    """
    Setup .env file for local development.
    Uses DuckDB by default (zero-config) with NVIDIA NIM for AI.
    """
    root_env = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if root_env.exists():
        print_success("Root .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, root_env)
        print_success("Created .env from .env.example")
    else:
        env_content = """# FloatChart Configuration
# Database: DuckDB (zero-config, runs locally)
DATABASE_URL=duckdb:///prototype.duckdb

# AI Provider: NVIDIA NIM
# Get your free API key at: https://build.nvidia.com
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxx
NVIDIA_MODEL=meta/llama-3.3-70b-instruct
"""
        root_env.write_text(env_content)
        print_success("Created .env file")
    
    print_warning("Please edit .env with your NVIDIA API key (get one at https://build.nvidia.com)")
    return True

def install_dependencies(project_root):
    """Install Python dependencies from requirements.txt."""
    req_file = project_root / "requirements.txt"
    
    if not req_file.exists():
        print_error("requirements.txt not found")
        return False
    
    print("  Installing dependencies (this may take a minute)...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Dependencies installed successfully")
            return True
        else:
            print_error(f"Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def verify_installation():
    """Verify key packages are installed."""
    packages = ['flask', 'sqlalchemy', 'pandas', 'langchain_core', 'langchain_openai']
    missing = []
    
    for pkg in packages:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print_warning(f"Some packages may need manual install: {', '.join(missing)}")
        print(f"  Run: {Colors.CYAN}pip install -r requirements.txt{Colors.END}")
        return False
    
    print_success("All key packages verified")
    return True

def check_env_configured(project_root):
    """Check if .env has real credentials (not placeholders)."""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        return False
    
    content = env_file.read_text()
    
    # Check for placeholder values
    if "your_password" in content:
        return False
    if "nvapi-xxxxxxxxxxxxxxxxxxxxxxxx" in content:
        return False
    if "your_nvidia_api_key_here" in content:
        return False
    
    return "DATABASE_URL=" in content and len(content) > 50

def check_prototype_db(project_root):
    """Check if prototype.duckdb exists and has data."""
    db_file = project_root / "prototype.duckdb"
    
    if not db_file.exists():
        print_warning("prototype.duckdb not found — you can generate it with the Data Manager")
        return False
    
    # Quick check: does it have data?
    try:
        import duckdb
        con = duckdb.connect(str(db_file), read_only=True)
        count = con.execute("SELECT COUNT(*) FROM argo_data").fetchone()[0]
        con.close()
        print_success(f"Database ready: {count:,} records in argo_data")
        return True
    except Exception as e:
        print_warning(f"Database exists but check failed: {e}")
        return True  # File exists, might still work

def launch_data_manager(project_root):
    """Launch the Data Manager web app."""
    data_gen_dir = project_root / "DATA_GENERATOR"
    
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║            🚀 Launching Data Manager                          ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
The Data Manager will open in your browser.
Use it to download ARGO oceanographic data.

{Colors.WARNING}Press Ctrl+C to stop the server when done.{Colors.END}
""")
    
    time.sleep(1)
    
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:5001")
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    os.chdir(data_gen_dir)
    subprocess.run([sys.executable, "app.py"])

def launch_chatbot(project_root):
    """Launch the FloatChart Chat App."""
    chatbot_dir = project_root / "ARGO_CHATBOT"
    
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║            🚀 Launching FloatChart Chat                       ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
The Chat App will open in your browser.

{Colors.WARNING}Press Ctrl+C to stop the server when done.{Colors.END}
""")
    
    time.sleep(1)
    
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:5000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    os.chdir(chatbot_dir)
    subprocess.run([sys.executable, "app.py"])

def show_instructions():
    """Show detailed setup instructions."""
    print(f"""
{Colors.BOLD}📝 SETUP INSTRUCTIONS:{Colors.END}

{Colors.CYAN}1. Database (DuckDB — zero config):{Colors.END}
   • DuckDB is included — no installation needed!
   • The prototype database is ready to use out of the box
   • For large datasets, switch to PostgreSQL in .env

{Colors.CYAN}2. Get an NVIDIA API Key:{Colors.END}
   • Go to https://build.nvidia.com
   • Get a key for Llama 3.3 70B Instruct

{Colors.CYAN}3. Configure .env:{Colors.END}
   Edit {Colors.BOLD}.env{Colors.END} in project root:
   
   DATABASE_URL=duckdb:///prototype.duckdb
   NVIDIA_API_KEY=nvapi-...

{Colors.CYAN}4. Download Data (optional):{Colors.END}
   Run: cd DATA_GENERATOR && python app.py
   → Opens wizard at http://localhost:5001

{Colors.CYAN}5. Launch Chat App:{Colors.END}
   Run: cd ARGO_CHATBOT && python app.py
   → Opens chat at http://localhost:5000

""")

def show_quick_launch_menu(project_root):
    """Show menu for quick launch options."""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                    FloatChart Ready! 🎉                       ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
{Colors.BOLD}What would you like to do?{Colors.END}

  {Colors.CYAN}1{Colors.END} - Launch Data Manager (download ARGO data)
  {Colors.CYAN}2{Colors.END} - Launch Chat App (requires data)
  {Colors.CYAN}3{Colors.END} - Show setup instructions
  {Colors.CYAN}q{Colors.END} - Quit

""")
    
    while True:
        choice = input(f"{Colors.BOLD}Enter choice (1/2/3/q): {Colors.END}").strip().lower()
        
        if choice == '1':
            launch_data_manager(project_root)
            break
        elif choice == '2':
            launch_chatbot(project_root)
            break
        elif choice == '3':
            show_instructions()
        elif choice == 'q':
            print("\nGoodbye! 🌊")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or q.")

def main():
    print_banner()
    
    project_root = Path(__file__).parent.absolute()
    
    # Check for --quick flag
    quick_mode = "--quick" in sys.argv
    
    if not quick_mode:
        total_steps = 5
        
        # Step 1: Check Python
        print_step(1, total_steps, "Checking Python version...")
        if not check_python_version():
            sys.exit(1)
        
        # Step 2: Check pip
        print_step(2, total_steps, "Checking pip...")
        if not check_pip():
            sys.exit(1)
        
        # Step 3: Install dependencies
        print_step(3, total_steps, "Installing dependencies...")
        if not install_dependencies(project_root):
            print_warning("Some dependencies may have failed. Try: pip install -r requirements.txt")
        
        # Step 4: Setup environment
        print_step(4, total_steps, "Setting up configuration...")
        create_env_file(project_root)
        
        # Step 5: Verify everything
        print_step(5, total_steps, "Verifying installation...")
        verify_installation()
        check_prototype_db(project_root)
    
    # Check if env is configured
    if check_env_configured(project_root):
        print_success("Configuration detected!")
        show_quick_launch_menu(project_root)
    else:
        print(f"""
{Colors.WARNING}{Colors.BOLD}
⚠️  Configuration Required
{Colors.END}
Please edit {Colors.BOLD}.env{Colors.END} (at project root) with your credentials:

  DATABASE_URL=duckdb:///prototype.duckdb
  NVIDIA_API_KEY=nvapi-...

{Colors.CYAN}Get your NVIDIA API key at:{Colors.END}
  https://build.nvidia.com

After configuring, run this script again or:
  cd DATA_GENERATOR && python app.py  (to download data)
  cd ARGO_CHATBOT && python app.py    (to launch chat)
""")

if __name__ == "__main__":
    main()
