#!/usr/bin/env python3

# === Imports ===
import os
from fastmcp import FastMCP

# Try to import qiskit-metal components, but make them optional
try:
    from qiskit_metal import Dict as QDict, designs, MetalGUI
    from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
    from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
    from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
    from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
    from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
    import numpy as np
    QISKIT_METAL_AVAILABLE = True
    print("✓ Qiskit Metal imported successfully")
except ImportError as e:
    print(f"⚠ Warning: Qiskit Metal not available: {e}")
    QISKIT_METAL_AVAILABLE = False
    # Create dummy classes for graceful degradation
    class DummyClass:
        def __init__(self, *args, **kwargs):
            pass
    designs = type('', (), {'DesignPlanar': DummyClass})()
    TransmonPocket = jj_manhattan = NSquareSpiral = RouteStraight = RouteMeander = OpenToGround = DummyClass

# Initialize FastMCP
mcp = FastMCP("Qiskit Metal MCP Server")

# Global holders for stateful objects
design = None
gui = None

# === Tool 1: Create Design ===
@mcp.tool()
def create_design() -> str:
    """Initialize the Qiskit Metal planar design and GUI.
    
    This is the first function you should call when starting a new quantum circuit design.
    It creates a new DesignPlanar object that serves as the foundation for all subsequent
    component additions (qubits, transmission lines, etc.).
    
    Returns:
        Success message with confirmation that the design was initialized,
        or error message if Qiskit Metal is not available or initialization fails.
        
    Prerequisites:
        - Qiskit Metal must be installed and available
        
    Example usage:
        Call this before any other design operations to set up the workspace.
    """
    global design, gui
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available. Please install qiskit-metal and its dependencies."
    
    try:
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        # Skip GUI in headless environments
        # gui = MetalGUI(design)
        return "✓ Design initialized successfully."
    except Exception as e:
        return f"❌ Error creating design: {str(e)}"

# === Tool 2: Set Design Variables ===
@mcp.tool()
def set_design_variables(cpw_width: str = '0.5um', cpw_gap: str = '0.3um', 
                        chip_size_x: str = '9mm', chip_size_y: str = '6.5mm') -> str:
    """Set basic design variables for coplanar waveguide (CPW) geometry and chip dimensions.
    
    Configures the CPW parameters and chip size that will be used throughout the design.
    These variables affect the impedance and performance characteristics of all
    transmission lines and interconnects in the quantum circuit.
    
    Args:
        cpw_width: Center conductor width (default: '0.5um')
        cpw_gap: Gap between center conductor and ground plane (default: '0.3um')
        chip_size_x: Chip width dimension (default: '9mm')
        chip_size_y: Chip height dimension (default: '6.5mm')
    
    Returns:
        Success message confirming the variables were set with their values,
        or error message if no design exists or operation fails.
        
    Prerequisites:
        - Must call create_design() first
        
    Note:
        Default values are reasonable for superconducting quantum circuits.
        Adjust based on your specific fabrication process and design requirements.
        CPW impedance is determined by width/gap ratio and substrate properties.
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."
    
    try:
        design.variables['cpw_width'] = cpw_width
        design.variables['cpw_gap'] = cpw_gap
        design._chips['main']['size']['size_x'] = chip_size_x
        design._chips['main']['size']['size_y'] = chip_size_y
        return f"✓ Design variables set: cpw_width={cpw_width}, cpw_gap={cpw_gap}, chip_size=({chip_size_x}, {chip_size_y})."
    except Exception as e:
        return f"❌ Error setting variables: {str(e)}"

# === Tool 3: Create Transmon Qubits ===
@mcp.tool()
def create_transmons(q1_name: str = 'Q1', q2_name: str = 'Q2',
                    pad_width: str = '425um', pad_height: str = '250um',
                    pocket_width: str = '650um', pocket_height: str = '450um',
                    q1_pos_x: str = '-2.5mm', q1_pos_y: str = '0mm',
                    q2_pos_x: str = '+2.5mm', q2_pos_y: str = '0mm',
                    pad_gap: str = '30um', inductor_width: str = '10um') -> str:
    """Add two customizable transmon pocket qubits to the quantum circuit design.
    
    Creates two transmon qubits with fully customizable parameters including
    dimensions, positions, and electrical properties. Transmons are the most 
    common type of superconducting qubit, consisting of a Josephson junction 
    shunted by a large capacitor formed by the pads.
    
    Args:
        q1_name: Name for the first qubit (default: 'Q1')
        q2_name: Name for the second qubit (default: 'Q2')
        pad_width: Width of main capacitor pads (default: '425um')
        pad_height: Height of main capacitor pads (default: '250um')
        pocket_width: Width of protective ground pocket (default: '650um')
        pocket_height: Height of protective ground pocket (default: '450um')
        q1_pos_x: X position of first qubit (default: '-2.5mm')
        q1_pos_y: Y position of first qubit (default: '0mm')
        q2_pos_x: X position of second qubit (default: '+2.5mm')
        q2_pos_y: Y position of second qubit (default: '0mm')
        pad_gap: Gap between capacitor pads (default: '30um')
        inductor_width: Width of inductive shunt (default: '10um')
    
    Connection pads:
        Each qubit has two connection pads:
        - 'a': Right side connection pad
        - 'b': Left side connection pad
    
    Returns:
        Success message confirming both qubits were added to the design,
        or error message if prerequisites not met or creation fails.
        
    Prerequisites:
        - Must call create_design() first
        - Qiskit Metal must be available
        
    Note:
        Default positioning places qubits 5mm apart to minimize unwanted coupling
        while allowing controlled interaction through coupling elements.
        Pad dimensions affect qubit frequency and coupling strength.
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        TransmonPocket(design, q1_name, options=dict(
            pad_width=pad_width,
            pad_height=pad_height,
            pocket_width=pocket_width,
            pocket_height=pocket_height,
            pad_gap=pad_gap,
            inductor_width=inductor_width,
            connection_pads=dict(
                a=dict(loc_W=+1, loc_H=0),
                b=dict(loc_W=-1, loc_H=0)
            ),
            pos_x=q1_pos_x,
            pos_y=q1_pos_y
        ))

        TransmonPocket(design, q2_name, options=dict(
            pad_width=pad_width,
            pad_height=pad_height,
            pocket_width=pocket_width,
            pocket_height=pocket_height,
            pad_gap=pad_gap,
            inductor_width=inductor_width,
            connection_pads=dict(
                a=dict(loc_W=+1, loc_H=0),
                b=dict(loc_W=-1, loc_H=0)
            ),
            pos_x=q2_pos_x,
            pos_y=q2_pos_y
        ))

        return f"✓ Transmon {q1_name} and {q2_name} added to design at positions ({q1_pos_x}, {q1_pos_y}) and ({q2_pos_x}, {q2_pos_y})."
    except Exception as e:
        return f"❌ Error creating transmons: {str(e)}"

# === Tool 4: Add Coupler (NSquareSpiral) ===
@mcp.tool()
def add_coupler(coupler_name: str = 'SpiralCoupler', n_turns: int = 3, 
               spacing: str = '0.2mm', width: str = '0.02mm',
               orientation: str = '0', pos_x: str = '0mm', pos_y: str = '0mm',
               subtract: bool = False) -> str:
    """Add a customizable square spiral inductor coupler to the quantum circuit design.
    
    Creates an N-turn square spiral inductor that provides controlled magnetic 
    coupling between qubits or other circuit elements. This type of coupler 
    enables two-qubit gate operations by providing tunable interaction strength 
    through mutual inductance.
    
    Args:
        coupler_name: Name for the spiral coupler component (default: 'SpiralCoupler')
        n_turns: Number of spiral turns (default: 3)
        spacing: Spacing between spiral traces (default: '0.2mm')
        width: Width of spiral traces (default: '0.02mm')
        orientation: Rotation angle in degrees (default: '0')
        pos_x: X position of spiral center (default: '0mm')
        pos_y: Y position of spiral center (default: '0mm')
        subtract: Whether to subtract from ground plane (default: False)
    
    The spiral geometry maximizes coupling strength while maintaining a compact 
    footprint. Coupling strength depends on proximity to qubits and can be tuned 
    by adjusting position, size, or number of turns.
    
    Returns:
        Success message confirming the spiral coupler was added with specifications,
        or error message if prerequisites not met or creation fails.
        
    Prerequisites:
        - Must call create_design() first
        - Qiskit Metal must be available
        
    Note:
        More turns increase inductance but also increase size and parasitic effects.
        Typical values: 2-10 turns, 0.1-0.5mm spacing, 10-50um trace width.
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        NSquareSpiral(design, coupler_name, options=dict(
            n=n_turns,
            spacing=spacing,
            width=width,
            orientation=orientation,
            pos_x=pos_x,
            pos_y=pos_y,
            subtract=str(subtract).lower()
        ))

        return f"✓ Square spiral coupler '{coupler_name}' added with {n_turns} turns at ({pos_x}, {pos_y})."
    except Exception as e:
        return f"❌ Error adding coupler: {str(e)}"

# === Tool 5: Add Josephson Junction ===
@mcp.tool()
def add_josephson_junction(junction_name: str = 'JJ1', width: str = '0.01mm',
                          orientation: str = '90', pos_x: str = '0mm', pos_y: str = '0mm',
                          pad_lower_width: str = '5um', pad_lower_height: str = '2um',
                          finger_lower_width: str = '0.2um', finger_lower_height: str = '4um',
                          extension: str = '0.2um', layer: str = '1') -> str:
    """Add a customizable Josephson junction using the Manhattan geometry model.
    
    Creates a Josephson junction with the Manhattan design, which features 
    rectangular geometry suitable for standard fabrication processes. 
    Josephson junctions are the fundamental nonlinear element in superconducting
    quantum circuits, providing the anharmonicity necessary for qubit operation.
    
    Args:
        junction_name: Name for the junction component (default: 'JJ1')
        width: Overall junction width (default: '0.01mm')
        orientation: Rotation angle in degrees (default: '90')
        pos_x: X position of junction center (default: '0mm')
        pos_y: Y position of junction center (default: '0mm')
        pad_lower_width: Width of lower junction pad (default: '5um')
        pad_lower_height: Height of lower junction pad (default: '2um')
        finger_lower_width: Width of junction constriction (default: '0.2um')
        finger_lower_height: Height of junction constriction (default: '4um')
        extension: Extension length of junction (default: '0.2um')
        layer: Fabrication layer number (default: '1')
    
    The Manhattan model uses rectangular pads with a narrow constriction to form
    the tunnel junction. Junction dimensions directly affect the critical current
    and charging energy, which determine qubit frequency and anharmonicity.
    
    Returns:
        Success message confirming the Josephson junction was added with specifications,
        or error message if prerequisites not met or creation fails.
        
    Prerequisites:
        - Must call create_design() first
        - Qiskit Metal must be available
        
    Note:
        In real devices, junctions are typically integrated into transmon structures.
        Standalone junctions are useful for analysis or specialized circuit elements.
        Critical current scales approximately with junction area.
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        jj_manhattan(design, junction_name, options=dict(
            width=width,
            orientation=orientation,
            pos_x=pos_x,
            pos_y=pos_y,
            JJ_pad_lower_width=pad_lower_width,
            JJ_pad_lower_height=pad_lower_height,
            finger_lower_width=finger_lower_width,
            finger_lower_height=finger_lower_height,
            extension=extension,
            layer=layer
        ))

        return f"✓ Josephson Junction '{junction_name}' added at ({pos_x}, {pos_y}) with {finger_lower_width} x {finger_lower_height} constriction."
    except Exception as e:
        return f"❌ Error adding junction: {str(e)}"

# # === Tool 6: Add Transmission Line and Termination ===
# @mcp.tool()
# def add_tlines_and_termination(line_name: str = 'CPW_Line', termination_name: str = 'Term1',
#                                start_component: str = 'Q1', start_pin: str = 'a',
#                                end_component: str = 'Q2', end_pin: str = 'b',
#                                termination_component: str = 'Q1', termination_pin: str = 'b',
#                                fillet: str = '50um', trace_width: str = None, trace_gap: str = None) -> str:
#     """Add a customizable coplanar waveguide (CPW) transmission line and termination.
    
#     This function creates two essential circuit elements with full customization:
    
#     1. CPW Transmission Line: Connects any two component pins using straight 
#        path routing with configurable fillet radius for smooth corners
    
#     2. Open-to-Ground Termination: Provides proper impedance termination 
#        to prevent reflections and acts as a measurement/control port
    
#     Args:
#         line_name: Name for the transmission line (default: 'CPW_Line')
#         termination_name: Name for the termination (default: 'Term1')
#         start_component: Name of component for transmission line start (default: 'Q1')
#         start_pin: Pin name on start component (default: 'a')
#         end_component: Name of component for transmission line end (default: 'Q2')
#         end_pin: Pin name on end component (default: 'b')
#         termination_component: Name of component for termination (default: 'Q1')
#         termination_pin: Pin name for termination (default: 'b')
#         fillet: Radius for rounded corners (default: '50um')
#         trace_width: CPW trace width (default: use design variable)
#         trace_gap: CPW gap width (default: use design variable)
    
#     The CPW is a low-loss transmission line ideal for microwave frequencies
#     used in quantum computing. Proper termination is crucial for signal integrity
#     and preventing unwanted standing waves.
    
#     Returns:
#         Success message confirming both transmission line and termination were added,
#         or error message if prerequisites not met or creation fails.
        
#     Prerequisites:
#         - Must call create_design() first
#         - Specified components must exist in the design
#         - Specified pins must exist on the components
#         - Qiskit Metal must be available
        
#     Note:
#         The fillet radius determines the sharpness of bends and affects
#         transmission characteristics at high frequencies. Smaller fillets
#         create sharper turns but may cause fabrication issues.
#     """
#     global design
    
#     if not QISKIT_METAL_AVAILABLE:
#         return "❌ Error: Qiskit Metal is not available."
        
#     if design is None:
#         return "❌ Please run create_design() first."

#     try:
#         # Create transmission line options
#         line_options = dict(
#             pin_inputs=dict(
#                 start_pin=(start_component, start_pin),
#                 end_pin=(end_component, end_pin)
#             ),
#             fillet=fillet
#         )
        
#         # Add trace width and gap if specified
#         if trace_width is not None:
#             line_options['trace_width'] = trace_width
#         if trace_gap is not None:
#             line_options['trace_gap'] = trace_gap
        
#         # Create the transmission line
#         RouteStraight(design, line_name, options=line_options)

#         # Create the termination
#         OpenToGround(design, termination_name, options=dict(
#             pin_inputs=dict(start_pin=(termination_component, termination_pin))
#         ))

#         return f"✓ Transmission line '{line_name}' connecting {start_component}.{start_pin} to {end_component}.{end_pin} and termination '{termination_name}' at {termination_component}.{termination_pin} added."
#     except Exception as e:
#         return f"❌ Error adding transmission line: {str(e)}"

# === Tool 7: Export Design to GDS ===
@mcp.tool()
def export_design_to_gds(export_path: str = "./quantum_design.gds") -> str:
    """Export the current quantum circuit design to a GDS (Graphic Database System) file.
    
    GDS is the industry standard file format for integrated circuit layouts and
    photolithography masks. This export enables fabrication of the designed 
    quantum circuit using standard semiconductor manufacturing processes.
    
    Export configuration:
    - Robust GDS renderer initialization and configuration
    - Design validation and rebuild before export
    - Cross-platform path handling with proper validation
    - Enhanced error handling and informative feedback
    - Output format: GDS II binary format
    
    Args:
        export_path: File path for the output GDS file (default: "./quantum_design.gds")
    
    Returns:
        Success message with absolute path to the exported file and component summary,
        or detailed error message if prerequisites not met or export fails.
        
    Prerequisites:
        - Must call create_design() first
        - Design should contain components (qubits, transmission lines, etc.)
        - Qiskit Metal must be available
        - Write permissions for the specified path
        
    Note:
        This implementation properly initializes the GDS renderer, validates the design,
        and rebuilds it before export to ensure all components are properly rendered.
        The exported GDS file can be imported into layout tools like KLayout or Cadence.
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available. Please install qiskit-metal and its dependencies."
        
    if design is None:
        return "❌ Please run create_design() first to initialize a design."

    try:
        # Validate the export path
        export_path = export_path.strip()
        if not export_path:
            export_path = "./quantum_design.gds"
            
        # Ensure the file has a .gds extension
        if not export_path.lower().endswith('.gds'):
            export_path += '.gds'
            
        # Use cross-platform paths and create directory if needed
        abs_export_path = os.path.abspath(export_path)
        export_dir = os.path.dirname(abs_export_path)
        
        # Create directory if it doesn't exist
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            
        # Validate we have write permissions
        try:
            # Test write permissions by creating a temporary file
            test_file = abs_export_path + '.temp'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (OSError, IOError) as e:
            return f"❌ Error: Cannot write to path '{abs_export_path}'. Check permissions. Details: {str(e)}"

        # Validate design has components
        if not hasattr(design, 'components') or len(design.components) == 0:
            return "❌ Warning: Design contains no components. Add some components (qubits, transmission lines, etc.) before exporting."

        # Rebuild the design to ensure all components are properly rendered
        try:
            design.rebuild()
        except Exception as rebuild_error:
            return f"❌ Error rebuilding design before export: {str(rebuild_error)}. The design may have invalid components."

        # Initialize and configure the GDS renderer
        try:
            gds_renderer = design.renderers.gds
            
            # Configure GDS export options for better compatibility
            gds_renderer.options['path_filename'] = abs_export_path
            gds_renderer.options['check_short_segments_by_scaling_fillet'] = 2.0
            gds_renderer.options['short_segments_to_not_fillet'] = 'True'
            
            # Additional options for robust export
            if hasattr(gds_renderer.options, 'precision'):
                gds_renderer.options['precision'] = 1e-9  # 1 nm precision
            if hasattr(gds_renderer.options, 'unit'):
                gds_renderer.options['unit'] = 1e-6  # 1 micron units
                
        except AttributeError as attr_error:
            return f"❌ Error: GDS renderer not properly initialized. Design may be corrupted. Details: {str(attr_error)}"

        # Perform the actual GDS export
        try:
            gds_renderer.export_to_gds(abs_export_path)
        except Exception as export_error:
            # Try alternative export method if the first one fails
            try:
                # Alternative method: render to GDS directly
                gds_renderer.render_design()
                gds_renderer.export_to_gds(abs_export_path)
            except Exception as alt_export_error:
                return f"❌ Error during GDS export: {str(export_error)}. Alternative method also failed: {str(alt_export_error)}"

        # Verify the file was created and has content
        if not os.path.exists(abs_export_path):
            return f"❌ Error: GDS file was not created at '{abs_export_path}'. Export may have failed silently."
            
        file_size = os.path.getsize(abs_export_path)
        if file_size == 0:
            return f"❌ Error: GDS file was created but is empty. Design may not have exportable geometry."

        # Generate success message with design summary
        component_count = len(design.components)
        component_names = list(design.components.keys())
        file_size_mb = file_size / (1024 * 1024)
        
        success_message = f"""✓ Design successfully exported to GDS!

File Details:
  Path: {abs_export_path}
  Size: {file_size_mb:.2f} MB ({file_size:,} bytes)
  
Design Summary:
  Components: {component_count}
  Component List: {', '.join(component_names) if component_names else 'None'}
  
Export Settings:
  Precision: 1 nm
  Units: 1 μm  
  Fillet scaling: 2.0x
  Short segments handling: Enabled

Next Steps:
  1. Open the GDS file in KLayout, Cadence, or similar layout tool
  2. Verify the geometry renders correctly
  3. Run design rule checks (DRC) for your fabrication process
  4. Generate process-specific masks and submit for fabrication"""

        return success_message

    except Exception as e:
        return f"❌ Unexpected error during GDS export: {str(e)}. Please check your design and try again."

# === Tool 8: Get Design Info ===
@mcp.tool()
def get_design_info() -> str:
    """Retrieve comprehensive information about the current quantum circuit design.
    
    Returns a detailed summary of the design state including:
    - List of all components (qubits, transmission lines, couplers, junctions, etc.)
    - Design variables (CPW width, gap, and other global parameters)  
    - Design name and class type
    - Current design status
    
    This function is useful for:
    - Debugging design issues
    - Verifying component additions
    - Documenting design parameters
    - Checking design state before export operations
    
    Returns:
        Formatted string containing complete design information,
        or error message if no design exists or information cannot be retrieved.
        
    Prerequisites:
        - Must call create_design() first
        - Qiskit Metal must be available
        
    Note:
        The component list shows all successfully added elements.
        If a component is missing from the list, it may not have been
        properly created or an error occurred during its addition.
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ No design created yet. Please run create_design() first."
    
    try:
        components = list(design.components.keys())
        variables = dict(design.variables)
        
        info = f"""
✓ Current Design Information:
========================
Components: {', '.join(components) if components else 'None'}
Variables: {variables}
Design Name: {design.name}
Design Class: {design.__class__.__name__}
        """
        return info.strip()
    except Exception as e:
        return f"❌ Error getting design info: {str(e)}"

# === Tool 9: Clear Design ===
@mcp.tool()
def clear_design() -> str:
    """Clear the current design and reset to initial state for starting fresh.
    
    This function performs a complete reset of the design workspace by:
    - Removing all components (qubits, transmission lines, couplers, etc.)
    - Clearing design variables and settings
    - Resetting the GUI state (if applicable)
    - Freeing memory used by the current design
    
    Use this function when you want to:
    - Start a completely new design from scratch
    - Clear a corrupted or problematic design state  
    - Reset after testing or experimentation
    - Free up memory from large designs
    
    Returns:
        Success message confirming the design was cleared,
        or error message if clearing operation fails.
        
    Prerequisites:
        - None (can be called at any time)
        
    Note:
        This operation is irreversible! Make sure to export your design
        to GDS or save it before clearing if you want to preserve the work.
        After clearing, you must call create_design() again to start working.
    """
    global design, gui
    try:
        design = None
        gui = None
        return "✓ Design cleared successfully."
    except Exception as e:
        return f"❌ Error clearing design: {str(e)}"

# === Tool 10: Connect Components with Meandered CPW ===
@mcp.tool()
def connect_components(component_name: str, component1: str, pin1: str, component2: str, pin2: str,
                      length: str, asymmetry: str = '0um', flip: bool = False, fillet: str = '90um') -> str:
    """Connect any two component pins with a meandered coplanar waveguide (CPW) transmission line.
    
    This is a generalized connection function that creates flexible routing between
    any components in the quantum circuit using meandered (zigzag) CPW geometry.
    The meander pattern allows for precise length control and compact routing.
    
    Args:
        component_name: Name for the new CPW route (must be unique in design)
        component1: Name of the first component to connect
        pin1: Pin name on the first component (e.g., 'a', 'b', 'coupling_out')
        component2: Name of the second component to connect  
        pin2: Pin name on the second component (e.g., 'a', 'b', 'coupling_in')
        length: Total electrical length of the meandered line (e.g., '2mm', '500um')
        asymmetry: Offset for meander pattern asymmetry (default: '0um')
        flip: Whether to flip the lead direction (default: False)
        fillet: Radius for rounded corners to improve fabrication (default: '90um')
    
    Key features:
    - Automatic routing between any two pins
    - Precise length control for timing/phase requirements
    - HFSS wire bond compatibility for electromagnetic simulation
    - Configurable meander pattern for compact layouts
    
    Returns:
        Success message with connection details,
        or error message if components don't exist or connection fails.
        
    Prerequisites:
        - Must call create_design() first
        - Both components must exist in the design
        - Specified pins must exist on the components
        - Qiskit Metal must be available
        
    Example usage:
        connect_components('Q1_Q2_link', 'Q1', 'a', 'Q2', 'b', '1.5mm')
        connect_components('readout_line', 'Q1', 'b', 'resonator', 'input', '800um', flip=True)
    """
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        # Create options dictionary for the meandered route
        myoptions = QDict(
            fillet=fillet,
            hfss_wire_bonds=True,
            pin_inputs=QDict(
                start_pin=QDict(
                    component=component1,
                    pin=pin1),
                end_pin=QDict(
                    component=component2,
                    pin=pin2)),
            total_length=length
        )
        
        # Set meander options
        myoptions.meander = QDict()
        myoptions.meander.asymmetry = asymmetry
        myoptions.meander.lead_direction_inverted = 'true' if flip else 'false'
        
        # Create the meandered route
        route = RouteMeander(design, component_name, myoptions)
        
        return f"✓ Connected {component1}.{pin1} to {component2}.{pin2} with meandered CPW '{component_name}' (length: {length})"
    except Exception as e:
        return f"❌ Error connecting components: {str(e)}"

# === Tool 11: Check Status ===
@mcp.tool()
def check_status() -> str:
    """Check the comprehensive status of the Qiskit Metal MCP server and current design.
    
    Provides a complete health check and status report including:
    - Qiskit Metal installation status and availability
    - Current design state (created/not created)
    - Component count and list of all components in the design
    - Server readiness for design operations
    
    This function is useful for:
    - Troubleshooting connection or installation issues
    - Verifying server state before starting design work
    - Monitoring design progress and component count
    - Debugging when operations fail unexpectedly
    
    Returns:
        Formatted status report with all relevant information,
        including any error conditions or missing dependencies.
        
    Prerequisites:
        - None (can be called at any time)
        
    Note:
        This is a read-only operation that doesn't modify the design.
        If Qiskit Metal shows as unavailable, check your installation
        and ensure all dependencies are properly installed.
    """
    status = f"""
🔍 Qiskit Metal MCP Server Status:
================================
Qiskit Metal Available: {'✓ Yes' if QISKIT_METAL_AVAILABLE else '❌ No'}
Current Design: {'✓ Created' if design is not None else '❌ Not created'}
"""
    if design is not None:
        try:
            components = list(design.components.keys())
            status += f"Components: {len(components)} ({', '.join(components) if components else 'None'})\n"
        except:
            status += "Components: Error reading\n"
    
    return status.strip()

if __name__ == "__main__":
    print("🚀 Starting Qiskit Metal FastMCP Server...")
    print(f"📊 Qiskit Metal Available: {QISKIT_METAL_AVAILABLE}")
    mcp.run()
