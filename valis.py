#!/usr/bin/env python
"""
VALIS Registration Script for HE and CD8 qptiff files

This script performs registration of two whole slide images:
- HE.qptiff (moving image) - will be downsampled by 2x
- CD8.qptiff (reference image) - uses channel 0 (DAPI) for coregistration

Usage:
    python valis.py HE.qptiff CD8.qptiff

Requirements:
    - GPU support (tested with L40 GPU)
    - VALIS library with all dependencies
"""

import os
import sys
import argparse
import time
import pyvips
from valis import registration, preprocessing, slide_io
import torch


def downsample_slide(input_path, output_path, factor=2):
    """
    Downsample a slide by a given factor using pyvips.
    
    Parameters
    ----------
    input_path : str
        Path to input slide file
    output_path : str
        Path to save downsampled slide
    factor : int
        Downsampling factor (default: 2)
    
    Returns
    -------
    str
        Path to downsampled slide
    """
    print(f"Downsampling {input_path} by factor of {factor}...")
    
    # Load the slide using pyvips
    image = pyvips.Image.new_from_file(input_path, access='sequential')
    
    # Downsample the image
    downsampled = image.resize(1.0 / factor, kernel='lanczos3')
    
    # Save the downsampled image
    downsampled.write_to_file(output_path)
    
    print(f"Downsampled slide saved to: {output_path}")
    return output_path


def main():
    """
    Main function to perform VALIS registration with HE and CD8 files.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Register HE and CD8 qptiff files using VALIS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python valis.py HE.qptiff CD8.qptiff
    python valis.py /path/to/HE.qptiff /path/to/CD8.qptiff --output ./results
        """
    )
    parser.add_argument('he_file', type=str, help='Path to HE.qptiff file (moving image)')
    parser.add_argument('cd8_file', type=str, help='Path to CD8.qptiff file (reference image)')
    parser.add_argument('--output', '-o', type=str, default='./valis_results',
                        help='Output directory for results (default: ./valis_results)')
    parser.add_argument('--registered-output', '-r', type=str, default='./valis_registered',
                        help='Output directory for registered slides (default: ./valis_registered)')
    parser.add_argument('--no-gpu', action='store_true',
                        help='Force CPU usage instead of GPU')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.he_file):
        print(f"Error: HE file not found: {args.he_file}")
        sys.exit(1)
    
    if not os.path.exists(args.cd8_file):
        print(f"Error: CD8 file not found: {args.cd8_file}")
        sys.exit(1)
    
    # Check GPU availability
    if torch.cuda.is_available() and not args.no_gpu:
        print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA Version: {torch.version.cuda}")
        print("  GPU acceleration will be used for registration")
    else:
        if args.no_gpu:
            print("  CPU mode forced by user")
        else:
            print("✗ No GPU detected - using CPU")
    
    # Create output directories
    os.makedirs(args.output, exist_ok=True)
    
    # Step 1: Downsample HE file by 2x
    print("\n" + "="*70)
    print("Step 1: Downsampling HE file")
    print("="*70)
    
    he_basename = os.path.basename(args.he_file)
    he_name = os.path.splitext(he_basename)[0]
    downsampled_he_path = os.path.join(args.output, f"{he_name}_downsampled_2x.tiff")
    
    # Downsample the HE file
    downsampled_he_path = downsample_slide(args.he_file, downsampled_he_path, factor=2)
    
    # Step 2: Prepare for registration
    print("\n" + "="*70)
    print("Step 2: Setting up VALIS registration")
    print("="*70)
    
    # Create a temporary directory with both files
    src_dir = os.path.join(args.output, "registration_input")
    os.makedirs(src_dir, exist_ok=True)
    
    # Copy/link files to source directory
    import shutil
    cd8_dest = os.path.join(src_dir, os.path.basename(args.cd8_file))
    he_dest = os.path.join(src_dir, os.path.basename(downsampled_he_path))
    
    if not os.path.exists(cd8_dest):
        shutil.copy2(args.cd8_file, cd8_dest)
    if not os.path.exists(he_dest):
        shutil.copy2(downsampled_he_path, he_dest)
    
    print(f"Registration source directory: {src_dir}")
    print(f"Registration results directory: {args.output}")
    
    # Step 3: Configure registration parameters
    print("\n" + "="*70)
    print("Step 3: Configuring registration parameters")
    print("="*70)
    
    # Set CD8 as reference image (it will use channel 0 - DAPI)
    reference_img = os.path.basename(args.cd8_file)
    print(f"Reference image: {reference_img} (using channel 0 - DAPI)")
    print(f"Moving image: {os.path.basename(downsampled_he_path)} (HE downsampled 2x)")
    
    # Configure processor for CD8 to use channel 0 (DAPI)
    # CD8 is fluorescence, so use ChannelGetter
    processor_dict = {
        reference_img: [
            preprocessing.ChannelGetter,
            {"channel": 0, "adaptive_eq": True}  # Use channel 0 (DAPI)
        ]
    }
    
    # Step 4: Perform registration
    print("\n" + "="*70)
    print("Step 4: Performing registration")
    print("="*70)
    
    start_time = time.time()
    
    # Create VALIS registrar with GPU-optimized settings
    registrar = registration.Valis(
        src_dir=src_dir,
        dst_dir=args.output,
        reference_img_f=reference_img,
        align_to_reference=True,
        # Use GPU-accelerated feature detector and matcher (default)
        # GPU will be used automatically if available
        max_processed_image_dim_px=2048,  # Higher resolution for better accuracy with GPU
        max_non_rigid_registration_dim_px=2048,  # Higher resolution for non-rigid registration
    )
    
    # Perform registration with custom processor for CD8
    print("Starting registration process...")
    print("This may take several minutes depending on image size and GPU availability...")
    
    rigid_registrar, non_rigid_registrar, error_df = registrar.register(
        processor_dict=processor_dict
    )
    
    registration_time = time.time() - start_time
    
    print(f"\n✓ Registration completed in {registration_time/60:.2f} minutes")
    
    # Display error statistics
    if error_df is not None and not error_df.empty:
        print("\nRegistration Error Statistics:")
        print(error_df.to_string())
    
    # Step 5: Warp and save registered slides
    print("\n" + "="*70)
    print("Step 5: Warping and saving registered slides")
    print("="*70)
    
    os.makedirs(args.registered_output, exist_ok=True)
    
    start_time = time.time()
    registrar.warp_and_save_slides(args.registered_output)
    warp_time = time.time() - start_time
    
    print(f"✓ Registered slides saved in {warp_time/60:.2f} minutes")
    print(f"  Output directory: {args.registered_output}")
    
    # Step 6: Summary
    print("\n" + "="*70)
    print("Registration Complete!")
    print("="*70)
    print(f"\nResults saved to:")
    print(f"  Registration data: {args.output}")
    print(f"  Registered slides: {args.registered_output}")
    print(f"\nTotal time: {(registration_time + warp_time)/60:.2f} minutes")
    
    # Cleanup: Shutdown JVM
    print("\nCleaning up...")
    registration.kill_jvm()
    print("Done!")


if __name__ == "__main__":
    main()
