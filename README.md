<div align="center">
  <img src="logo.png" alt="Funky Junction Logo" width="300">
  
  # Funky Junction
  ## Qiskit Metal MCP Server

  A comprehensive Model Context Protocol (MCP) server for quantum circuit design using Qiskit Metal. This server provides tools, resources, and prompts for designing, simulating, and analyzing superconducting quantum circuits.

  *Built by **Team Silicon Architects** at the Stanford MCP x Quantum Science Hackathon 2025*
  
  **Team Members:** Sarah Dweik, Sebastien Boussard, Paul Goldschmidt & Gabriel Dupuis
</div>

## 🚀 Features

### 🔧 **Quantum Circuit Design Tools**
- **Design Management**: Create, configure, and manage quantum circuit designs
- **Component Library**: Add transmon qubits, Josephson junctions, spiral couplers
- **Transmission Lines**: Create coplanar waveguides with meandered routing
- **Export Capabilities**: Export designs to GDS format for fabrication
- **Visualization**: Launch KLayout for professional circuit visualization

### 📚 **Learning Resources**
- **Python Examples**: Access and execute quantum circuit design examples
- **Research Papers**: Extract and analyze text from quantum computing PDFs
- **Documentation**: Comprehensive guides and technical references
- **Interactive Analysis**: Guided prompts for systematic learning

### 🤖 **MCP Integration**
- **Tools**: 14+ specialized tools for quantum circuit operations
- **Resources**: Dynamic access to code examples and research documents
- **Prompts**: Template-driven analysis and execution workflows
- **Real-time**: Live design creation and modification capabilities

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Available Tools](#-available-tools)
- [Resources](#-resources)
- [Prompt Templates](#-prompt-templates)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🛠 Installation

### Prerequisites

- **Python 3.8+**
- **pip** or **conda** package manager
- **Git** for cloning the repository

### Required Dependencies

```bash
# Core MCP and quantum computing libraries
pip install fastmcp
pip install qiskit-metal

# PDF processing (choose one or more)
pip install PyPDF2          # Recommended for most PDFs
pip install pdfplumber       # Better table extraction
pip install PyMuPDF         # High performance alternative

# Optional: Visualization
pip install klayout          # Professional IC layout viewer
# OR download from: https://www.klayout.de/build.html
```

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/PaulGoldschmidt/qsim-mcp.git
   cd qsim-mcp
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Qiskit Metal Installation**
   ```bash
   python -c "import qiskit_metal; print('✓ Qiskit Metal installed successfully')"
   ```

4. **Test the MCP Server**
   ```bash
   cd src/qiskit-metal-mcp
   python quiskit-metal-mcp-server.py
   ```

### Docker Installation (Alternative)

```bash
# Build the container
docker build -t funky-junction .

# Run the server
docker run -p 3000:3000 funky-junction
```

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
cd src/qiskit-metal-mcp
python quiskit-metal-mcp-server.py
```

You should see:
```
🚀 Starting Funky Junction - Qiskit Metal FastMCP Server...
📊 Qiskit Metal Available: True
Server running on port 3000...
```

### 2. Connect MCP Client

Configure your MCP client (Claude Desktop, etc.) to connect to:
```
http://localhost:3000
```

### 3. Basic Circuit Design Workflow

```python
# 1. Create a new design
create_design()

# 2. Set design parameters
set_design_variables(cpw_width='0.5um', cpw_gap='0.3um')

# 3. Add qubits
create_transmons(q1_name='Q1', q2_name='Q2')

# 4. Add coupling element
add_coupler(coupler_name='Coupler1', n_turns=3)

# 5. Connect components
connect_components('Q1_Q2_line', 'Q1', 'a', 'Q2', 'b', '1.5mm')

# 6. Export design
export_design_to_gds('./my_quantum_chip.gds')

# 7. Visualize (if KLayout installed)
visualize_gds_with_klayout('./my_quantum_chip.gds')
```

## 🔧 Available Tools

### **Design Management**
| Tool | Description | Usage |
|------|-------------|-------|
| `create_design()` | Initialize new quantum circuit design | First step in any design |
| `set_design_variables()` | Configure CPW parameters and chip size | Set before adding components |
| `get_design_info()` | View current design components and settings | Debug and verification |
| `clear_design()` | Reset design to start fresh | Clean slate for new design |
| `check_status()` | Server and design health check | Troubleshooting |

### **Component Creation**
| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `create_transmons()` | Add transmon pocket qubits | `pad_width`, `pad_height`, positions |
| `add_coupler()` | Create spiral inductor coupler | `n_turns`, `spacing`, `width` |
| `add_josephson_junction()` | Add Manhattan geometry junction | `width`, `finger_width`, `orientation` |
| `connect_components()` | Route CPW between components | `component1`, `pin1`, `component2`, `pin2`, `length` |

### **Export & Visualization**
| Tool | Description | Output |
|------|-------------|--------|
| `export_design_to_gds()` | Export to GDS fabrication format | `.gds` file for clean room |
| `visualize_gds_with_klayout()` | Open design in KLayout viewer | Professional visualization |

### **Resources & Analysis**
| Tool | Description | Input |
|------|-------------|-------|
| `run_python_example()` | Execute quantum circuit examples | `filename` from resources |
| `extract_pdf_text()` | Extract text from research papers | `filename`, `pages`, `max_chars` |

## 📚 Resources

Access learning materials and examples through MCP resources:

### **Comprehensive Resource Discovery**
- `@resources://list` - All available Python examples and PDFs
- `@examples://list` - Python code examples only  
- `@pdfs://list` - Research papers and documentation only

### **Python Examples**
Current examples in `src/resources/`:
- **demo.py** - Complete 4-qubit demonstration chip
- **chip.py** - Advanced chip design with launchers and test structures
- **munch_qubits.py** - Qubit array patterns
- **simpleChip.py** - Basic chip template

Access with:
- `@examples://demo.py` - View source code
- `run_python_example(filename='demo.py')` - Execute example

### **Research Papers**
Current PDFs in `src/resources/`:
- **Circuit Quantum Electrodynamics** - Foundation theory
- **Coupling Superconducting Qubits Via A Cavity Bus** - Inter-qubit communication
- **Fast Tunable Coupler For Superconducting Qubits** - Dynamic coupling
- **Superconducting Flux Qubit Capacitively Coupled** - Flux qubit design
- **Wafer Scale Uniformity Of Dolan Bridge And Bridgeless** - Fabrication techniques

Access with:
- `@pdfs://CircuitQuantumElectrodynamics.pdf` - Get PDF info
- `extract_pdf_text(filename='CircuitQuantumElectrodynamics.pdf', pages='1-5')` - Extract content

## 🎯 Prompt Templates

### **Example Execution & Analysis**
```
/prompt run_example_prompt filename=demo.py analyze_output=true
```
Generates structured prompt for:
- Executing Python examples
- Analyzing circuit design patterns
- Understanding component usage
- Identifying best practices

### **Research Paper Analysis**
```
/prompt analyze_pdf_prompt filename=CircuitQuantumElectrodynamics.pdf focus_area=couplers max_pages=10
```
Focus areas available:
- `couplers` - Qubit coupling mechanisms
- `qubits` - Qubit design and characterization  
- `circuits` - Overall circuit architecture
- `fabrication` - Manufacturing processes
- `theory` - Theoretical foundations
- `general` - Balanced coverage

## 💡 Usage Examples

### **Example 1: Create a Simple Two-Qubit System**

```python
# Initialize design
create_design()
set_design_variables(
    cpw_width='0.5um',
    cpw_gap='0.3um', 
    chip_size_x='9mm',
    chip_size_y='6.5mm'
)

# Add two qubits
create_transmons(
    q1_name='Q1',
    q2_name='Q2',
    q1_pos_x='-2mm',
    q1_pos_y='0mm',
    q2_pos_x='2mm', 
    q2_pos_y='0mm'
)

# Add coupling element
add_coupler(
    coupler_name='Coupler_Q1_Q2',
    n_turns=4,
    spacing='0.2mm',
    pos_x='0mm',
    pos_y='0mm'
)

# Export and visualize
export_design_to_gds('./two_qubit_system.gds')
visualize_gds_with_klayout('./two_qubit_system.gds')
```

### **Example 2: Analyze Research Papers**

```python
# List available research papers
# Use: @pdfs://list

# Get information about a specific paper
# Use: @pdfs://CircuitQuantumElectrodynamics.pdf

# Extract and analyze content
extract_pdf_text(
    filename='CircuitQuantumElectrodynamics.pdf',
    pages='1-5',
    max_chars=15000
)

# Use guided analysis
# /prompt analyze_pdf_prompt filename=CircuitQuantumElectrodynamics.pdf focus_area=theory
```

### **Example 3: Learn from Code Examples**

```python
# Discover available examples
# Use: @examples://list

# View source code
# Use: @examples://demo.py

# Execute and analyze
run_python_example(filename='demo.py')

# Get guided analysis
# /prompt run_example_prompt filename=demo.py analyze_output=true
```

## ⚙️ Configuration

### **Environment Variables**

Create a `.env` file in the project root:

```bash
# MCP Server Configuration
MCP_SERVER_PORT=3000
MCP_SERVER_HOST=localhost

# Qiskit Metal Configuration  
QISKIT_METAL_ENABLE_LOGGING=false
QISKIT_METAL_GUI_DISABLE=true

# PDF Processing
PDF_MAX_EXTRACT_CHARS=20000
PDF_DEFAULT_PAGES=10

# Visualization
KLAYOUT_DISABLE_MACROS=true
QT_QPA_PLATFORM=xcb
```

### **Server Configuration**

Edit `src/qiskit-metal-mcp/config.json`:

```json
{
  "server": {
    "name": "Funky Junction - Qiskit Metal MCP Server",
    "version": "1.0.0",
    "port": 3000
  },
  "resources": {
    "directory": "../../resources",
    "auto_discover": true
  },
  "tools": {
    "execution_timeout": 30,
    "max_output_chars": 15000
  }
}
```

## 🔧 Development

### **Project Structure**

```
funky-junction/
├── README.md                          # This file
├── logo.png                           # Project logo
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── src/
│   ├── qiskit-metal-mcp/
│   │   ├── quiskit-metal-mcp-server.py # Main MCP server
│   │   └── config.json                # Server configuration
│   └── resources/                     # Examples and documentation
│       ├── README.md                  # Resources overview
│       ├── *.py                       # Python examples
│       └── *.pdf                      # Research papers
├── docs/                              # Additional documentation
├── tests/                             # Unit tests
└── docker/                            # Docker configuration
```

### **Adding New Tools**

1. **Define the tool function:**
```python
@mcp.tool()
def my_new_tool(param1: str, param2: int = 5) -> str:
    """Description of what the tool does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 5)
    
    Returns:
        Success message or error details
    """
    try:
        # Tool implementation
        result = do_something(param1, param2)
        return f"✓ Success: {result}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

2. **Add comprehensive documentation**
3. **Test with various inputs**
4. **Update this README**

### **Adding New Resources**

1. **Static resource:**
```python
@mcp.resource("myresource://static")
def get_static_resource() -> str:
    """Static resource description."""
    return "# Resource Content\n\nResource information here..."
```

2. **Dynamic resource:**
```python
@mcp.resource("myresource://{identifier}")
def get_dynamic_resource(identifier: str) -> str:
    """Dynamic resource description."""
    # Process identifier and return content
    return f"# Resource: {identifier}\n\nDynamic content..."
```

### **Running Tests**

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test category
pytest tests/test_tools.py
pytest tests/test_resources.py
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src tests/
```

## 🐛 Troubleshooting

### **Common Issues**

#### **"Qiskit Metal not available" Error**
```bash
# Install Qiskit Metal
pip install qiskit-metal

# If installation fails, try:
conda install -c conda-forge qiskit-metal

# Verify installation
python -c "import qiskit_metal; print('OK')"
```

#### **PDF Extraction Not Working**
```bash
# Install PDF libraries
pip install PyPDF2 pdfplumber PyMuPDF

# Test extraction
python -c "import PyPDF2; print('PyPDF2 OK')"
python -c "import pdfplumber; print('pdfplumber OK')"
python -c "import fitz; print('PyMuPDF OK')"
```

#### **KLayout Visualization Issues**
```bash
# Install KLayout
# Ubuntu/Debian:
sudo apt install klayout

# macOS:
brew install klayout

# Windows: Download from klayout.de

# Test KLayout
klayout --version
```

#### **GDS Export Errors**
- **"Design contains no components"**: Add components before exporting
- **"Multiple cells with name"**: Clear design and rebuild
- **"Permission denied"**: Check write permissions for output directory

#### **MCP Connection Issues**
- **Port already in use**: Change port in configuration
- **Connection refused**: Ensure server is running
- **Timeout errors**: Check firewall settings

### **Debug Mode**

Enable verbose logging:

```bash
# Set environment variable
export QISKIT_METAL_DEBUG=true

# Run server with debug output
python quiskit-metal-mcp-server.py --debug
```

### **Performance Optimization**

For large designs:
```python
# Disable GUI completely
design._gui = None

# Use batch operations
components = [create_multiple_qubits(positions)]

# Optimize GDS export
export_design_to_gds(path, precision=1e-9)
```

## 📊 System Requirements

### **Minimum Requirements**
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **OS**: Windows 10, macOS 10.14, Ubuntu 18.04+

### **Recommended Requirements**
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8+ GB
- **Storage**: 10+ GB free space
- **OS**: Latest stable versions
- **Display**: 1920x1080+ for KLayout visualization

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Quick Contribution Steps**

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### **Development Guidelines**

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation as needed
- Test on multiple platforms when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Qiskit Metal Team** - Quantum circuit design framework
- **Anthropic** - Model Context Protocol specification
- **FastMCP** - Python MCP server implementation
- **KLayout** - Professional IC layout visualization
- **Research Community** - Quantum computing papers and examples

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/PaulGoldschmidt/qsim-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PaulGoldschmidt/qsim-mcp/discussions)
- **Documentation**: [Project Wiki](https://github.com/PaulGoldschmidt/qsim-mcp/wiki)

**Team Silicon Architects Contact:**
- **Sarah Dweik**
- **Sebastien Boussard** 
- **Paul Goldschmidt**
- **Gabriel Dupuis**

---

**Built with ❤️ by Team Silicon Architects for the quantum computing community**

*Funky Junction: Enabling accessible quantum circuit design through intelligent tooling and comprehensive resources.*
