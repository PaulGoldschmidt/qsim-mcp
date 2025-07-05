#!/usr/bin/env python3

# === Octave-based OpenEMS MCP Server ===
# Electromagnetic field simulation server using Octave scripts
# Provides tools for quantum circuit EM analysis through Octave/OpenEMS

import os
import json
import numpy as np
import subprocess
import tempfile
import shutil
from pathlib import Path
from fastmcp import FastMCP
import time
import re
from typing import Optional

# Initialize FastMCP
mcp = FastMCP("Octave OpenEMS MCP Server")

# Global simulation context
current_simulation = None
simulation_results = {}
octave_available = False

def check_octave_installation():
    """Check if Octave is available on the system"""
    global octave_available
    try:
        result = subprocess.run(['octave', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            octave_available = True
            return True, result.stdout.split('\n')[0]
        else:
            octave_available = False
            return False, "Octave command failed"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        octave_available = False
        return False, "Octave not found in PATH"

def execute_octave_script(script_path, working_dir=None):
    """Execute an Octave script and return the results"""
    if not octave_available:
        return False, "", "Octave not available"
    
    try:
        if working_dir is None:
            working_dir = os.path.dirname(script_path)
        
        # Execute the Octave script
        cmd = ['octave', '--no-gui', '--eval', f'run("{script_path}")']
        result = subprocess.run(cmd, cwd=working_dir, 
                              capture_output=True, text=True, timeout=300)
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "", "Script execution timed out (5 min limit)"
    except Exception as e:
        return False, "", f"Execution error: {str(e)}"

# Check Octave availability at startup
octave_status, octave_info = check_octave_installation()
print(f"🔧 Octave Status: {'Available' if octave_status else 'Not Available'}")
if octave_status:
    print(f"📋 {octave_info}")

# === Tool 1: Check Octave OpenEMS Status ===
@mcp.tool()
def check_octave_openems_status() -> str:
    """Check Octave and OpenEMS installation status.
    
    Verifies Octave installation, OpenEMS availability, and system readiness for
    electromagnetic simulations using Octave scripts.
    
    Returns:
        Detailed status report including installation status and capabilities.
    """
    global octave_available, current_simulation, simulation_results
    
    status_report = """
Octave OpenEMS MCP Server Status Report
=======================================

"""
    
    # Check Octave availability
    octave_status, octave_info = check_octave_installation()
    if octave_status:
        status_report += f"✓ Octave: {octave_info}\n"
    else:
        status_report += f"❌ Octave: {octave_info}\n"
    
    # Check OpenEMS executable
    openems_exe = shutil.which("openEMS")
    if openems_exe:
        status_report += f"✓ OpenEMS Executable: {openems_exe}\n"
    else:
        status_report += "❌ OpenEMS Executable: Not Found in PATH\n"
    
    # Check AppCSXCAD viewer
    appcsxcad_exe = shutil.which("AppCSXCAD")
    if appcsxcad_exe:
        status_report += f"✓ AppCSXCAD Viewer: {appcsxcad_exe}\n"
    else:
        status_report += "❌ AppCSXCAD Viewer: Not Found in PATH\n"
    
    # Simulation status
    status_report += f"\nSimulation Context:\n"
    status_report += f"• Active Simulation: {'Yes' if current_simulation else 'No'}\n"
    status_report += f"• Cached Results: {len(simulation_results)} simulations\n"
    
    # System readiness
    if octave_status and openems_exe:
        status_report += "\n✓ System Ready: Octave + OpenEMS available\n"
    else:
        status_report += "\n❌ System Not Ready: Missing dependencies\n"
    
    # Installation help
    if not octave_status or not openems_exe:
        status_report += """

Installation Instructions:
=========================
For Ubuntu/Debian:
1. sudo apt update
2. sudo apt install octave openems
3. Test: octave --version && openEMS

For other systems:
• Octave: https://www.gnu.org/software/octave/download.html
• OpenEMS: https://openems.de/index.php/Install

Note: This server generates and executes Octave scripts for OpenEMS
"""
    
    return status_report

# === Tool 2: Create CPW Octave Simulation ===
@mcp.tool()
def create_cpw_octave_simulation(name: str = "cpw_octave_sim",
                                width: float = 10.0, gap: float = 6.0,
                                substrate_height: float = 500.0, 
                                substrate_width: float = 5000.0,
                                substrate_er: float = 11.9, 
                                length: float = 1000.0,
                                frequency_start: float = 1e9, 
                                frequency_stop: float = 20e9, 
                                frequency_points: int = 201,
                                output_dir: str = "./octave_simulations") -> str:
    """Create a CPW transmission line simulation using Octave scripts.
    
    Generates and stores an Octave script for CPW electromagnetic simulation.
    The script includes geometry setup, meshing, excitation, and post-processing.
    
    Args:
        name: Simulation name for identification
        width: CPW center conductor width in micrometers
        gap: CPW gap width in micrometers
        substrate_height: Substrate thickness in micrometers
        substrate_width: Substrate width in micrometers
        substrate_er: Relative permittivity of substrate
        length: CPW length in micrometers
        frequency_start: Start frequency in Hz
        frequency_stop: Stop frequency in Hz
        frequency_points: Number of frequency points
        output_dir: Directory to store scripts and results
    
    Returns:
        Success message with script details or error if creation fails.
    """
    global current_simulation
    
    if not octave_available:
        return "❌ Error: Octave not available. Please install Octave."
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        script_path = os.path.join(output_dir, f"{name}.m")
        
        # Generate comprehensive Octave script
        octave_script = f"""
%% CPW Transmission Line Simulation
%% Generated by Octave OpenEMS MCP Server
%% Simulation: {name}
%% Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

close all;
clear;
clc;

%% Add OpenEMS to path (adjust if needed)
addpath('/usr/share/openEMS/matlab');
addpath('/usr/share/CSXCAD/matlab');

%% Physical constants and setup
physical_constants;
unit = 1e-6; % micrometers

%% Design Parameters
CPW_length = {length};
CPW_port_length = 10000; % um
CPW_width = {width};
CPW_gap = {gap};
substrate_thickness = {substrate_height};
substrate_width = {substrate_width};
substrate_epr = {substrate_er};
f_max = {frequency_stop};
air_spacing = 7000; % um

%% Simulation Parameters
feed_R = 50;
pml_add_cells = [8, 8, 8, 8, 8, 8];
feed_shift_cells = 0;
resolution = 40; % mesh resolution in um

%% Initialize FDTD
FDTD = InitFDTD('EndCriteria', 1e-4);
FDTD = SetGaussExcite(FDTD, f_max/2, f_max/2);
BC = [2 2 2 2 2 2]; % PMC boundaries for CPW
FDTD = SetBoundaryCond(FDTD, BC);

%% Initialize CSX (geometry)
CSX = InitCSX();

%% Define mesh
mesh.x = SmoothMeshLines([0 CPW_length/2 CPW_length/2+air_spacing], resolution, 1.5, 0);
mesh.x = unique(sort([-mesh.x mesh.x]));

edge_res = 40;
mesh.y = SmoothMeshLines([CPW_width/2+[-edge_res/3 +edge_res/3*2] CPW_gap+CPW_width/2+[-edge_res/3*2 +edge_res/3]], edge_res, 1.5, 0);
mesh.y = SmoothMeshLines([0 mesh.y], edge_res*2, 1.3, 0);
mesh.y = SmoothMeshLines([0 mesh.y substrate_width/2 substrate_width/2+air_spacing], resolution, 1.3, 0);
mesh.y = unique(sort([-mesh.y mesh.y]));

mesh.z = SmoothMeshLines([-air_spacing linspace(0,substrate_thickness,5) substrate_thickness+air_spacing], resolution);
mesh = AddPML(mesh, pml_add_cells);
CSX = DefineRectGrid(CSX, unit, mesh);

%% Define materials
% Substrate
CSX = AddMaterial(CSX, 'Substrate');
CSX = SetMaterialProperty(CSX, 'Substrate', 'Epsilon', substrate_epr);
start = [-CPW_length/2, -substrate_width/2, 0];
stop = [+CPW_length/2, +substrate_width/2, substrate_thickness];
CSX = AddBox(CSX, 'Substrate', 0, start, stop);

%% Define CPW geometry
% CPW ports
CSX = AddMetal(CSX, 'CPW_PORT');

% Port 1 (excitation)
portstart = [-CPW_length/2, -CPW_width/2, substrate_thickness];
portstop = [-CPW_length/2+CPW_port_length, CPW_width/2, substrate_thickness];
[CSX,port{{1}}] = AddCPWPort(CSX, 999, 1, 'CPW_PORT', portstart, portstop, CPW_gap, 'x', [0 1 0], ...
                             'ExcitePort', true, 'FeedShift', feed_shift_cells*resolution, ...
                             'MeasPlaneShift', CPW_port_length, 'Feed_R', feed_R);

% Port 2 (measurement)
portstart = [CPW_length/2, -CPW_width/2, substrate_thickness];
portstop = [CPW_length/2-CPW_port_length, CPW_width/2, substrate_thickness];
[CSX,port{{2}}] = AddCPWPort(CSX, 999, 2, 'CPW_PORT', portstart, portstop, CPW_gap, 'x', [0 1 0], ...
                             'MeasPlaneShift', CPW_port_length, 'Feed_R', feed_R);

% CPW center conductor
CSX = AddMetal(CSX, 'CPW');
start = [-CPW_length/2+CPW_port_length, -CPW_width/2, substrate_thickness];
stop = [+CPW_length/2-CPW_port_length, +CPW_width/2, substrate_thickness];
CSX = AddBox(CSX, 'CPW', 999, start, stop);

% Ground planes
CSX = AddMetal(CSX, 'GND');
% Left ground
start = [-CPW_length/2, -CPW_width/2-CPW_gap, substrate_thickness];
stop = [+CPW_length/2, -substrate_width/2, substrate_thickness];
CSX = AddBox(CSX, 'GND', 999, start, stop);
% Right ground
start = [-CPW_length/2, +CPW_width/2+CPW_gap, substrate_thickness];
stop = [+CPW_length/2, +substrate_width/2, substrate_thickness];
CSX = AddBox(CSX, 'GND', 999, start, stop);

%% Save geometry and run simulation
Sim_Path = '{output_dir}';
Sim_CSX = '{name}.xml';

% Remove old results
[status, message, messageid] = rmdir(Sim_Path, 's');
[status, message, messageid] = mkdir(Sim_Path);

% Write OpenEMS files
WriteOpenEMS([Sim_Path '/' Sim_CSX], FDTD, CSX);

fprintf('Starting OpenEMS simulation: {name}\\n');
fprintf('Output directory: %s\\n', Sim_Path);
fprintf('Frequency range: %.1f - %.1f GHz\\n', {frequency_start/1e9}, {frequency_stop/1e9});

% Run simulation
RunOpenEMS(Sim_Path, Sim_CSX);

%% Post-processing
fprintf('Processing results...\\n');

% Frequency vector
f = linspace({frequency_start}, {frequency_stop}, {frequency_points});

% Calculate S-parameters
port = calcPort(port, Sim_Path, f, 'RefImpedance', 50);

s11 = port{{1}}.uf.ref ./ port{{1}}.uf.inc;
s21 = port{{2}}.uf.ref ./ port{{1}}.uf.inc;
s12 = port{{1}}.uf.ref ./ port{{2}}.uf.inc;
s22 = port{{2}}.uf.ref ./ port{{2}}.uf.inc;

% Save S-parameters to text files
save('-ascii', [Sim_Path '/s11_real.txt'], 'real(s11)');
save('-ascii', [Sim_Path '/s11_imag.txt'], 'imag(s11)');
save('-ascii', [Sim_Path '/s21_real.txt'], 'real(s21)');
save('-ascii', [Sim_Path '/s21_imag.txt'], 'imag(s21)');
save('-ascii', [Sim_Path '/s12_real.txt'], 'real(s12)');
save('-ascii', [Sim_Path '/s12_imag.txt'], 'imag(s12)');
save('-ascii', [Sim_Path '/s22_real.txt'], 'real(s22)');
save('-ascii', [Sim_Path '/s22_imag.txt'], 'imag(s22)');
save('-ascii', [Sim_Path '/frequency.txt'], 'f');

% Calculate characteristic impedance
Zc = port{{1}}.uf.inc ./ port{{1}}.if.inc * feed_R;
save('-ascii', [Sim_Path '/impedance_real.txt'], 'real(Zc)');
save('-ascii', [Sim_Path '/impedance_imag.txt'], 'imag(Zc)');

% Generate plots
figure('Position', [100, 100, 1200, 800]);

% S-parameters plot
subplot(2,2,1);
plot(f/1e9, 20*log10(abs(s11)), 'b-', 'LineWidth', 2);
hold on;
plot(f/1e9, 20*log10(abs(s21)), 'r-', 'LineWidth', 2);
plot(f/1e9, 20*log10(abs(s12)), 'g--', 'LineWidth', 1.5);
plot(f/1e9, 20*log10(abs(s22)), 'm--', 'LineWidth', 1.5);
grid on;
xlabel('Frequency (GHz)');
ylabel('S-Parameters (dB)');
legend('S11', 'S21', 'S12', 'S22', 'Location', 'best');
title('S-Parameter Magnitude');

% Phase plot
subplot(2,2,2);
plot(f/1e9, angle(s11)*180/pi, 'b-', 'LineWidth', 2);
hold on;
plot(f/1e9, angle(s21)*180/pi, 'r-', 'LineWidth', 2);
grid on;
xlabel('Frequency (GHz)');
ylabel('Phase (degrees)');
legend('S11', 'S21', 'Location', 'best');
title('S-Parameter Phase');

% Characteristic impedance
subplot(2,2,3);
plot(f/1e9, real(Zc), 'k-', 'LineWidth', 2);
hold on;
plot(f/1e9, imag(Zc), 'r--', 'LineWidth', 2);
grid on;
xlabel('Frequency (GHz)');
ylabel('Impedance (Ohms)');
legend('Real(Zc)', 'Imag(Zc)', 'Location', 'best');
title('Characteristic Impedance');

% VSWR
subplot(2,2,4);
vswr = (1 + abs(s11)) ./ (1 - abs(s11));
plot(f/1e9, vswr, 'g-', 'LineWidth', 2);
grid on;
xlabel('Frequency (GHz)');
ylabel('VSWR');
title('Voltage Standing Wave Ratio');

% Save plot
saveas(gcf, [Sim_Path '/cpw_analysis.png']);
saveas(gcf, [Sim_Path '/cpw_analysis.fig']);

fprintf('Simulation completed successfully!\\n');
fprintf('Results saved to: %s\\n', Sim_Path);

%% Save summary data
summary.name = '{name}';
summary.type = 'CPW';
summary.parameters.width = {width};
summary.parameters.gap = {gap};
summary.parameters.length = {length};
summary.parameters.substrate_er = {substrate_er};
summary.parameters.substrate_height = {substrate_height};
summary.frequency_range = [{frequency_start}, {frequency_stop}];
summary.frequency_points = {frequency_points};

save([Sim_Path '/simulation_summary.mat'], 'summary');

fprintf('Summary:\\n');
fprintf('  CPW Width: %.1f um\\n', {width});
fprintf('  CPW Gap: %.1f um\\n', {gap});
fprintf('  Length: %.1f um\\n', {length});
fprintf('  Substrate εᵣ: %.1f\\n', {substrate_er});
fprintf('  Avg |S11|: %.2f dB\\n', mean(20*log10(abs(s11))));
fprintf('  Avg |S21|: %.2f dB\\n', mean(20*log10(abs(s21))));
fprintf('  Avg Zc: %.1f Ohms\\n', mean(real(Zc)));
"""

        # Write the script to file
        with open(script_path, 'w') as f:
            f.write(octave_script)
        
        # Store simulation context
        current_simulation = {
            'name': name,
            'type': 'CPW_Octave',
            'script_path': script_path,
            'output_dir': output_dir,
            'parameters': {
                'width': width,
                'gap': gap,
                'substrate_height': substrate_height,
                'substrate_width': substrate_width,
                'substrate_er': substrate_er,
                'length': length,
                'frequency_range': [frequency_start, frequency_stop],
                'frequency_points': frequency_points
            }
        }
        
        return f"""
✓ CPW Octave Simulation Created: {name}
======================================

Script Generated: {script_path}
Output Directory: {output_dir}

CPW Parameters:
• Center Conductor Width: {width} μm
• Gap Width: {gap} μm
• Substrate Height: {substrate_height} μm
• Substrate Width: {substrate_width} μm
• Substrate εᵣ: {substrate_er}
• Length: {length} μm

Simulation Settings:
• Frequency Range: {frequency_start/1e9:.1f} - {frequency_stop/1e9:.1f} GHz
• Frequency Points: {frequency_points}
• Reference Impedance: 50Ω
• Mesh Resolution: 40 μm

Generated Files:
• {name}.m - Main Octave script
• Ready for execution with run_octave_simulation()

Status: Ready for simulation
Next: Use run_octave_simulation() to execute
"""
        
    except Exception as e:
        return f"❌ Error creating CPW Octave simulation: {str(e)}" 

# === Tool 3: Run Octave Simulation ===
@mcp.tool()
def run_octave_simulation(simulation_name: Optional[str] = None) -> str:
    """Execute the current Octave simulation script.
    
    Runs the generated Octave script for electromagnetic simulation and 
    processes the results. Handles script execution, result parsing, and
    error reporting.
    
    Args:
        simulation_name: Name of simulation to run (uses current if None)
    
    Returns:
        Success message with execution results or error if execution fails.
    """
    global current_simulation, simulation_results
    
    if not octave_available:
        return "❌ Error: Octave not available. Please install Octave."
    
    # Determine which simulation to run
    sim_to_run = None
    if simulation_name is None:
        if current_simulation is None:
            return "❌ No simulation specified or active."
        sim_to_run = current_simulation
    else:
        # Look for simulation in results
        if simulation_name in simulation_results:
            sim_to_run = simulation_results[simulation_name]
        else:
            return f"❌ Simulation '{simulation_name}' not found."
    
    try:
        script_path = sim_to_run['script_path']
        output_dir = sim_to_run['output_dir']
        
        # Execute the Octave script
        print(f"🚀 Executing Octave simulation: {sim_to_run['name']}")
        success, stdout, stderr = execute_octave_script(script_path, output_dir)
        
        if not success:
            return f"""
❌ Simulation Execution Failed: {sim_to_run['name']}
==================================================

Error Details:
{stderr if stderr else 'Unknown error'}

Script Path: {script_path}
Output Directory: {output_dir}

Troubleshooting:
• Check Octave installation: octave --version
• Verify OpenEMS is available: openEMS --version
• Check script permissions and paths
• Ensure sufficient disk space
"""
        
        # Parse results and store in simulation_results
        results = {
            'name': sim_to_run['name'],
            'type': sim_to_run['type'],
            'script_path': script_path,
            'output_dir': output_dir,
            'parameters': sim_to_run['parameters'],
            'completed': True,
            'execution_time': time.time(),
            'stdout': stdout,
            'stderr': stderr
        }
        
        # Try to load frequency data and S-parameters
        try:
            freq_file = os.path.join(output_dir, 'frequency.txt')
            if os.path.exists(freq_file):
                frequencies = np.loadtxt(freq_file)
                results['frequencies'] = frequencies
                
                # Load S-parameters if available
                s_files = {
                    's11': ('s11_real.txt', 's11_imag.txt'),
                    's21': ('s21_real.txt', 's21_imag.txt'),
                    's12': ('s12_real.txt', 's12_imag.txt'),
                    's22': ('s22_real.txt', 's22_imag.txt')
                }
                
                s_params = {}
                for param, (real_file, imag_file) in s_files.items():
                    real_path = os.path.join(output_dir, real_file)
                    imag_path = os.path.join(output_dir, imag_file)
                    if os.path.exists(real_path) and os.path.exists(imag_path):
                        real_data = np.loadtxt(real_path)
                        imag_data = np.loadtxt(imag_path)
                        s_params[param] = real_data + 1j * imag_data
                
                results['s_parameters'] = s_params
                
                # Load impedance if available
                imp_real = os.path.join(output_dir, 'impedance_real.txt')
                imp_imag = os.path.join(output_dir, 'impedance_imag.txt')
                if os.path.exists(imp_real) and os.path.exists(imp_imag):
                    real_imp = np.loadtxt(imp_real)
                    imag_imp = np.loadtxt(imp_imag)
                    results['impedance'] = real_imp + 1j * imag_imp
        
        except Exception as parse_error:
            results['parse_warning'] = f"Could not parse all results: {str(parse_error)}"
        
        # Store results
        simulation_results[sim_to_run['name']] = results
        
        # Generate summary
        param = sim_to_run['parameters']
        freq_range = param['frequency_range']
        
        summary = f"""
✓ Octave Simulation Completed: {sim_to_run['name']}
=================================================

Execution Details:
• Script: {script_path}
• Output Directory: {output_dir}
• Simulation Type: {sim_to_run['type']}
• Status: Successfully completed

Parameters:
• Frequency Range: {freq_range[0]/1e9:.1f} - {freq_range[1]/1e9:.1f} GHz
• CPW Width: {param['width']} μm
• CPW Gap: {param['gap']} μm
• Substrate εᵣ: {param['substrate_er']}

Generated Files:
• S-parameter data files (s11, s21, s12, s22)
• Impedance analysis
• Frequency response plots
• MATLAB summary data

Available Actions:
• extract_octave_s_parameters() - Get S-parameter analysis
• analyze_octave_impedance() - Get impedance analysis  
• plot_octave_results() - Generate additional plots
• export_octave_results() - Export to standard formats

Results stored and ready for analysis!
"""
        
        # Add performance summary if S-parameters are available
        if 's_parameters' in results and 's11' in results['s_parameters']:
            s11 = results['s_parameters']['s11']
            s21 = results['s_parameters']['s21']
            avg_s11_db = np.mean(20 * np.log10(np.abs(s11)))
            avg_s21_db = np.mean(20 * np.log10(np.abs(s21)))
            
            summary += f"""
Performance Summary:
• Average S11: {avg_s11_db:.2f} dB (return loss)
• Average S21: {avg_s21_db:.2f} dB (insertion loss)
"""
            
            if 'impedance' in results:
                avg_z = np.mean(np.real(results['impedance']))
                summary += f"• Average Impedance: {avg_z:.1f} Ω\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error running Octave simulation: {str(e)}"

# === Tool 4: Extract S-Parameters from Octave Results ===
@mcp.tool()
def extract_octave_s_parameters(simulation_name: Optional[str] = None) -> str:
    """Extract and analyze S-parameters from completed Octave simulation.
    
    Processes S-parameter data from Octave simulation results and provides
    detailed analysis including return loss, insertion loss, and matching.
    
    Args:
        simulation_name: Name of completed simulation (uses current if None)
    
    Returns:
        S-parameter analysis or error if extraction fails.
    """
    global current_simulation, simulation_results
    
    # Determine simulation to analyze
    if simulation_name is None:
        if current_simulation is None:
            return "❌ No simulation specified or active."
        simulation_name = current_simulation['name']
    
    if simulation_name not in simulation_results:
        return f"❌ Simulation '{simulation_name}' not found in results."
    
    result = simulation_results[simulation_name]
    
    if not result.get('completed', False):
        return f"❌ Simulation '{simulation_name}' not completed yet."
    
    try:
        # Check if S-parameters are available
        if 's_parameters' not in result or 'frequencies' not in result:
            return f"❌ S-parameter data not available for '{simulation_name}'"
        
        s_params = result['s_parameters']
        frequencies = result['frequencies']
        
        # Analyze S-parameters
        analysis = f"""
S-Parameter Analysis: {simulation_name}
======================================

Simulation Type: {result['type']}
Frequency Points: {len(frequencies)}
Frequency Range: {frequencies[0]/1e9:.2f} - {frequencies[-1]/1e9:.2f} GHz

"""
        
        # Analyze each S-parameter
        for param_name in ['s11', 's21', 's12', 's22']:
            if param_name in s_params:
                param_data = s_params[param_name]
                mag_db = 20 * np.log10(np.abs(param_data))
                phase_deg = np.angle(param_data) * 180 / np.pi
                
                analysis += f"""
{param_name.upper()} Analysis:
• Average Magnitude: {np.mean(mag_db):.2f} dB
• Min Magnitude: {np.min(mag_db):.2f} dB  
• Max Magnitude: {np.max(mag_db):.2f} dB
• Phase Range: {np.min(phase_deg):.1f}° to {np.max(phase_deg):.1f}°
"""
        
        # Special analysis for specific parameters
        if 's11' in s_params:
            s11 = s_params['s11']
            s11_db = 20 * np.log10(np.abs(s11))
            vswr = (1 + np.abs(s11)) / (1 - np.abs(s11))
            
            # Find frequency points with good matching (S11 < -10 dB)
            good_match_mask = s11_db < -10
            if np.any(good_match_mask):
                match_freqs = frequencies[good_match_mask]
                match_bw = (match_freqs[-1] - match_freqs[0]) / 1e9 if len(match_freqs) > 1 else 0
                
                analysis += f"""
Matching Analysis (S11):
• Best Return Loss: {np.min(s11_db):.2f} dB at {frequencies[np.argmin(s11_db)]/1e9:.2f} GHz
• Average VSWR: {np.mean(vswr):.2f}
• Min VSWR: {np.min(vswr):.2f}
• Bandwidth (S11 < -10dB): {match_bw:.2f} GHz
"""
            else:
                analysis += f"""
Matching Analysis (S11):
• Best Return Loss: {np.min(s11_db):.2f} dB at {frequencies[np.argmin(s11_db)]/1e9:.2f} GHz
• Average VSWR: {np.mean(vswr):.2f}
• Warning: No frequencies with S11 < -10 dB found
"""
        
        if 's21' in s_params:
            s21 = s_params['s21']
            s21_db = 20 * np.log10(np.abs(s21))
            
            analysis += f"""
Transmission Analysis (S21):
• Average Insertion Loss: {-np.mean(s21_db):.2f} dB
• Best Transmission: {np.max(s21_db):.2f} dB at {frequencies[np.argmax(s21_db)]/1e9:.2f} GHz
• Worst Transmission: {np.min(s21_db):.2f} dB at {frequencies[np.argmin(s21_db)]/1e9:.2f} GHz
"""
        
        # Design recommendations
        analysis += """

Design Recommendations:
======================
"""
        
        if 's11' in s_params and 's21' in s_params:
            s11_avg = np.mean(20 * np.log10(np.abs(s_params['s11'])))
            s21_avg = np.mean(20 * np.log10(np.abs(s_params['s21'])))
            
            if s11_avg > -10:
                analysis += "• Poor matching detected. Consider adjusting CPW dimensions.\n"
            elif s11_avg < -20:
                analysis += "• Excellent matching achieved.\n"
            else:
                analysis += "• Good matching achieved.\n"
            
            if s21_avg < -3:
                analysis += "• High insertion loss. Check conductor losses and substrate.\n"
            elif s21_avg > -1:
                analysis += "• Low loss transmission line.\n"
            else:
                analysis += "• Acceptable transmission loss.\n"
        
        # Data availability summary
        analysis += f"""

Available Data Files:
• Output Directory: {result['output_dir']}
• Frequency data: frequency.txt
"""
        for param in ['s11', 's21', 's12', 's22']:
            if param in s_params:
                analysis += f"• {param.upper()}: {param}_real.txt, {param}_imag.txt\n"
        
        analysis += "• Plots: cpw_analysis.png, cpw_analysis.fig\n"
        
        return analysis
        
    except Exception as e:
        return f"❌ Error extracting S-parameters: {str(e)}"

# === Tool 5: Analyze Impedance from Octave Results ===
@mcp.tool()
def analyze_octave_impedance(simulation_name: Optional[str] = None) -> str:
    """Analyze characteristic impedance from Octave simulation results.
    
    Processes impedance data and provides detailed analysis of characteristic
    impedance vs frequency, including design recommendations.
    
    Args:
        simulation_name: Name of completed simulation (uses current if None)
    
    Returns:
        Impedance analysis or error if analysis fails.
    """
    global current_simulation, simulation_results
    
    # Determine simulation to analyze
    if simulation_name is None:
        if current_simulation is None:
            return "❌ No simulation specified or active."
        simulation_name = current_simulation['name']
    
    if simulation_name not in simulation_results:
        return f"❌ Simulation '{simulation_name}' not found in results."
    
    result = simulation_results[simulation_name]
    
    if not result.get('completed', False):
        return f"❌ Simulation '{simulation_name}' not completed yet."
    
    try:
        if 'impedance' not in result or 'frequencies' not in result:
            return f"❌ Impedance data not available for '{simulation_name}'"
        
        impedance = result['impedance']
        frequencies = result['frequencies']
        
        # Analyze impedance
        real_z = np.real(impedance)
        imag_z = np.imag(impedance)
        mag_z = np.abs(impedance)
        
        analysis = f"""
Characteristic Impedance Analysis: {simulation_name}
==================================================

Frequency Range: {frequencies[0]/1e9:.2f} - {frequencies[-1]/1e9:.2f} GHz
Data Points: {len(frequencies)}

Impedance Statistics:
• Average |Z|: {np.mean(mag_z):.2f} Ω
• Min |Z|: {np.min(mag_z):.2f} Ω at {frequencies[np.argmin(mag_z)]/1e9:.2f} GHz
• Max |Z|: {np.max(mag_z):.2f} Ω at {frequencies[np.argmax(mag_z)]/1e9:.2f} GHz
• Standard Deviation: {np.std(mag_z):.2f} Ω

Real Part Analysis:
• Average Re(Z): {np.mean(real_z):.2f} Ω
• Min Re(Z): {np.min(real_z):.2f} Ω
• Max Re(Z): {np.max(real_z):.2f} Ω

Imaginary Part Analysis:
• Average Im(Z): {np.mean(imag_z):.2f} Ω
• Min Im(Z): {np.min(imag_z):.2f} Ω  
• Max Im(Z): {np.max(imag_z):.2f} Ω
"""
        
        # Target impedance analysis (assuming 50Ω target)
        target_z = 50.0
        z_error = mag_z - target_z
        z_error_percent = (z_error / target_z) * 100
        
        analysis += f"""

50Ω Target Analysis:
• Average Error: {np.mean(z_error):.2f} Ω ({np.mean(z_error_percent):.1f}%)
• Max Positive Error: {np.max(z_error):.2f} Ω ({np.max(z_error_percent):.1f}%)
• Max Negative Error: {np.min(z_error):.2f} Ω ({np.min(z_error_percent):.1f}%)
• RMS Error: {np.sqrt(np.mean(z_error**2)):.2f} Ω
"""
        
        # Frequency stability analysis
        z_variation = np.max(mag_z) - np.min(mag_z)
        z_variation_percent = (z_variation / np.mean(mag_z)) * 100
        
        analysis += f"""

Frequency Stability:
• Impedance Variation: {z_variation:.2f} Ω ({z_variation_percent:.1f}%)
"""
        
        if z_variation_percent < 5:
            analysis += "• Excellent frequency stability\n"
        elif z_variation_percent < 10:
            analysis += "• Good frequency stability\n"
        else:
            analysis += "• Poor frequency stability - consider design optimization\n"
        
        # Design recommendations
        analysis += """

Design Recommendations:
======================
"""
        
        avg_z = np.mean(mag_z)
        if avg_z < 45:
            analysis += "• Impedance too low. Increase CPW gap or reduce width.\n"
        elif avg_z > 55:
            analysis += "• Impedance too high. Decrease CPW gap or increase width.\n"
        else:
            analysis += "• Impedance close to 50Ω target. Good design.\n"
        
        if np.mean(np.abs(imag_z)) > 5:
            analysis += "• Significant reactive component. Check substrate properties.\n"
        
        if z_variation_percent > 10:
            analysis += "• High frequency dispersion. Consider substrate optimization.\n"
        
        # CPW design parameters from simulation
        if 'parameters' in result:
            params = result['parameters']
            analysis += f"""

Current Design Parameters:
• CPW Width: {params['width']} μm
• CPW Gap: {params['gap']} μm
• Substrate εᵣ: {params['substrate_er']}
• Width/Gap Ratio: {params['width']/params['gap']:.2f}

Data Files:
• impedance_real.txt - Real part vs frequency
• impedance_imag.txt - Imaginary part vs frequency
• cpw_analysis.png - Impedance plots
"""
        
        return analysis
        
    except Exception as e:
        return f"❌ Error analyzing impedance: {str(e)}"

# === Tool 6: List Octave Simulations ===
@mcp.tool()
def list_octave_simulations() -> str:
    """List all Octave-based simulations and their status.
    
    Provides overview of all Octave electromagnetic simulations that have been
    run, their types, parameters, and availability of results.
    
    Returns:
        Formatted list of all simulations with their status and details.
    """
    global current_simulation, simulation_results
    
    if not simulation_results:
        return """
No Octave Simulations Found
===========================

No Octave-based electromagnetic simulations have been completed yet.

Available Simulation Types:
• CPW Transmission Lines (create_cpw_octave_simulation)
• Resonator Analysis (coming soon)
• Custom Geometries (advanced)

Getting Started:
1. Use create_cpw_octave_simulation() to set up a CPW simulation
2. Use run_octave_simulation() to execute the simulation
3. Use extract_octave_s_parameters() to analyze results
4. Use analyze_octave_impedance() to check impedance

All simulations generate Octave scripts and execute via Octave + OpenEMS.
"""
    
    simulation_list = """
Octave OpenEMS Simulation Summary
=================================

"""
    
    for name, result in simulation_results.items():
        status = "✓ Completed" if result.get('completed', False) else "⚠ In Progress"
        
        simulation_list += f"""
Simulation: {name}
{'─' * (len(name) + 12)}
• Type: {result['type']}
• Status: {status}
• Script: {result.get('script_path', 'N/A')}
• Output Directory: {result.get('output_dir', 'N/A')}
"""
        
        if 'frequencies' in result:
            simulation_list += f"• Frequency Points: {len(result['frequencies'])}\n"
        
        if 'parameters' in result:
            params = result['parameters']
            simulation_list += "• Parameters:\n"
            for key, value in params.items():
                if isinstance(value, (int, float)):
                    if key.startswith('frequency'):
                        simulation_list += f"  - {key}: {value/1e9:.2f} GHz\n"
                    else:
                        simulation_list += f"  - {key}: {value}\n"
                elif isinstance(value, list) and len(value) == 2:
                    simulation_list += f"  - {key}: {value[0]/1e9:.1f} - {value[1]/1e9:.1f} GHz\n"
                else:
                    simulation_list += f"  - {key}: {value}\n"
        
        # Add performance summary if available
        if 's_parameters' in result and 's11' in result['s_parameters']:
            s11_avg = np.mean(20 * np.log10(np.abs(result['s_parameters']['s11'])))
            simulation_list += f"• Avg S11: {s11_avg:.1f} dB\n"
            
        if 'impedance' in result:
            z_avg = np.mean(np.abs(result['impedance']))
            simulation_list += f"• Avg Impedance: {z_avg:.1f} Ω\n"
        
        simulation_list += "\n"
    
    # Add current simulation info
    if current_simulation:
        simulation_list += f"""
Current Active Simulation:
• Name: {current_simulation['name']}
• Type: {current_simulation['type']}
• Status: Ready for execution
• Script: {current_simulation.get('script_path', 'N/A')}
"""
    
    simulation_list += f"""
Summary:
• Total Simulations: {len(simulation_results)}
• Active Simulation: {'Yes' if current_simulation else 'No'}
• Octave Status: {'Available' if octave_available else 'Not Available'}

Available Actions:
• extract_octave_s_parameters(simulation_name)
• analyze_octave_impedance(simulation_name)
• export_octave_results(simulation_name)
• clear_octave_data(simulation_name)
"""
    
    return simulation_list

# === Tool 7: Export Octave Results ===
@mcp.tool()
def export_octave_results(simulation_name: Optional[str] = None, 
                          export_format: str = "touchstone",
                          output_file: Optional[str] = None) -> str:
    """Export Octave simulation results to standard formats.
    
    Exports electromagnetic simulation results to industry-standard
    formats for use in circuit simulators and design tools.
    
    Args:
        simulation_name: Name of simulation to export (uses current if None)
        export_format: Format ("touchstone", "csv", "json", "matlab")
        output_file: Output file path (auto-generated if None)
    
    Returns:
        Success message with export information or error if export fails.
    """
    global current_simulation, simulation_results
    
    # Determine simulation to export
    if simulation_name is None:
        if current_simulation is None:
            return "❌ No simulation specified or active."
        simulation_name = current_simulation['name']
    
    if simulation_name not in simulation_results:
        return f"❌ Simulation '{simulation_name}' not found."
    
    result = simulation_results[simulation_name]
    
    if not result.get('completed', False):
        return f"❌ Simulation '{simulation_name}' not completed yet."
    
    try:
        if 's_parameters' not in result or 'frequencies' not in result:
            return f"❌ S-parameter data not available for '{simulation_name}'"
        
        freq = result['frequencies']
        s_params = result['s_parameters']
        
        # Generate output filename if not provided
        if output_file is None:
            if export_format == "touchstone":
                output_file = f"{simulation_name}.s2p"
            elif export_format == "csv":
                output_file = f"{simulation_name}.csv"
            elif export_format == "json":
                output_file = f"{simulation_name}.json"
            elif export_format == "matlab":
                output_file = f"{simulation_name}.mat"
            else:
                return f"❌ Unsupported export format: {export_format}"
        
        # Export based on format
        if export_format == "touchstone":
            # Touchstone format (.s2p)
            with open(output_file, 'w') as f:
                f.write("# Hz S MA R 50\n")
                f.write("# Octave OpenEMS Simulation Results\n")
                f.write(f"# Simulation: {simulation_name}\n")
                f.write(f"# Type: {result['type']}\n")
                f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                for i, f_hz in enumerate(freq):
                    # Get S-parameters at this frequency
                    s11 = s_params.get('s11', [0])[i] if i < len(s_params.get('s11', [])) else 0
                    s21 = s_params.get('s21', [0])[i] if i < len(s_params.get('s21', [])) else 0
                    s12 = s_params.get('s12', [0])[i] if i < len(s_params.get('s12', [])) else 0
                    s22 = s_params.get('s22', [0])[i] if i < len(s_params.get('s22', [])) else 0
                    
                    # Convert to magnitude and angle
                    s11_mag = abs(s11)
                    s11_ang = np.angle(s11) * 180 / np.pi
                    s21_mag = abs(s21)
                    s21_ang = np.angle(s21) * 180 / np.pi
                    s12_mag = abs(s12)
                    s12_ang = np.angle(s12) * 180 / np.pi
                    s22_mag = abs(s22)
                    s22_ang = np.angle(s22) * 180 / np.pi
                    
                    f.write(f"{f_hz:.6e} {s11_mag:.6f} {s11_ang:.6f} {s21_mag:.6f} {s21_ang:.6f} {s12_mag:.6f} {s12_ang:.6f} {s22_mag:.6f} {s22_ang:.6f}\n")
        
        elif export_format == "csv":
            # CSV format
            with open(output_file, 'w') as f:
                f.write("Frequency_Hz,S11_mag,S11_phase,S21_mag,S21_phase,S12_mag,S12_phase,S22_mag,S22_phase\n")
                for i, f_hz in enumerate(freq):
                    s11 = s_params.get('s11', [0])[i] if i < len(s_params.get('s11', [])) else 0
                    s21 = s_params.get('s21', [0])[i] if i < len(s_params.get('s21', [])) else 0
                    s12 = s_params.get('s12', [0])[i] if i < len(s_params.get('s12', [])) else 0
                    s22 = s_params.get('s22', [0])[i] if i < len(s_params.get('s22', [])) else 0
                    
                    f.write(f"{f_hz},{abs(s11):.6f},{np.angle(s11)*180/np.pi:.6f},{abs(s21):.6f},{np.angle(s21)*180/np.pi:.6f},{abs(s12):.6f},{np.angle(s12)*180/np.pi:.6f},{abs(s22):.6f},{np.angle(s22)*180/np.pi:.6f}\n")
        
        elif export_format == "json":
            # JSON format
            export_data = {
                "simulation_name": simulation_name,
                "simulation_type": result['type'],
                "parameters": result.get('parameters', {}),
                "frequency_hz": freq.tolist(),
                "s_parameters": {}
            }
            
            for param_name, param_data in s_params.items():
                if len(param_data) > 0:
                    export_data["s_parameters"][param_name] = {
                        "magnitude": np.abs(param_data).tolist(),
                        "phase_deg": (np.angle(param_data) * 180 / np.pi).tolist()
                    }
            
            if 'impedance' in result:
                imp_data = result['impedance']
                export_data["impedance"] = {
                    "magnitude": np.abs(imp_data).tolist(),
                    "real": np.real(imp_data).tolist(),
                    "imaginary": np.imag(imp_data).tolist()
                }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        file_size = os.path.getsize(output_file) / 1024
        
        return f"""
✓ Results Exported: {simulation_name}
====================================

Export Information:
• Format: {export_format.upper()}
• Output File: {output_file}
• Size: {file_size:.1f} KB
• Data Points: {len(freq)}

Data Contents:
• Frequency range: {freq[0]/1e9:.1f} - {freq[-1]/1e9:.1f} GHz
• S-parameters: {list(s_params.keys())}
• Source simulation: {result['type']}

Usage Guidelines:
• Touchstone (.s2p): Import into ADS, CST, HFSS, Keysight
• CSV: Import into Excel, Python, MATLAB, plotting tools
• JSON: Direct Python/JavaScript processing and web apps
• MATLAB: Use in MATLAB/Simulink for circuit analysis

File Location: {os.path.abspath(output_file)}

Note: Data extracted from Octave simulation results in {result['output_dir']}
"""
        
    except Exception as e:
        return f"❌ Error exporting results: {str(e)}"

# === Tool 8: Clear Octave Simulation Data ===
@mcp.tool()
def clear_octave_data(simulation_name: str = "all") -> str:
    """Clear Octave simulation data to free memory and reset state.
    
    Removes stored simulation results and resets the simulation context.
    Useful for freeing memory after large simulations or starting fresh.
    
    Args:
        simulation_name: Name of simulation to clear ("all" for everything)
    
    Returns:
        Success message confirming what was cleared.
    """
    global current_simulation, simulation_results
    
    if simulation_name == "all":
        # Clear everything
        cleared_count = len(simulation_results)
        simulation_results.clear()
        current_simulation = None
        
        return f"""
✓ All Octave Simulation Data Cleared
===================================

Cleared Items:
• {cleared_count} completed simulations
• Current active simulation
• All cached results and S-parameter data

Memory Status:
• Simulation cache: Empty
• Active simulation: None
• Ready for new simulations

Next Steps:
• Use create_cpw_octave_simulation() for CPW analysis
• Use check_octave_openems_status() to verify system status
• Generated Octave scripts remain in output directories

Note: This clears cached data, not the generated Octave scripts or results files.
"""
    
    else:
        # Clear specific simulation
        if simulation_name in simulation_results:
            del simulation_results[simulation_name]
            
            # Clear current simulation if it matches
            if current_simulation and current_simulation['name'] == simulation_name:
                current_simulation = None
            
            return f"""
✓ Simulation Cleared: {simulation_name}
=====================================

Cleared Items:
• Simulation results for {simulation_name}
• Associated cached S-parameter data
• Current simulation reference (if it was {simulation_name})

Remaining Simulations: {len(simulation_results)}

Note: Generated Octave script and output files remain unchanged.
To completely remove: manually delete the output directory.
"""
        
        else:
            available_sims = list(simulation_results.keys()) if simulation_results else ["None"]
            return f"""
❌ Simulation Not Found: {simulation_name}
========================================

Available Simulations:
{', '.join(available_sims)}

Use list_octave_simulations() to see all available simulations.
Use "all" to clear everything.
"""

# Main server startup
if __name__ == "__main__":
    print("🚀 Starting Octave OpenEMS FastMCP Server...")
    print(f"🔧 Octave Available: {octave_available}")
    if octave_available:
        print(f"📋 {octave_info}")
    else:
        print("❌ Octave not available - install Octave to use this server")
    
    openems_exe = shutil.which("openEMS")
    print(f"⚡ OpenEMS: {'Available' if openems_exe else 'Not Found'}")
    
    mcp.run() 