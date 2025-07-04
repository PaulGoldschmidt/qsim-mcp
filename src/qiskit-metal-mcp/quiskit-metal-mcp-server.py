#!/usr/bin/env python3

# === Imports ===
import os
import json
from pathlib import Path
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

# Resources directory path
RESOURCES_DIR = Path(__file__).parent.parent / "resources"

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
        TransmonPocket(design, q1_name, options=QDict(
            pad_width=pad_width,
            pad_height=pad_height,
            pocket_width=pocket_width,
            pocket_height=pocket_height,
            pad_gap=pad_gap,
            inductor_width=inductor_width,
            connection_pads=QDict(
                a=QDict(loc_W=+1, loc_H=0),
                b=QDict(loc_W=-1, loc_H=0)
            ),
            pos_x=q1_pos_x,
            pos_y=q1_pos_y
        ))

        TransmonPocket(design, q2_name, options=QDict(
            pad_width=pad_width,
            pad_height=pad_height,
            pocket_width=pocket_width,
            pocket_height=pocket_height,
            pad_gap=pad_gap,
            inductor_width=inductor_width,
            connection_pads=QDict(
                a=QDict(loc_W=+1, loc_H=0),
                b=QDict(loc_W=-1, loc_H=0)
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
        NSquareSpiral(design, coupler_name, options=QDict(
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
        jj_manhattan(design, junction_name, options=QDict(
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
        # Get current working directory for relative path resolution
        current_dir = os.getcwd()
        
        # Validate the export path
        export_path = export_path.strip()
        if not export_path:
            export_path = "./quantum_design.gds"
            
        # Ensure the file has a .gds extension
        if not export_path.lower().endswith('.gds'):
            export_path += '.gds'
            
        # Handle path resolution - if relative, resolve from current working directory
        if not os.path.isabs(export_path):
            abs_export_path = os.path.join(current_dir, export_path)
        else:
            abs_export_path = export_path
            
        # Normalize the path
        abs_export_path = os.path.normpath(abs_export_path)
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

        # Initialize and configure the GDS renderer first
        try:
            gds_renderer = design.renderers.gds
            
            # Comprehensive clearing of GDS renderer to prevent duplicate cell names
            # Clear the GDS library completely
            if hasattr(gds_renderer, 'lib') and gds_renderer.lib is not None:
                gds_renderer.lib = None
            
            # Clear any existing data structures
            if hasattr(gds_renderer, 'clear_data'):
                gds_renderer.clear_data()
            elif hasattr(gds_renderer, 'clear'):
                gds_renderer.clear()
            
            # Reset any internal state
            if hasattr(gds_renderer, '_lib'):
                gds_renderer._lib = None
            if hasattr(gds_renderer, '_main_cell'):
                gds_renderer._main_cell = None
            if hasattr(gds_renderer, 'elements'):
                gds_renderer.elements = {}
            
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

        # Rebuild the design to ensure all components are properly rendered
        try:
            design.rebuild()
        except Exception as rebuild_error:
            return f"❌ Error rebuilding design before export: {str(rebuild_error)}. The design may have invalid components."

        # Perform the actual GDS export with proper error handling for duplicate cells
        try:
            # Final clear before export to ensure clean state
            if hasattr(gds_renderer, 'clear_data'):
                gds_renderer.clear_data()
            elif hasattr(gds_renderer, 'clear'):
                gds_renderer.clear()
            
            # Reset library one more time to be absolutely sure
            if hasattr(gds_renderer, 'lib'):
                gds_renderer.lib = None
            
            gds_renderer.export_to_gds(abs_export_path)
        except Exception as export_error:
            # If we get a duplicate cell error, try more aggressive clearing
            if "Multiple cells with name" in str(export_error) or "Cell named" in str(export_error):
                try:
                    # Force complete reset of the GDS renderer
                    gds_renderer = design.renderers.gds
                    
                    # Clear all possible state variables
                    for attr in ['lib', '_lib', '_main_cell', 'elements', 'cells']:
                        if hasattr(gds_renderer, attr):
                            setattr(gds_renderer, attr, None if attr.endswith('cell') or attr.endswith('lib') else {})
                    
                    # Try all clearing methods
                    for clear_method in ['clear_data', 'clear', 'reset']:
                        if hasattr(gds_renderer, clear_method):
                            getattr(gds_renderer, clear_method)()
                    
                    # Re-render the design fresh
                    if hasattr(gds_renderer, 'render_design'):
                        gds_renderer.render_design()
                    
                    # Try export again
                    gds_renderer.export_to_gds(abs_export_path)
                except Exception as alt_export_error:
                    return f"❌ Error during GDS export (duplicate cells): {str(export_error)}. Retry also failed: {str(alt_export_error)}\n\nSuggestion: Try clearing the design and recreating it from scratch."
            else:
                return f"❌ Error during GDS export: {str(export_error)}"

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
        
        # Calculate relative path for user-friendly display
        try:
            rel_export_path = os.path.relpath(abs_export_path, current_dir)
        except ValueError:
            rel_export_path = abs_export_path
            
        success_message = f"""✓ Design successfully exported to GDS!

File Details:
  Relative Path: {rel_export_path}
  Absolute Path: {abs_export_path}
  Working Directory: {current_dir}
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

# === Tool 12: Visualize GDS with KLayout ===
@mcp.tool()
def visualize_gds_with_klayout(gds_file_path: str) -> str:
    """Open and visualize a GDS file using KLayout viewer.
    
    This function launches KLayout, a professional IC layout tool, to visualize
    GDS files containing quantum circuit designs. KLayout provides advanced 
    visualization capabilities including layer management, measurement tools,
    and 3D viewing for comprehensive design review.
    
    Args:
        gds_file_path: Path to the GDS file to visualize (e.g., './quantum_design.gds')
    
    Features of KLayout visualization:
    - High-resolution vector graphics rendering
    - Layer-by-layer view control with color coding
    - Precise measurement and annotation tools
    - Zoom and pan for detailed inspection
    - Cross-sectional views for multi-layer designs
    - Export capabilities (PNG, SVG, PDF)
    
    Returns:
        Success message confirming KLayout was launched with the GDS file,
        or detailed error message if KLayout is not available or file issues exist.
        
    Prerequisites:
        - KLayout must be installed and accessible in system PATH
        - Valid GDS file must exist at the specified path
        - Display environment for GUI applications (not headless)
        
    Installation notes:
        - Linux: sudo apt install klayout  or  conda install -c conda-forge klayout
        - macOS: brew install klayout  or  download from klayout.de
        - Windows: Download installer from klayout.de
        
    Note:
        KLayout will launch as a separate application window. The function returns
        immediately after launching - KLayout runs independently of the MCP server.
        Use this for design verification, measurements, and preparing documentation.
    """
    import subprocess
    import shutil
    
    try:
        # Validate the input file path
        gds_file_path = gds_file_path.strip()
        if not gds_file_path:
            return "❌ Error: No GDS file path provided."
        
        # Convert to absolute path for better reliability
        abs_gds_path = os.path.abspath(gds_file_path)
        
        # Check if the GDS file exists
        if not os.path.exists(abs_gds_path):
            return f"❌ Error: GDS file not found at '{abs_gds_path}'.\n\nPlease check the file path and ensure the file exists."
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(abs_gds_path):
            return f"❌ Error: '{abs_gds_path}' is not a file."
        
        # Verify it has a .gds extension (case insensitive)
        if not abs_gds_path.lower().endswith('.gds'):
            return f"❌ Warning: File '{abs_gds_path}' does not have a .gds extension. This may not be a valid GDS file."
        
        # Check file size to ensure it's not empty
        file_size = os.path.getsize(abs_gds_path)
        if file_size == 0:
            return f"❌ Error: GDS file '{abs_gds_path}' is empty (0 bytes)."
        
        # Check if KLayout is installed and accessible
        klayout_cmd = None
        for cmd_name in ['klayout', 'klayout_app', 'klayout.exe']:
            if shutil.which(cmd_name):
                klayout_cmd = cmd_name
                break
        
        if not klayout_cmd:
            return """❌ Error: KLayout not found in system PATH.

Installation Instructions:
==========================
• Linux (Ubuntu/Debian): sudo apt install klayout
• Linux (conda): conda install -c conda-forge klayout  
• macOS (Homebrew): brew install klayout
• macOS/Windows: Download from https://www.klayout.de/build.html

After installation, ensure 'klayout' command is accessible from terminal.

Alternative:
If KLayout is installed but not in PATH, you can try:
- Add KLayout installation directory to your PATH environment variable
- Use the full path to KLayout executable in the gds_file_path parameter"""
        
        # Set up environment for GUI fixes (resolves Wayland/Qt issues)
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'xcb'  # Force X11 backend (fixes Wayland issues)
        env['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'  # Reduce Qt warnings
        env['QT_X11_NO_MITSHM'] = '1'  # Fix threading issues
        env['KLAYOUT_DISABLE_MACROS'] = '1'  # Disable problematic plugins

        # Launch KLayout with the GDS file and GUI fixes
        try:
            # Use subprocess.Popen for non-blocking launch with error suppression
            # KLayout will run independently of this script
            process = subprocess.Popen(
                [klayout_cmd, '-nc', '-z', abs_gds_path],  # -nc: no config, -z: no splash
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent process
            )
            
            # Give it a moment to start
            import time
            time.sleep(1)
            
            # Check if the process started successfully
            if process.poll() is None:
                # Process is still running (good)
                file_size_mb = file_size / (1024 * 1024)
                
                return f"""✅ KLayout launched successfully with GUI fixes!

File Information:
================
• File: {abs_gds_path}
• Size: {file_size_mb:.2f} MB ({file_size:,} bytes)
• Process ID: {process.pid}
• GUI Backend: X11 (xcb)

Applied Fixes:
=============
• Qt X11 backend (fixes Wayland issues)
• Error suppression (reduces console spam)
• Threading fixes (resolves QSocketNotifier warnings)
• No splash screen (faster startup)
• Disabled problematic macros (LVS/DRC)

KLayout Usage Tips:
==================
• Use mouse wheel to zoom in/out
• Drag to pan around the design
• Press 'F' to fit design to window
• Use Layers panel to control visibility
• Right-click for context menus
• Ruler tool for measurements (press 'R')
• Press 'Escape' to clear selections

The KLayout window should now be open with your quantum circuit design.
If KLayout doesn't appear, check: ps aux | grep klayout
KLayout runs independently - you can continue using other MCP functions."""
            else:
                # Process exited immediately (probably an error)
                return_code = process.poll()
                return f"❌ Error: KLayout exited immediately with code {return_code}. Try using the launcher script: ./launch_klayout.sh {abs_gds_path}"
                
        except subprocess.SubprocessError as e:
            return f"❌ Error launching KLayout: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error launching KLayout: {str(e)}"
    
    except Exception as e:
        return f"❌ Unexpected error in visualize_gds_with_klayout: {str(e)}"

# === Tool 13: Export GDS to PNG ===
@mcp.tool()
def export_gds_to_png(gds_file_path: str, png_output_path: str = None, 
                     width: int = 1920, height: int = 1080, dpi: int = 300) -> str:
    """Export a GDS file to a PNG image for easy visualization and documentation.
    
    This function converts GDS layout files into high-quality PNG images without
    requiring GUI applications. Perfect for documentation, presentations, and
    quick visualization of quantum circuit designs.
    
    Args:
        gds_file_path: Path to the input GDS file (e.g., './quantum_design.gds')
        png_output_path: Path for output PNG file (default: auto-generated from GDS filename)
        width: Image width in pixels (default: 1920)
        height: Image height in pixels (default: 1080)
        dpi: Resolution in dots per inch (default: 300)
    
    Features:
    - High-resolution PNG export suitable for publications
    - Automatic fitting and scaling of the design
    - Multiple rendering backends (gdspy, gdstk, KLayout batch mode)
    - Cross-platform compatibility
    - No GUI required - works in headless environments
    
    Returns:
        Success message with PNG file path and image details,
        or error message if conversion fails.
        
    Prerequisites:
        - Valid GDS file must exist
        - One of: gdspy, gdstk, or KLayout must be available
        - Write permissions for output directory
        
    Note:
        This function tries multiple rendering methods automatically:
        1. gdspy (if available) - Fast and reliable
        2. gdstk (if available) - Modern alternative to gdspy  
        3. KLayout batch mode (if available) - Professional quality
        Image quality and layer colors may vary between methods.
    """
    import subprocess
    import shutil
    
    try:
        # Get current working directory for path resolution
        current_dir = os.getcwd()
        
        # Validate input file path
        gds_file_path = gds_file_path.strip()
        if not gds_file_path:
            return "❌ Error: No GDS file path provided."
        
        # Handle GDS file path resolution
        if not os.path.isabs(gds_file_path):
            abs_gds_path = os.path.join(current_dir, gds_file_path)
        else:
            abs_gds_path = gds_file_path
        abs_gds_path = os.path.normpath(abs_gds_path)
        
        # Check if GDS file exists
        if not os.path.exists(abs_gds_path):
            return f"❌ Error: GDS file not found at '{abs_gds_path}'.\n📂 Current directory: {current_dir}\n📁 Looking for: {gds_file_path}"
        
        if not os.path.isfile(abs_gds_path):
            return f"❌ Error: '{abs_gds_path}' is not a file."
        
        # Check file size
        file_size = os.path.getsize(abs_gds_path)
        if file_size == 0:
            return f"❌ Error: GDS file is empty (0 bytes)."
        
        # Generate output path if not specified
        if png_output_path is None:
            base_name = os.path.splitext(os.path.basename(abs_gds_path))[0]
            png_output_path = f"{base_name}_visualization.png"
        
        # Handle PNG output path resolution
        if not os.path.isabs(png_output_path):
            abs_png_path = os.path.join(current_dir, png_output_path)
        else:
            abs_png_path = png_output_path
        abs_png_path = os.path.normpath(abs_png_path)
        
        # Ensure PNG extension
        if not abs_png_path.lower().endswith('.png'):
            abs_png_path += '.png'
        
        # Create output directory if needed
        output_dir = os.path.dirname(abs_png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Try multiple rendering methods in order of preference
        
        # Method 1: Try gdspy (fast and reliable)
        try:
            import gdspy
            return _export_gds_to_png_gdspy(abs_gds_path, abs_png_path, width, height, dpi)
        except ImportError:
            pass
        except Exception as e:
            print(f"gdspy method failed: {e}")
        
        # Method 2: Try gdstk (modern alternative)
        try:
            import gdstk
            return _export_gds_to_png_gdstk(abs_gds_path, abs_png_path, width, height, dpi)
        except ImportError:
            pass
        except Exception as e:
            print(f"gdstk method failed: {e}")
        
        # Method 3: Try KLayout in batch mode (high quality)
        klayout_cmd = None
        for cmd_name in ['klayout', 'klayout_app', 'klayout.exe']:
            if shutil.which(cmd_name):
                klayout_cmd = cmd_name
                break
        
        if klayout_cmd:
            try:
                return _export_gds_to_png_klayout(abs_gds_path, abs_png_path, width, height, dpi, klayout_cmd)
            except Exception as e:
                print(f"KLayout batch method failed: {e}")
        
        # If all methods fail, return helpful error message
        # Calculate relative paths for display
        try:
            rel_gds_path = os.path.relpath(abs_gds_path, current_dir)
            rel_png_path = os.path.relpath(abs_png_path, current_dir)
        except ValueError:
            rel_gds_path = abs_gds_path
            rel_png_path = abs_png_path
            
        return f"""❌ Error: No suitable GDS rendering library found.

To enable GDS to PNG conversion, install one of these options:

**Option 1 - gdspy (Recommended):**
```bash
pip install gdspy matplotlib pillow
```

**Option 2 - gdstk (Modern alternative):**
```bash
pip install gdstk matplotlib pillow
```

**Option 3 - KLayout (Professional):**
- Linux: sudo apt install klayout
- macOS: brew install klayout
- Windows: Download from https://www.klayout.de/

File Information:
• GDS File: {rel_gds_path}
• Absolute Path: {abs_gds_path}
• Working Directory: {current_dir}
• Size: {file_size / (1024*1024):.2f} MB
• Desired Output: {rel_png_path}

Once a library is installed, try running this function again."""
        
    except Exception as e:
        return f"❌ Unexpected error in export_gds_to_png: {str(e)}"

def _export_gds_to_png_gdspy(gds_path, png_path, width, height, dpi):
    """Export GDS to PNG using gdspy library."""
    import gdspy
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.collections import PatchCollection
    
    try:
        # Load the GDS file
        gdsii = gdspy.GdsLibrary(infile=gds_path)
        
        # Get the first cell (usually the top cell)
        if not gdsii.cells:
            return f"❌ Error: No cells found in GDS file."
        
        cell_name = list(gdsii.cells.keys())[0]
        cell = gdsii.cells[cell_name]
        
        # Create figure with specified dimensions
        fig_width = width / dpi
        fig_height = height / dpi
        fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height), dpi=dpi)
        
        # Get all polygons from the cell
        polygons = cell.get_polygons(by_spec=True)
        
        if not polygons:
            return f"❌ Error: No polygons found in GDS cell '{cell_name}'."
        
        # Color map for different layers
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        all_patches = []
        layer_info = []
        
        for spec, poly_list in polygons.items():
            layer = spec[0]
            color = colors[layer % len(colors)]
            
            layer_info.append(f"Layer {layer}: {len(poly_list)} polygons")
            
            for poly in poly_list:
                if len(poly) >= 3:  # Valid polygon needs at least 3 points
                    patch = patches.Polygon(poly, closed=True, facecolor=color, 
                                          edgecolor='black', alpha=0.7, linewidth=0.5)
                    all_patches.append(patch)
        
        # Add all patches to the plot
        if all_patches:
            collection = PatchCollection(all_patches, match_original=True)
            ax.add_collection(collection)
        
        # Set aspect ratio and fit to data
        ax.set_aspect('equal')
        ax.autoscale()
        
        # Remove axes for cleaner look
        ax.set_xlabel('X (μm)')
        ax.set_ylabel('Y (μm)')
        ax.grid(True, alpha=0.3)
        
        # Add title
        ax.set_title(f'Quantum Circuit Layout - {os.path.basename(gds_path)}', 
                    fontsize=12, fontweight='bold')
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(png_path, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        # Get file info
        png_size = os.path.getsize(png_path)
        png_size_mb = png_size / (1024 * 1024)
        
        # Calculate relative paths for display
        current_dir = os.getcwd()
        try:
            rel_gds_path = os.path.relpath(gds_path, current_dir)
            rel_png_path = os.path.relpath(png_path, current_dir)
        except ValueError:
            rel_gds_path = gds_path
            rel_png_path = png_path
            
        return f"""✅ Successfully exported GDS to PNG using gdspy!

📁 **File Information:**
• Input GDS: {rel_gds_path}
• Output PNG: {rel_png_path}
• Working Directory: {current_dir}
• PNG Size: {png_size_mb:.2f} MB ({png_size:,} bytes)

🎨 **Image Details:**
• Dimensions: {width} x {height} pixels
• Resolution: {dpi} DPI
• Cell: {cell_name}
• Layers Found: {len(polygons)}
• Total Polygons: {sum(len(polys) for polys in polygons.values())}

📊 **Layer Summary:**
{chr(10).join(layer_info)}

🎯 **Rendering Method:** gdspy + matplotlib
✨ **Quality:** High-resolution vector-based rendering suitable for publications

The PNG file is ready for use in presentations, documentation, or further analysis!"""
        
    except Exception as e:
        return f"❌ Error with gdspy export: {str(e)}"

def _export_gds_to_png_gdstk(gds_path, png_path, width, height, dpi):
    """Export GDS to PNG using gdstk library."""
    import gdstk
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.collections import PatchCollection
    
    try:
        # Load the GDS file
        library = gdstk.read_gds(gds_path)
        
        if not library.cells:
            return f"❌ Error: No cells found in GDS file."
        
        # Get the top cell (last one is usually the main cell)
        cell = library.cells[-1]
        
        # Create figure
        fig_width = width / dpi
        fig_height = height / dpi
        fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height), dpi=dpi)
        
        # Color map for different layers
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        all_patches = []
        layer_count = {}
        
        # Process all polygons in the cell
        for polygon in cell.polygons:
            layer = polygon.layer
            if layer not in layer_count:
                layer_count[layer] = 0
            layer_count[layer] += 1
            
            color = colors[layer % len(colors)]
            
            # Get polygon points
            points = polygon.points
            if len(points) >= 3:
                patch = patches.Polygon(points, closed=True, facecolor=color,
                                      edgecolor='black', alpha=0.7, linewidth=0.5)
                all_patches.append(patch)
        
        # Add all patches to the plot
        if all_patches:
            collection = PatchCollection(all_patches, match_original=True)
            ax.add_collection(collection)
        
        # Set aspect ratio and fit to data
        ax.set_aspect('equal')
        ax.autoscale()
        
        # Styling
        ax.set_xlabel('X (μm)')
        ax.set_ylabel('Y (μm)')
        ax.grid(True, alpha=0.3)
        ax.set_title(f'Quantum Circuit Layout - {os.path.basename(gds_path)}', 
                    fontsize=12, fontweight='bold')
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(png_path, dpi=dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        # Get file info
        png_size = os.path.getsize(png_path)
        png_size_mb = png_size / (1024 * 1024)
        
        layer_info = [f"Layer {layer}: {count} polygons" for layer, count in sorted(layer_count.items())]
        
        # Calculate relative paths for display
        current_dir = os.getcwd()
        try:
            rel_gds_path = os.path.relpath(gds_path, current_dir)
            rel_png_path = os.path.relpath(png_path, current_dir)
        except ValueError:
            rel_gds_path = gds_path
            rel_png_path = png_path
            
        return f"""✅ Successfully exported GDS to PNG using gdstk!

📁 **File Information:**
• Input GDS: {rel_gds_path}
• Output PNG: {rel_png_path}
• Working Directory: {current_dir}
• PNG Size: {png_size_mb:.2f} MB ({png_size:,} bytes)

🎨 **Image Details:**
• Dimensions: {width} x {height} pixels
• Resolution: {dpi} DPI
• Cell: {cell.name}
• Layers Found: {len(layer_count)}
• Total Polygons: {sum(layer_count.values())}

📊 **Layer Summary:**
{chr(10).join(layer_info)}

🎯 **Rendering Method:** gdstk + matplotlib
✨ **Quality:** Modern high-resolution rendering

The PNG file is ready for presentations and documentation!"""
        
    except Exception as e:
        return f"❌ Error with gdstk export: {str(e)}"

def _export_gds_to_png_klayout(gds_path, png_path, width, height, dpi, klayout_cmd):
    """Export GDS to PNG using KLayout in batch mode."""
    import subprocess
    import tempfile
    
    try:
        # Create a simple KLayout script for PNG export
        script_content = f"""
import pya

# Load the GDS file
app = pya.Application.instance()
main_window = app.main_window()
layout_view = main_window.create_layout(0)
layout_view.load_layout("{gds_path}")

# Fit the view
layout_view.zoom_fit()

# Set up export options
save_options = pya.SaveLayoutOptions()
save_options.set_format("PNG")
save_options.set_scale_factor(1.0)

# Export to PNG
layout_view.save_image("{png_path}", {width}, {height})

# Exit
app.exit(0)
"""
        
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Run KLayout in batch mode
            result = subprocess.run(
                [klayout_cmd, '-b', '-r', script_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check if PNG was created
            if os.path.exists(png_path):
                png_size = os.path.getsize(png_path)
                png_size_mb = png_size / (1024 * 1024)
                
                # Calculate relative paths for display
                current_dir = os.getcwd()
                try:
                    rel_gds_path = os.path.relpath(gds_path, current_dir)
                    rel_png_path = os.path.relpath(png_path, current_dir)
                except ValueError:
                    rel_gds_path = gds_path
                    rel_png_path = png_path
                    
                return f"""✅ Successfully exported GDS to PNG using KLayout batch mode!

📁 **File Information:**
• Input GDS: {rel_gds_path}
• Output PNG: {rel_png_path}
• Working Directory: {current_dir}
• PNG Size: {png_size_mb:.2f} MB ({png_size:,} bytes)

🎨 **Image Details:**
• Dimensions: {width} x {height} pixels
• Resolution: {dpi} DPI

🎯 **Rendering Method:** KLayout Professional
✨ **Quality:** Professional layout tool rendering

The PNG export is complete and ready for use!"""
            else:
                return f"❌ Error: KLayout did not create PNG file. Return code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
        
        finally:
            # Clean up temporary script file
            try:
                os.unlink(script_path)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return f"❌ Error: KLayout batch export timed out after 60 seconds."
    except Exception as e:
        return f"❌ Error with KLayout batch export: {str(e)}"

# === Resource 1: List All Resources ===
@mcp.resource("resources://list")
def get_all_resources() -> str:
    """
    List all available resources in the resources directory including Python examples and PDFs.
    
    This resource provides a comprehensive list of all files that can be accessed
    for quantum circuit design learning and reference.
    """
    if not RESOURCES_DIR.exists():
        return "# No Resources Found\n\nThe resources directory does not exist."
    
    python_files = []
    pdf_files = []
    
    for file_path in RESOURCES_DIR.glob("*"):
        if file_path.is_file():
            if file_path.suffix.lower() == ".py" and file_path.name != "__init__.py":
                python_files.append(file_path.name)
            elif file_path.suffix.lower() == ".pdf":
                pdf_files.append(file_path.name)
    
    content = "# Available Resources\n\n"
    
    if python_files:
        content += "## 🐍 Python Examples\n"
        content += "These examples demonstrate quantum circuit design patterns:\n\n"
        for filename in sorted(python_files):
            content += f"- **{filename}** - Use @examples://{filename} to view code\n"
        content += "\n"
    
    if pdf_files:
        content += "## 📄 Research Papers & Documentation\n"
        content += "Academic papers and technical documentation:\n\n"
        for filename in sorted(pdf_files):
            title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            content += f"- **{title}** - Use @pdfs://{filename} to access\n"
        content += "\n"
    
    # Add PNG visualizations
    current_dir = Path(os.getcwd())
    png_files = []
    visualization_patterns = [
        "*visualization*.png",
        "*_chip*.png", 
        "*quantum*.png",
        "*qubit*.png",
        "*circuit*.png"
    ]
    
    # Find PNG files matching visualization patterns
    for pattern in visualization_patterns:
        for file_path in current_dir.glob(pattern):
            if file_path.is_file() and file_path.name not in png_files:
                png_files.append(file_path.name)
    
    # Also check for PNG files with corresponding GDS files
    for file_path in current_dir.glob("*.png"):
        if file_path.is_file() and file_path.name not in png_files:
            gds_name = file_path.stem + ".gds"
            if (current_dir / gds_name).exists():
                png_files.append(file_path.name)
    
    if png_files:
        content += "## 🖼️ PNG Visualizations\n"
        content += "Quantum circuit visualization images:\n\n"
        for filename in sorted(png_files):
            title = filename.replace('.png', '').replace('_', ' ').replace('-', ' ').title()
            content += f"- **{title}** - Use @png://{filename} to access\n"
        content += "\n"
    
    if not python_files and not pdf_files and not png_files:
        return "# No Resources Found\n\nNo Python files, PDFs, or PNG visualizations found."
    
    content += "## Usage\n"
    content += "- Use `@resources://list` to see this comprehensive list\n"
    content += "- Use `@examples://list` to see only Python examples\n"
    content += "- Use `@pdfs://list` to see only PDF documents\n"
    content += "- Use `@png://list` to see only PNG visualizations\n"
    content += "- Use `@examples://{filename}` to view Python source code\n"
    content += "- Use `@pdfs://{filename}` to get PDF information\n"
    content += "- Use `@png://{filename}` to get PNG visualization details\n"
    content += "- Use tools `run_python_example`, `extract_pdf_text`, and `export_gds_to_png` to work with files\n"
    
    return content

# === Resource 2: List Python Examples ===
@mcp.resource("examples://list")
def get_python_examples() -> str:
    """
    List all available Python examples in the resources directory.
    
    This resource provides a list of all Python example files that can be run
    to demonstrate quantum circuit design patterns and techniques.
    """
    if not RESOURCES_DIR.exists():
        return "# No Examples Found\n\nThe resources directory does not exist."
    
    python_files = []
    for file_path in RESOURCES_DIR.glob("*.py"):
        if file_path.name != "__init__.py":
            python_files.append(file_path.name)
    
    if not python_files:
        return "# No Python Examples Found\n\nNo Python files found in the resources directory."
    
    content = "# Available Python Examples\n\n"
    content += "These examples demonstrate various quantum circuit design patterns:\n\n"
    
    for filename in sorted(python_files):
        content += f"- **{filename}** - Use @examples://{filename} to view the code\n"
    
    content += "\n## Usage\n"
    content += "- Use `@examples://list` to see this list\n"
    content += "- Use `@examples://{filename}` to view a specific example's source code\n"
    content += "- Use the `run_python_example` tool to execute an example\n"
    
    return content

# === Resource 3: List PDF Documents ===
@mcp.resource("pdfs://list")
def get_pdf_documents() -> str:
    """
    List all available PDF documents in the resources directory.
    
    This resource provides a list of all PDF files containing research papers,
    technical documentation, and reference materials for quantum circuit design.
    """
    if not RESOURCES_DIR.exists():
        return "# No PDFs Found\n\nThe resources directory does not exist."
    
    pdf_files = []
    for file_path in RESOURCES_DIR.glob("*.pdf"):
        pdf_files.append(file_path.name)
    
    if not pdf_files:
        return "# No PDF Documents Found\n\nNo PDF files found in the resources directory."
    
    content = "# Available PDF Documents\n\n"
    content += "Research papers and technical documentation for quantum circuit design:\n\n"
    
    for filename in sorted(pdf_files):
        # Create a readable title from filename
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        content += f"- **{title}**\n"
        content += f"  - File: `{filename}`\n"
        content += f"  - Access: Use @pdfs://{filename} to get info\n"
        content += f"  - Extract: Use `extract_pdf_text` tool with filename='{filename}'\n\n"
    
    content += "## Usage\n"
    content += "- Use `@pdfs://list` to see this list\n"
    content += "- Use `@pdfs://{filename}` to get PDF metadata and information\n"
    content += "- Use the `extract_pdf_text` tool to extract readable content\n"
    
    return content

# === Resource 4: Get PDF Information ===
@mcp.resource("pdfs://{filename}")
def get_pdf_info(filename: str) -> str:
    """
    Get information about a specific PDF document.
    
    Args:
        filename: The name of the PDF file to get info about (e.g., 'CircuitQuantumElectrodynamics.pdf')
    """
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    file_path = RESOURCES_DIR / filename
    
    if not file_path.exists():
        return f"# PDF Not Found: {filename}\n\nThe file '{filename}' does not exist in the resources directory.\n\nUse @pdfs://list to see available PDFs."
    
    try:
        # Get basic file information
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Create readable title from filename
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        content = f"# PDF Document: {title}\n\n"
        content += f"**Filename:** `{filename}`\n"
        content += f"**File Path:** `{file_path}`\n"
        content += f"**File Size:** {file_size_mb:.2f} MB ({file_size:,} bytes)\n\n"
        
        # Try to extract basic PDF metadata if possible
        try:
            import PyPDF2
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                
                content += f"**Pages:** {num_pages}\n"
                
                # Try to get metadata
                if pdf_reader.metadata:
                    metadata = pdf_reader.metadata
                    if metadata.title:
                        content += f"**Title:** {metadata.title}\n"
                    if metadata.author:
                        content += f"**Author:** {metadata.author}\n"
                    if metadata.subject:
                        content += f"**Subject:** {metadata.subject}\n"
                    if metadata.creator:
                        content += f"**Creator:** {metadata.creator}\n"
                
        except ImportError:
            content += "**Note:** PyPDF2 not available for detailed PDF analysis\n"
        except Exception as e:
            content += f"**Note:** Could not read PDF metadata: {str(e)}\n"
        
        content += "\n## Usage\n"
        content += f"- Use `extract_pdf_text(filename='{filename}')` to extract readable text\n"
        content += f"- Use `extract_pdf_text(filename='{filename}', pages='1-3')` to extract specific pages\n"
        content += "- This document contains technical information about quantum circuit design\n"
        
        return content
        
    except Exception as e:
        return f"# Error Reading PDF Info: {filename}\n\nFailed to get file information: {str(e)}"

# === Resource 5: Get Python Example Content ===
@mcp.resource("examples://{filename}")
def get_python_example_content(filename: str) -> str:
    """
    Get the source code content of a specific Python example.
    
    Args:
        filename: The name of the Python file to retrieve (e.g., 'demo.py')
    """
    if not filename.endswith('.py'):
        filename += '.py'
    
    file_path = RESOURCES_DIR / filename
    
    if not file_path.exists():
        return f"# Example Not Found: {filename}\n\nThe file '{filename}' does not exist in the resources directory.\n\nUse @examples://list to see available examples."
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        content = f"# Source Code: {filename}\n\n"
        content += f"**File Path:** `{file_path}`\n\n"
        content += "## Source Code\n\n"
        content += f"```python\n{source_code}\n```\n\n"
        content += "## Usage\n"
        content += f"Use the `run_python_example` tool with filename='{filename}' to execute this example.\n"
        
        return content
    except Exception as e:
        return f"# Error Reading {filename}\n\nFailed to read the file: {str(e)}"

# === Resource 6: List PNG Visualizations ===
@mcp.resource("png://list")
def get_png_visualizations() -> str:
    """
    List all available PNG visualization files created by GDS export functions.
    
    This resource provides a list of all PNG files in the current working directory
    that appear to be quantum circuit visualizations created by the export_gds_to_png function.
    """
    current_dir = Path(os.getcwd())
    
    png_files = []
    visualization_patterns = [
        "*visualization*.png",
        "*_chip*.png", 
        "*quantum*.png",
        "*qubit*.png",
        "*circuit*.png"
    ]
    
    # Find PNG files matching visualization patterns
    for pattern in visualization_patterns:
        for file_path in current_dir.glob(pattern):
            if file_path.is_file() and file_path.name not in png_files:
                png_files.append(file_path.name)
    
    # Also check for any PNG files that might be GDS exports
    for file_path in current_dir.glob("*.png"):
        if file_path.is_file() and file_path.name not in png_files:
            # Check if there's a corresponding GDS file
            gds_name = file_path.stem + ".gds"
            if (current_dir / gds_name).exists():
                png_files.append(file_path.name)
    
    if not png_files:
        return "# No PNG Visualizations Found\n\nNo PNG visualization files found in the current working directory.\n\nUse the `export_gds_to_png` tool to create visualizations from GDS files."
    
    content = "# Available PNG Visualizations\n\n"
    content += "PNG visualization files created by quantum circuit design tools:\n\n"
    
    for filename in sorted(png_files):
        file_path = current_dir / filename
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Create a readable title from filename
        title = filename.replace('.png', '').replace('_', ' ').replace('-', ' ').title()
        
        content += f"- **{title}**\n"
        content += f"  - File: `{filename}`\n"
        content += f"  - Size: {file_size_mb:.2f} MB\n"
        content += f"  - Access: Use @png://{filename} to get detailed info\n\n"
    
    content += "## Usage\n"
    content += "- Use `@png://list` to see this list\n"
    content += "- Use `@png://{filename}` to get detailed PNG information\n"
    content += "- These PNG files can be opened with any image viewer\n"
    content += "- Use the `export_gds_to_png` tool to create new visualizations\n"
    
    return content

# === Resource 7: Get PNG Visualization Information ===
@mcp.resource("png://{filename}")
def get_png_info(filename: str) -> str:
    """
    Get detailed information about a specific PNG visualization file.
    
    Args:
        filename: The name of the PNG file to get info about (e.g., 'quantum_circuit_visualization.png')
    """
    if not filename.endswith('.png'):
        filename += '.png'
    
    current_dir = Path(os.getcwd())
    file_path = current_dir / filename
    
    if not file_path.exists():
        available_files = [f.name for f in current_dir.glob("*.png")]
        return f"# PNG Not Found: {filename}\n\nThe file '{filename}' does not exist in the current working directory.\n\nAvailable PNG files: {', '.join(available_files) if available_files else 'None'}\n\nUse @png://list to see available visualizations."
    
    try:
        # Get basic file information
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        file_mtime = file_path.stat().st_mtime
        
        import datetime
        modification_time = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create readable title from filename
        title = filename.replace('.png', '').replace('_', ' ').replace('-', ' ').title()
        
        content = f"# PNG Visualization: {title}\n\n"
        content += f"**Filename:** `{filename}`\n"
        content += f"**File Path:** `{file_path}`\n"
        content += f"**File Size:** {file_size_mb:.2f} MB ({file_size:,} bytes)\n"
        content += f"**Last Modified:** {modification_time}\n\n"
        
        # Try to get image dimensions if PIL/Pillow is available
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
                content += f"**Image Dimensions:** {width} x {height} pixels\n"
                content += f"**Color Mode:** {mode}\n"
                
                # Calculate DPI if available
                if hasattr(img, 'info') and 'dpi' in img.info:
                    dpi = img.info['dpi']
                    content += f"**DPI:** {dpi[0]} x {dpi[1]}\n"
                    
        except ImportError:
            content += "**Note:** PIL/Pillow not available for detailed image analysis\n"
        except Exception as e:
            content += f"**Note:** Could not read image metadata: {str(e)}\n"
        
        # Check if there's a corresponding GDS file
        gds_name = filename.replace('.png', '.gds')
        gds_path = current_dir / gds_name
        if gds_path.exists():
            gds_size = gds_path.stat().st_size
            gds_size_mb = gds_size / (1024 * 1024)
            content += f"\n**Source GDS File:** `{gds_name}` ({gds_size_mb:.2f} MB)\n"
        
        # Detect visualization type based on filename patterns
        visualization_type = "Unknown"
        if "quantum" in filename.lower():
            visualization_type = "Quantum Circuit"
        elif "qubit" in filename.lower():
            visualization_type = "Qubit Design"
        elif "chip" in filename.lower():
            visualization_type = "Chip Layout"
        elif "circuit" in filename.lower():
            visualization_type = "Circuit Design"
        elif "visualization" in filename.lower():
            visualization_type = "GDS Visualization"
            
        content += f"**Visualization Type:** {visualization_type}\n"
        
        content += "\n## Usage\n"
        content += f"- Open `{filename}` with any image viewer or web browser\n"
        content += f"- Use in presentations, documentation, or reports\n"
        content += f"- High-resolution suitable for printing and publications\n"
        
        if gds_path.exists():
            content += f"- Regenerate with `export_gds_to_png(gds_file_path='{gds_name}', png_output_path='{filename}')`\n"
        
        content += "\n## Technical Details\n"
        content += "- Created by Qiskit Metal MCP Server GDS to PNG export function\n"
        content += "- Vector-based rendering with matplotlib backend\n"
        content += "- Layer-specific color coding for quantum circuit components\n"
        
        return content
        
    except Exception as e:
        return f"# Error Reading PNG Info: {filename}\n\nFailed to get file information: {str(e)}"

# === Tool 14: Run Python Example ===
@mcp.tool()
def run_python_example(filename: str) -> str:
    """Execute a Python example from the resources directory.
    
    This tool allows you to run quantum circuit design examples that demonstrate
    various patterns and techniques. The examples are executed in a controlled
    environment and their output is captured for analysis.
    
    Args:
        filename: Name of the Python file to execute (e.g., 'demo.py')
    
    Returns:
        Success message with execution output or error details if execution fails.
        
    Prerequisites:
        - The specified Python file must exist in the resources directory
        - Required dependencies must be installed
        
    Note:
        Examples are executed in the same environment as the MCP server.
        Some examples may require additional setup or dependencies.
    """
    if not filename.endswith('.py'):
        filename += '.py'
    
    file_path = RESOURCES_DIR / filename
    
    if not file_path.exists():
        available_files = [f.name for f in RESOURCES_DIR.glob("*.py") if f.name != "__init__.py"]
        return f"❌ File '{filename}' not found in resources directory.\n\nAvailable files: {', '.join(available_files)}"
    
    try:
        # Execute the Python file and capture output
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, str(file_path)],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            cwd=str(RESOURCES_DIR)
        )
        
        success_msg = f"✓ Successfully executed {filename}"
        
        if result.stdout:
            success_msg += f"\n\n📄 Output:\n{result.stdout}"
        
        if result.stderr:
            success_msg += f"\n\n⚠️ Warnings/Errors:\n{result.stderr}"
        
        if result.returncode != 0:
            success_msg += f"\n\n❌ Process exited with code: {result.returncode}"
        
        return success_msg
        
    except subprocess.TimeoutExpired:
        return f"❌ Timeout: {filename} took longer than 30 seconds to execute."
    except Exception as e:
        return f"❌ Error executing {filename}: {str(e)}"

# === Tool 15: Extract PDF Text ===
@mcp.tool()
def extract_pdf_text(filename: str, pages: str = "all", max_chars: int = 10000) -> str:
    """Extract text content from a PDF document in the resources directory.
    
    This tool extracts readable text from PDF research papers and technical documents,
    making their content accessible for analysis and reference. Supports full document
    extraction or specific page ranges.
    
    Args:
        filename: Name of the PDF file to extract text from (e.g., 'CircuitQuantumElectrodynamics.pdf')
        pages: Page specification - 'all' for entire document, '1-3' for range, '1,3,5' for specific pages (default: 'all')
        max_chars: Maximum characters to return to prevent overwhelming output (default: 10000)
    
    Returns:
        Extracted text content with metadata, or error message if extraction fails.
        
    Prerequisites:
        - The specified PDF file must exist in the resources directory
        - PyPDF2 or similar PDF library should be installed for best results
        
    Note:
        Text extraction quality depends on the PDF format. Scanned documents
        (images) may not extract well without OCR capabilities.
    """
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    file_path = RESOURCES_DIR / filename
    
    if not file_path.exists():
        available_files = [f.name for f in RESOURCES_DIR.glob("*.pdf")]
        return f"❌ PDF '{filename}' not found in resources directory.\n\nAvailable PDFs: {', '.join(available_files)}"
    
    try:
        # Try PyPDF2 first (most common)
        try:
            import PyPDF2
            return _extract_with_pypdf2(file_path, filename, pages, max_chars)
        except ImportError:
            pass
        
        # Try pdfplumber as alternative
        try:
            import pdfplumber
            return _extract_with_pdfplumber(file_path, filename, pages, max_chars)
        except ImportError:
            pass
        
        # Try pymupdf as another alternative
        try:
            import fitz  # PyMuPDF
            return _extract_with_pymupdf(file_path, filename, pages, max_chars)
        except ImportError:
            pass
        
        # If no PDF libraries available, return helpful message
        return f"""❌ No PDF extraction libraries available.

To enable PDF text extraction, install one of:
• PyPDF2: pip install PyPDF2
• pdfplumber: pip install pdfplumber  
• PyMuPDF: pip install PyMuPDF

File Information:
• File: {filename}
• Path: {file_path}
• Size: {file_path.stat().st_size / (1024*1024):.2f} MB

Use @pdfs://{filename} to get PDF metadata without text extraction."""
        
    except Exception as e:
        return f"❌ Error extracting text from {filename}: {str(e)}"

def _extract_with_pypdf2(file_path, filename, pages, max_chars):
    """Extract text using PyPDF2 library."""
    import PyPDF2
    
    with open(file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        
        # Parse page specification
        page_nums = _parse_page_spec(pages, total_pages)
        
        extracted_text = ""
        for page_num in page_nums:
            if 0 <= page_num < total_pages:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        return _format_extraction_result(filename, extracted_text, page_nums, total_pages, max_chars, "PyPDF2")

def _extract_with_pdfplumber(file_path, filename, pages, max_chars):
    """Extract text using pdfplumber library."""
    import pdfplumber
    
    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        page_nums = _parse_page_spec(pages, total_pages)
        
        extracted_text = ""
        for page_num in page_nums:
            if 0 <= page_num < total_pages:
                page = pdf.pages[page_num]
                page_text = page.extract_text() or ""
                extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        return _format_extraction_result(filename, extracted_text, page_nums, total_pages, max_chars, "pdfplumber")

def _extract_with_pymupdf(file_path, filename, pages, max_chars):
    """Extract text using PyMuPDF library."""
    import fitz
    
    pdf_doc = fitz.open(file_path)
    total_pages = pdf_doc.page_count
    page_nums = _parse_page_spec(pages, total_pages)
    
    extracted_text = ""
    for page_num in page_nums:
        if 0 <= page_num < total_pages:
            page = pdf_doc[page_num]
            page_text = page.get_text()
            extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
    
    pdf_doc.close()
    return _format_extraction_result(filename, extracted_text, page_nums, total_pages, max_chars, "PyMuPDF")

def _parse_page_spec(pages, total_pages):
    """Parse page specification into list of page numbers (0-indexed)."""
    if pages.lower() == "all":
        return list(range(total_pages))
    
    page_nums = []
    
    # Handle comma-separated values and ranges
    for part in pages.split(','):
        part = part.strip()
        if '-' in part:
            # Handle range like "1-3"
            start, end = part.split('-')
            start_page = max(0, int(start.strip()) - 1)  # Convert to 0-indexed
            end_page = min(total_pages - 1, int(end.strip()) - 1)
            page_nums.extend(range(start_page, end_page + 1))
        else:
            # Handle single page
            page_num = max(0, min(total_pages - 1, int(part) - 1))  # Convert to 0-indexed
            page_nums.append(page_num)
    
    return sorted(list(set(page_nums)))  # Remove duplicates and sort

def _format_extraction_result(filename, extracted_text, page_nums, total_pages, max_chars, method):
    """Format the final extraction result."""
    # Truncate if too long
    if len(extracted_text) > max_chars:
        extracted_text = extracted_text[:max_chars] + f"\n\n... [TRUNCATED - showing first {max_chars} characters]"
    
    pages_extracted = [p + 1 for p in page_nums]  # Convert back to 1-indexed for display
    
    result = f"""✓ Successfully extracted text from {filename}

📄 **File Information:**
• Total Pages: {total_pages}
• Pages Extracted: {pages_extracted}
• Extraction Method: {method}
• Text Length: {len(extracted_text):,} characters

📝 **Extracted Content:**
{extracted_text}

💡 **Usage Tips:**
• Use pages='1-5' to extract specific page ranges
• Use max_chars parameter to control output length
• Text quality depends on PDF format (best with text-based PDFs)
"""
    
    return result

# === Prompt: Generate Example Execution Prompt ===
@mcp.prompt()
def run_example_prompt(filename: str, analyze_output: bool = True) -> str:
    """Generate a prompt for executing and analyzing a Python quantum circuit example."""
    return f"""Execute and analyze the quantum circuit example '{filename}' using the available tools. Follow these instructions:

1. First, use the run_python_example tool to execute the file:
   - Call run_python_example(filename='{filename}')
   - Review the execution output for any errors or warnings

2. If you want to examine the source code, use the resource:
   - Access @examples://{filename} to view the source code
   - Understand the quantum circuit design patterns being demonstrated

3. {"Provide a comprehensive analysis that includes:" if analyze_output else "Provide a summary that includes:"}
   - Overview of what the example demonstrates
   - Key quantum circuit components used (qubits, resonators, couplers, etc.)
   - Design patterns and techniques shown
   - Any notable features or innovations
   {"- Analysis of the execution output and results" if analyze_output else ""}
   {"- Potential modifications or extensions to the design" if analyze_output else ""}

4. Format your response with clear headings and bullet points for easy readability.

Execute the example '{filename}' and provide {"detailed analysis" if analyze_output else "a summary"} of the quantum circuit design it demonstrates."""

# === Prompt: Analyze PDF Document ===
@mcp.prompt()
def analyze_pdf_prompt(filename: str, focus_area: str = "general", max_pages: int = 10) -> str:
    """Generate a prompt for analyzing a PDF research document."""
    return f"""Analyze the research document '{filename}' focusing on {focus_area} aspects. Follow these instructions:

1. First, get basic information about the PDF:
   - Use @pdfs://{filename} to view document metadata and information
   - Review the document structure, page count, and basic details

2. Extract and analyze the content:
   - Use extract_pdf_text(filename='{filename}', pages='1-{max_pages}') to get the main content
   - Focus on the first {max_pages} pages which typically contain key information

3. Provide a comprehensive analysis that includes:
   - **Document Overview**: Title, authors, publication context, and main topic
   - **Key Concepts**: Primary quantum circuit design concepts discussed
   - **Technical Contributions**: Novel techniques, methodologies, or innovations presented
   - **Relevance to Quantum Computing**: How this relates to practical quantum circuit design
   - **Important Equations/Formulas**: Any significant mathematical relationships (if extractable)
   - **Experimental Results**: Key findings or performance metrics mentioned
   - **Applications**: Practical applications or use cases for the techniques described

4. For specific focus areas:
   - **"couplers"**: Focus on qubit coupling mechanisms and techniques
   - **"qubits"**: Emphasize qubit design, fabrication, and characterization
   - **"circuits"**: Highlight overall circuit architecture and design patterns
   - **"fabrication"**: Focus on manufacturing processes and techniques
   - **"theory"**: Emphasize theoretical foundations and mathematical models
   - **"general"**: Provide balanced coverage of all aspects

5. Conclude with:
   - **Key Takeaways**: 3-5 most important points from the document
   - **Relevance to Practice**: How this knowledge applies to quantum circuit design
   - **Further Reading**: Suggestions for related topics or follow-up research

Format your response with clear headings and bullet points for easy readability.

Analyze the document '{filename}' with focus on {focus_area} aspects and provide insights relevant to quantum circuit design."""

if __name__ == "__main__":
    print("🚀 Starting Qiskit Metal FastMCP Server...")
    print(f"📊 Qiskit Metal Available: {QISKIT_METAL_AVAILABLE}")
    mcp.run()
