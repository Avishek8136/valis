"""
Example demonstrating GPU acceleration in VALIS registration

This example shows how VALIS automatically uses GPU when available,
and how to force CPU usage if needed.
"""

from valis import registration, valtils

# Check if GPU is available
if valtils.is_gpu_available():
    print("✓ GPU detected - VALIS will use GPU acceleration")
    print(f"  Device: {valtils.get_device()}")
else:
    print("✗ No GPU detected - VALIS will use CPU")
    print(f"  Device: {valtils.get_device()}")

# Example 1: Default behavior (uses GPU if available)
print("\nExample 1: Default GPU-accelerated registration")
registrar = registration.Valis(
    src_dir="path/to/images",
    dst_dir="path/to/results"
)
# Registration will automatically use GPU for:
# - Feature detection (DISK, DeDoDe, LightGlue)
# - Non-rigid registration (RAFTWarper via PyTorch)
# - SimpleElastix operations (via OpenCL if available)

# Example 2: Force CPU usage
print("\nExample 2: Force CPU usage")
# You can force CPU usage by using force_cpu parameter in specific classes:

from valis import non_rigid_registrars, affine_optimizer

# Force CPU for non-rigid registration
nr_registrar_cpu = non_rigid_registrars.SimpleElastixWarper(force_cpu=True)

# Force CPU for affine optimization
affine_opt_cpu = affine_optimizer.AffineOptimizerMattesMI(force_cpu=True)

# Example 3: Specify GPU device for RAFTWarper
print("\nExample 3: Explicit device specification")
# RAFTWarper allows explicit device specification
raft_gpu = non_rigid_registrars.RAFTWarper(device='cuda')  # Force GPU
raft_cpu = non_rigid_registrars.RAFTWarper(device='cpu')   # Force CPU

print("\nGPU Acceleration Benefits:")
print("- Faster feature detection and matching (10-50x speedup)")
print("- Faster non-rigid registration with RAFTWarper (5-20x speedup)")
print("- Faster SimpleElastix operations when OpenCL is available")
print("- Automatic fallback to CPU when GPU is not available")
