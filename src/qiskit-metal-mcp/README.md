# Qiskit Metal MCP Server

A Model Context Protocol (MCP) server for Qiskit Metal that enables AI assistants to design, simulate, and analyze quantum circuits through natural language commands.

## Features

### Circuit Design
- **Create Designs**: Initialize new quantum circuit designs
- **Add Transmon Qubits**: Place superconducting transmon qubits with customizable parameters
- **Add Transmission Lines**: Create meandered and straight transmission lines
- **Add Couplers**: Implement coupled line tee couplers for qubit interactions
- **Component Management**: Add various quantum circuit components

### Visualization & Export
- **Render Designs**: Generate visual representations using matplotlib or GDS format
- **Export Netlists**: Export circuit descriptions for external simulation tools
- **Multiple Formats**: Support for PNG, GDS, and other output formats

### Analysis & Simulation
- **LOM Analysis**: Lumped Oscillator Model analysis for qubit frequencies
- **EPR Analysis**: Energy Participation Ratio analysis for coupling strengths
- **Circuit Simulation**: DC, AC, and transient simulation capabilities
- **Design Information**: Extract detailed component and design information

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

2. **Install Qiskit Metal** (if not already installed):
   ```bash
   pip install qiskit-metal
   ```

## Usage

### Starting the Server

Run the MCP server:
```bash
python qiskit_metal_mcp.py
```

### Available Tools

#### 1. Create Design
```python
create_design(design_name: str = "quantum_circuit")
```
Creates a new Qiskit Metal design for quantum circuit layout.

#### 2. Add Transmon Qubit
```python
add_transmon_qubit(
    qubit_name: str,
    pos_x: float = 0.0,
    pos_y: float = 0.0,
    pocket_width: float = 0.5,
    pocket_height: float = 0.5,
    connection_pads: Dict[str, Any] = None
)
```
Adds a superconducting transmon qubit to the design.

#### 3. Add Meandered Line
```python
add_meandered_line(
    line_name: str,
    start_point: List[float],
    end_point: List[float],
    width: float = 0.01,
    meander_length: float = 0.1
)
```
Adds a meandered transmission line for routing.

#### 4. Add Coupler
```python
add_coupler(
    coupler_name: str,
    pos_x: float = 0.0,
    pos_y: float = 0.0,
    coupling_length: float = 0.2,
    coupling_gap: float = 0.02
)
```
Adds a coupled line tee for qubit coupling.

#### 5. Render Design
```python
render_design(
    output_format: str = "matplotlib",
    save_path: Optional[str] = None,
    show_ports: bool = True,
    show_names: bool = True
)
```
Renders the design and optionally saves it to a file.

#### 6. Analyze Circuit
```python
analyze_circuit(
    analysis_type: str = "LOM",
    qubit_names: Optional[List[str]] = None,
    coupling_names: Optional[List[str]] = None
)
```
Performs LOM or EPR analysis on the circuit.

#### 7. Get Design Info
```python
get_design_info()
```
Returns detailed information about the current design.

#### 8. Export Netlist
```python
export_netlist(file_path: str)
```
Exports the design as a netlist file.

#### 9. Simulate Circuit
```python
simulate_circuit(
    simulation_type: str = "DC",
    voltage_sweep: Optional[List[float]] = None,
    frequency_sweep: Optional[List[float]] = None
)
```
Performs circuit simulation with various sweep options.

## Example Workflow

1. **Create a new design**:
   ```
   create_design("my_quantum_circuit")
   ```

2. **Add qubits**:
   ```
   add_transmon_qubit("q1", 0.0, 0.0)
   add_transmon_qubit("q2", 0.5, 0.0)
   ```

3. **Add coupling**:
   ```
   add_coupler("c1", 0.25, 0.0)
   ```

4. **Add transmission lines**:
   ```
   add_meandered_line("tl1", [0.0, 0.2], [0.5, 0.2])
   ```

5. **Render the design**:
   ```
   render_design("matplotlib", "circuit.png")
   ```

6. **Analyze the circuit**:
   ```
   analyze_circuit("LOM", ["q1", "q2"])
   ```

## Integration with AI Assistants

This MCP server can be integrated with AI assistants like Claude to enable natural language quantum circuit design:

- **Natural Language Commands**: "Create a 3-qubit circuit with nearest-neighbor coupling"
- **Interactive Design**: "Add a transmon qubit at position (1, 0) and connect it to the existing qubit"
- **Analysis Requests**: "What are the resonant frequencies of all qubits in the circuit?"
- **Visualization**: "Show me a 3D view of the circuit layout"

## Dependencies

- `qiskit-metal`: Core quantum circuit design framework
- `qiskit`: Quantum computing framework
- `numpy`: Numerical computing
- `matplotlib`: Plotting and visualization
- `scipy`: Scientific computing
- `pandas`: Data manipulation
- `plotly`: Interactive plotting
- `kaleido`: Static image export for plotly

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:

- Additional quantum components
- New analysis methods
- Enhanced visualization options
- Performance improvements
- Documentation updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.
