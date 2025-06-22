import numpy as np
import gdstk
import argparse
from scipy.sparse.linalg import gmres, LinearOperator
from multiprocessing import Pool, cpu_count
import functools
from tqdm import tqdm

def read_gds(filename, layer_map):
    """
    Reads a GDSII file and extracts polygons for specified layers.
    Same as original but with flattening support.
    """
    print(f"Reading GDS file: {filename}")
    library = gdstk.read_gds(filename)
    top_cells = library.top_level()
    if not top_cells:
        print("Error: No top-level cells found in GDS file.")
        return []
    top_cell = top_cells[0]

    # Flatten the cell hierarchy to get all polygons
    print(f"Flattening cell hierarchy from top cell: {top_cell.name}")
    flattened_cell = top_cell.flatten()
    
    polygons_with_ids = []
    for poly in flattened_cell.polygons:
        if poly.layer in layer_map:
            conductor_id = layer_map[poly.layer]
            polygons_with_ids.append((poly.points, conductor_id))

    if not polygons_with_ids:
        print("Warning: No polygons found for the specified layers.")
        print(f"Available layers in flattened geometry: {set(poly.layer for poly in flattened_cell.polygons)}")

    return polygons_with_ids

def discretize_polygons_optimized(polygons_with_ids, max_segment_length, min_segment_length=0.01):
    """
    Optimized discretization with minimum segment length filtering.
    
    Args:
        polygons_with_ids: List of (polygon_vertices, conductor_id)
        max_segment_length: Maximum segment length
        min_segment_length: Minimum segment length (smaller segments are merged)
    """
    segments = []
    total_removed = 0
    
    for poly_verts, conductor_id in polygons_with_ids:
        for i in range(len(poly_verts)):
            p1 = poly_verts[i]
            p2 = poly_verts[(i + 1) % len(poly_verts)]
            
            edge_vector = p2 - p1
            edge_length = np.linalg.norm(edge_vector)
            
            # Skip very small edges that don't contribute significantly
            if edge_length < min_segment_length:
                total_removed += 1
                continue
            
            num_segments = int(np.ceil(edge_length / max_segment_length))
            if num_segments == 0:
                continue

            segment_length = edge_length / num_segments
            segment_vector = edge_vector / num_segments

            for j in range(num_segments):
                start_point = p1 + j * segment_vector
                end_point = start_point + segment_vector
                center_point = start_point + 0.5 * segment_vector
                
                segments.append({
                    'start': start_point,
                    'end': end_point,
                    'center': center_point,
                    'length': segment_length,
                    'conductor_id': conductor_id
                })
    
    print(f"Geometric optimization: Removed {total_removed} tiny segments")
    return segments

def compute_influence_chunk(args):
    """
    Compute influence matrix elements for a chunk of segments (for parallelization).
    """
    i_start, i_end, segments, j_indices = args
    n_i = i_end - i_start
    n_j = len(j_indices)
    
    epsilon_0 = 8.854187817e-12
    eps = 1e-12
    
    # Pre-allocate result array
    chunk_result = np.zeros((n_i, n_j))
    
    for local_i, global_i in enumerate(range(i_start, i_end)):
        seg_i = segments[global_i]
        
        for local_j, global_j in enumerate(j_indices):
            seg_j = segments[global_j]
            
            if global_i == global_j:
                # Self-term
                chunk_result[local_i, local_j] = -(seg_i['length'] / (2 * np.pi * epsilon_0)) * (np.log(seg_i['length'] / 2) - 1)
            else:
                # Off-diagonal term
                dist = np.linalg.norm(seg_i['center'] - seg_j['center'])
                dist = max(dist, eps)
                chunk_result[local_i, local_j] = -(seg_j['length'] / (2 * np.pi * epsilon_0)) * np.log(dist)
    
    return chunk_result

class MatrixFreeOperator(LinearOperator):
    """
    Matrix-free operator for iterative solver.
    Instead of storing the full matrix, compute matrix-vector products on demand.
    """
    def __init__(self, segments, use_parallel=True, chunk_size=1000):
        self.segments = segments
        self.n_segments = len(segments)
        self.use_parallel = use_parallel
        self.chunk_size = chunk_size
        self.epsilon_0 = 8.854187817e-12
        self.eps = 1e-12
        
        # Prepare for parallel computation
        if use_parallel:
            self.n_cores = min(cpu_count(), 8)  # Limit to 8 cores to avoid memory issues
        else:
            self.n_cores = 1
        
        # Initialize parent LinearOperator
        super().__init__(dtype=np.float64, shape=(self.n_segments, self.n_segments))
    
    def _matvec(self, v):
        """
        Compute matrix-vector product P @ v without storing P.
        This is the key optimization - O(N²) operation but no O(N²) storage.
        """
        result = np.zeros(self.n_segments)
        
        if self.use_parallel and self.n_segments > 2000:
            # Parallel computation for large problems
            chunk_starts = list(range(0, self.n_segments, self.chunk_size))
            chunks = []
            
            for start in chunk_starts:
                end = min(start + self.chunk_size, self.n_segments)
                chunks.append((start, end, self.segments, list(range(self.n_segments))))
            
            with Pool(self.n_cores) as pool:
                chunk_results = pool.map(compute_influence_chunk, chunks)
            
            # Combine results
            for i, (start, _, _, _) in enumerate(chunks):
                end = min(start + self.chunk_size, self.n_segments)
                chunk_matvec = chunk_results[i] @ v
                result[start:end] = chunk_matvec
        else:
            # Serial computation for smaller problems
            for i in range(self.n_segments):
                seg_i = self.segments[i]
                for j in range(self.n_segments):
                    seg_j = self.segments[j]
                    
                    if i == j:
                        influence = -(seg_i['length'] / (2 * np.pi * self.epsilon_0)) * (np.log(seg_i['length'] / 2) - 1)
                    else:
                        dist = np.linalg.norm(seg_i['center'] - seg_j['center'])
                        dist = max(dist, self.eps)
                        influence = -(seg_j['length'] / (2 * np.pi * self.epsilon_0)) * np.log(dist)
                    
                    result[i] += influence * v[j]
        
        return result

def solve_bem_optimized(segments, num_conductors, tolerance=1e-6, max_iterations=1000):
    """
    Optimized BEM solver using matrix-free iterative methods.
    
    Key optimizations:
    1. Matrix-free GMRES instead of direct solver (O(N²) vs O(N³))
    2. No dense matrix storage (saves massive memory)
    3. Parallel matrix-vector products
    4. Configurable tolerance for trade-off between speed and accuracy
    """
    n_segments = len(segments)
    if n_segments == 0:
        return np.array([])
    
    print(f"Setting up matrix-free operator for {n_segments} segments...")
    
    # Create matrix-free operator
    use_parallel = n_segments > 1000  # Only use parallel for larger problems
    A_op = MatrixFreeOperator(segments, use_parallel=use_parallel)
    
    all_sigmas = []
    
    print(f"Solving {num_conductors} conductor problems using iterative GMRES...")
    
    for k in range(num_conductors):
        print(f"  Solving for conductor {k+1}/{num_conductors}")
        
        # Set up right-hand side vector
        V = np.zeros(n_segments)
        for i in range(n_segments):
            if segments[i]['conductor_id'] == k:
                V[i] = 1.0
        
        # Use GMRES iterative solver instead of direct solver
        # This is the key optimization: O(N²) instead of O(N³)
        sigma, info = gmres(
            A_op, V, 
            rtol=tolerance, 
            maxiter=max_iterations,
            restart=min(50, n_segments//10)  # Restart parameter for GMRES
        )
        
        if info == 0:
            print(f"    Converged successfully")
        elif info > 0:
            print(f"    Warning: Did not converge in {max_iterations} iterations (residual may be acceptable)")
        else:
            print(f"    Error: Solver failed with code {info}")
        
        all_sigmas.append(sigma)
    
    return np.array(all_sigmas)

def calculate_capacitance_matrix(all_sigmas, segments, num_conductors):
    """
    Same capacitance matrix calculation as original.
    """
    C = np.zeros((num_conductors, num_conductors))
    for k in range(num_conductors):
        sigma_k = all_sigmas[k]
        for m in range(num_conductors):
            Q_m = 0
            for i in range(len(segments)):
                if segments[i]['conductor_id'] == m:
                    Q_m += sigma_k[i] * segments[i]['length']
            C[m, k] = Q_m
    return C

def main():
    """
    Optimized main function with additional parameters for performance tuning.
    """
    parser = argparse.ArgumentParser(description='Optimized 2D Electrostatic Capacitance Solver')
    parser.add_argument('gds_file', type=str, help='Path to the GDSII file.')
    parser.add_argument('--layers', type=str, required=True, 
                        help='Layer mapping, e.g., "1:0,2:1" for layer 1 -> cond 0, layer 2 -> cond 1')
    parser.add_argument('--max_seg_len', type=float, default=1.0, 
                        help='Maximum segment length for discretization (in GDS units, e.g., um).')
    parser.add_argument('--min_seg_len', type=float, default=0.01,
                        help='Minimum segment length - smaller segments are filtered out')
    parser.add_argument('--tolerance', type=float, default=1e-6,
                        help='Solver tolerance (lower = more accurate but slower)')
    parser.add_argument('--max_iter', type=int, default=1000,
                        help='Maximum solver iterations')
    
    args = parser.parse_args()

    try:
        layer_map = dict(item.split(':') for item in args.layers.split(','))
        layer_map = {int(k): int(v) for k, v in layer_map.items()}
    except ValueError:
        print("Error: Invalid layer mapping format. Use 'layer:id,layer:id'.")
        return

    print("="*60)
    print("OPTIMIZED ELECTROSTATIC SOLVER")
    print("="*60)
    print(f"File: {args.gds_file}")
    print(f"Layers: {layer_map}")
    print(f"Max segment length: {args.max_seg_len} um")
    print(f"Min segment length: {args.min_seg_len} um")
    print(f"Solver tolerance: {args.tolerance}")
    print(f"Max iterations: {args.max_iter}")
    print(f"Available CPU cores: {cpu_count()}")
    print("="*60)

    # 1. Read GDS file
    polygons_with_ids = read_gds(args.gds_file, layer_map)
    if not polygons_with_ids:
        print("No polygons found. Exiting.")
        return

    print(f"Found {len(polygons_with_ids)} polygons.")

    # 2. Optimized discretization with filtering
    segments = discretize_polygons_optimized(polygons_with_ids, args.max_seg_len, args.min_seg_len)
    if not segments:
        print("No segments generated. Exiting.")
        return
    
    print(f"Polygons discretized into {len(segments)} segments (after optimization).")
    
    # Memory estimation
    dense_memory_gb = (len(segments)**2 * 8) / (1024**3)  # 8 bytes per float64
    print(f"Dense matrix would require {dense_memory_gb:.2f} GB memory")
    print(f"Matrix-free approach uses ~{len(segments) * 8 / (1024**2):.2f} MB")

    # 3. Optimized BEM solver
    num_conductors = len(layer_map)
    all_sigmas = solve_bem_optimized(segments, num_conductors, args.tolerance, args.max_iter)
    print("Optimized BEM solved for charge distribution.")

    # 4. Calculate capacitance matrix
    C = calculate_capacitance_matrix(all_sigmas, segments, num_conductors)
    
    print("\n" + "="*50)
    print("CAPACITANCE MATRIX RESULTS")
    print("="*50)
    # Convert to fF/um (1 F/m = 1e-3 fF/um)
    C_femtofarad_per_micron = C * 1e-3
    print("Capacitance Matrix (fF/um):")
    print(C_femtofarad_per_micron)
    print("="*50)

if __name__ == '__main__':
    main() 