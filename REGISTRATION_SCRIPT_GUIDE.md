# VALIS Registration Script Usage Guide

This guide provides detailed information on using the `valis.py` registration script for HE and CD8 qptiff files.

## Overview

The script performs automated registration of two whole slide images:
- **HE.qptiff** (Hematoxylin and Eosin) - the moving/source image
- **CD8.qptiff** (immunofluorescence) - the reference/target image

### Key Features

1. **Automatic Downsampling**: HE file is automatically downsampled by 2x to match the magnification of CD8
2. **Channel Selection**: Uses CD8 channel 0 (DAPI) for coregistration
3. **GPU Acceleration**: Automatically detects and uses NVIDIA GPU (tested with L40)
4. **Complete Pipeline**: Performs rigid and non-rigid registration
5. **Quality Metrics**: Generates registration error statistics and visual overlays

## Installation

Ensure you have VALIS installed with all dependencies:

```bash
pip install valis-wsi
```

For GPU support, ensure PyTorch with CUDA is installed:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Basic Usage

### Simple Registration

```bash
python valis.py HE.qptiff CD8.qptiff
```

This will:
1. Downsample HE.qptiff by 2x
2. Register both images using CD8 channel 0 (DAPI) as reference
3. Save results to `./valis_results/`
4. Save registered slides to `./valis_registered/`

### Custom Output Directories

```bash
python valis.py HE.qptiff CD8.qptiff \
    --output ./my_results \
    --registered-output ./my_registered_slides
```

### Force CPU Mode

If you want to run without GPU (for testing or debugging):

```bash
python valis.py HE.qptiff CD8.qptiff --no-gpu
```

## Command Line Arguments

| Argument | Short | Required | Default | Description |
|----------|-------|----------|---------|-------------|
| `he_file` | - | Yes | - | Path to HE.qptiff file (moving image) |
| `cd8_file` | - | Yes | - | Path to CD8.qptiff file (reference image) |
| `--output` | `-o` | No | `./valis_results` | Output directory for registration data |
| `--registered-output` | `-r` | No | `./valis_registered` | Output directory for registered slides |
| `--no-gpu` | - | No | False | Force CPU usage instead of GPU |

## Output Structure

### Registration Results Directory (`./valis_results/`)

```
valis_results/
├── registration_input/          # Temporary directory with input files
├── processed/                   # Processed images used for registration
│   ├── HE_downsampled_2x.png
│   └── CD8.png
├── rigid_registration/          # Thumbnails after rigid registration
│   ├── HE_downsampled_2x.png
│   └── CD8.png
├── non_rigid_registration/      # Thumbnails after non-rigid registration
│   ├── HE_downsampled_2x.png
│   └── CD8.png
├── overlaps/                    # Visual comparison overlays
│   ├── unregistered.png        # Before registration
│   ├── rigid.png               # After rigid registration
│   └── non_rigid.png           # After non-rigid registration
├── deformation_fields/          # Visualization of non-rigid deformation
│   └── HE_downsampled_2x.png
├── masks/                       # Tissue masks used for registration
└── data/                        # Registration statistics and metadata
    ├── summary.csv              # Registration error and timing info
    └── valis_registrar.pickle   # Serialized registrar (for reuse)
```

### Registered Slides Directory (`./valis_registered/`)

```
valis_registered/
├── HE_downsampled_2x.ome.tiff  # Registered HE slide
└── CD8.ome.tiff                # Registered CD8 slide (aligned)
```

## Understanding the Registration Process

### Step 1: Downsampling

The script automatically downsamples the HE file by 2x using pyvips:

```python
downsampled = image.resize(1.0 / factor, kernel='lanczos3')
```

This ensures both images have matching magnification before registration.

### Step 2: Channel Selection

For the CD8 fluorescence image, the script configures channel 0 (DAPI):

```python
processor_dict = {
    reference_img: [
        preprocessing.ChannelGetter,
        {"channel": 0, "adaptive_eq": True}
    ]
}
```

### Step 3: Registration

VALIS performs:
1. **Rigid Registration**: Aligns images using feature detection and matching
2. **Non-Rigid Registration**: Fine-tunes alignment with local deformations

### Step 4: Output Generation

The registered slides are saved as ome.tiff files, preserving metadata and enabling use in downstream analysis tools.

## GPU Acceleration

### Benefits

With GPU acceleration (L40 or equivalent):
- **Feature Detection**: 10-50x faster using DISK/DeDoDe/LightGlue
- **Non-Rigid Registration**: 5-20x faster using RAFTWarper
- **Overall**: Typical registration time reduces from 30-60 minutes to 5-10 minutes

### Verification

The script automatically detects GPU availability:

```
✓ GPU detected: NVIDIA L40
  CUDA Version: 12.1
  GPU acceleration will be used for registration
```

If no GPU is detected:

```
✗ No GPU detected - using CPU
```

## Troubleshooting

### Issue: Out of Memory Error

**Solution**: The script uses optimized image sizes (2048px) that work well with L40 GPU. If you have less memory, you can modify the script to use smaller sizes.

### Issue: Registration Quality is Poor

**Solution**: Check the overlaps directory to visually inspect registration quality. Poor results might indicate:
- Images are too different (wrong staining/channels)
- Insufficient tissue overlap
- Need for different preprocessing parameters

### Issue: Script Cannot Find Images

**Solution**: Provide full paths to the qptiff files:

```bash
python valis.py /full/path/to/HE.qptiff /full/path/to/CD8.qptiff
```

## Advanced Usage

### Reusing Registration Results

The pickled registrar in `data/valis_registrar.pickle` can be reused for:
- Warping additional images
- Transforming point coordinates
- Applying registration to new data

Example:

```python
import pickle
from valis import registration

# Load the registrar
with open('./valis_results/data/valis_registrar.pickle', 'rb') as f:
    registrar = pickle.load(f)

# Use it to warp points, etc.
# ...
```

## Performance Benchmarks

Typical performance on L40 GPU with 2048px images:

| Step | CPU Time | GPU Time | Speedup |
|------|----------|----------|---------|
| Downsampling | ~30s | ~30s | - |
| Rigid Registration | ~5-10 min | ~30-60s | ~10x |
| Non-Rigid Registration | ~20-30 min | ~2-5 min | ~6-10x |
| Warping & Saving | ~10-15 min | ~2-3 min | ~5x |
| **Total** | **35-55 min** | **5-9 min** | **~7x** |

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Run registration
python valis.py /data/slides/HE.qptiff /data/slides/CD8.qptiff \
    --output ./results_2024 \
    --registered-output ./registered_2024

# 2. Check registration quality
# View overlaps in: ./results_2024/overlaps/

# 3. Review error statistics
cat ./results_2024/data/summary.csv

# 4. Use registered slides for analysis
# Open ./registered_2024/*.ome.tiff in QuPath or other software
```

## Citation

If you use this script in your research, please cite:

```
Gatenbee CD, et al. (2023) Virtual alignment of pathology image series for 
multi-gigapixel whole slide images. Nature Communications.
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/MathOnco/valis/issues
- Documentation: https://valis.readthedocs.io
