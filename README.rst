
|docs| |CI| |pypi|

.. .. |Upload Python Package| image:: https://github.com/MathOnco/valis/actions/workflows/python-publish.yml/badge.svg
    :target: https://github.com/MathOnco/valis/actions/workflows/python-publish.yml

.. .. |build-status| image:: https://circleci.com/gh/readthedocs/readthedocs.org.svg?style=svg
..     :alt: build status
..     :target: https://circleci.com/gh/readthedocs/readthedocs.org

.. |docs| image:: https://readthedocs.org/projects/valis/badge/?version=latest
    :target: https://valis.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |CI| image:: https://github.com/MathOnco/valis/workflows/CI/badge.svg?branch=main
    :target: https://github.com/MathOnco/valis/actions?workflow=CI
    :alt: CI Status

.. .. |conda| image:: https://img.shields.io/conda/vn/conda-forge/valis_wsi
    :alt: Conda (channel only)

.. |pypi| image:: https://badge.fury.io/py/valis-wsi.svg
    :target: https://badge.fury.io/py/valis-wsi

.. image:: https://zenodo.org/badge/444523406.svg
   :target: https://zenodo.org/badge/latestdoi/444523406


.. .. |coverage| image:: https://codecov.io/gh/readthedocs/readthedocs.org/branch/master/graph/badge.svg
..     :alt: Test coverage
..     :scale: 100%
..     :target: https://codecov.io/gh/readthedocs/readthedocs.org

|
|

.. image::  https://github.com/MathOnco/valis/raw/main/docs/_images/banner.gif

|
|


VALIS, which stands for Virtual Alignment of pathoLogy Image Series, is a fully automated pipeline to register whole slide images (WSI) using rigid and/or non-rigid transformtions. A full description of the method is described in the paper by `Gatenbee et al. 2023 <https://www.nature.com/articles/s41467-023-40218-9>`_. VALIS uses `Bio-Formats <https://www.openmicroscopy.org/bio-formats/>`_, `OpenSlide <https://openslide.org/>`__, `libvips <https://www.libvips.org/>`_, and `scikit-image <https://scikit-image.org/>`_ to read images and slides, and so is able to work with over 300 image formats. Registered images can be saved as `ome.tiff <https://docs.openmicroscopy.org/ome-model/5.6.3/ome-tiff/>`_ slides that can be used in downstream analyses. ome.tiff format is opensource and widely supported, being readable in several different programming languages (Python, Java, Matlab, etc...) and software, such as `QuPath <https://qupath.github.io/>`_, `HALO by Idica Labs <https://indicalab.com/halo/>`_, etc...

The registration pipeline is fully automated and goes as follows:

    .. image::  https://github.com/MathOnco/valis/raw/main/docs/_images/pipeline.png

   #. Images/slides are converted to numpy arrays. As WSI are often too large to fit into memory, these images are usually lower resolution images from different pyramid levels.

   #. Images are processed to single channel images. They are then normalized to make them look as similar as possible. Masks are then created to focus registration on the tissue.

   #. Image features are detected and then matched between all pairs of image.

   #. If the order of images is unknown, they will be optimally ordered based on their feature similarity. This increases the chances of successful registration because each image will be aligned to one that looks very similar.

   #. Images will be aligned *towards* (not to) a reference image. If the reference image is not specified, it will automatically be set to the image at the center of the stack.

   #. Rigid registration is performed serially, with each image being rigidly aligned towards the reference image. That is, if the reference image is the 5th in the stack, image 4 will be aligned to 5 (the reference), and then 3 will be aligned to the now registered version of 4, and so on. Only features found in both neighboring slides are used to align the image to the next one in the stack. VALIS uses feature detection to match and align images, but one can optionally perform a final step that maximizes the mutual information between each pair of images. This rigid registration can optionally be updated by matching features in higher resolution versions of the images (see :code:`micro_rigid_registrar.MicroRigidRegistrar`).

   #. The registered rigid masks are combined to create a non-rigid registration mask. The bounding box of this mask is then used to extract higher resolution versions of the tissue from each slide. These higher resolution images are then processed as above and used for non-rigid registration, which is performed either by:

        * aligning each image towards the reference image following the same sequence used during rigid registration.
        * using groupwise registration that non-rigidly aligns the images to a common frame of reference. Currently this is only possible if `SimpleElastix <https://simpleelastix.github.io>`__ is installed.

   #. One can optionally perform a second non-rigid registration using an even higher resolution versions of each image. This is intended to better align micro-features not visible in the original images, and so is referred to as micro-registration. A mask can also be used to indicate where registration should take place.

   #. Error is estimated by calculating the distance between registered matched features in the full resolution images.

The transformations found by VALIS can then be used to warp the full resolution slides. It is also possible to merge non-RGB registered slides to create a highly multiplexed image. These aligned and/or merged slides can then be saved as ome.tiff images. The transformations can also be use to warp point data, such as cell centroids, polygon vertices, etc...

In addition to registering images, VALIS provides tools to read slides using Bio-Formats and OpenSlide, which can be read at multiple resolutions and converted to numpy arrays or pyvips.Image objects. One can also slice regions of interest from these slides and warp annotated images. VALIS also provides functions to convert slides to the ome.tiff format, preserving the original metadata. Please see examples and documentation for more details.

Installation
------------

**Important:** VALIS requires several system-level dependencies to be installed before you can install it with pip.

System Dependencies (Required)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before installing VALIS, you must install these system dependencies:

**1. Java Development Kit (JDK)**

VALIS uses Bio-Formats to read slide images, which requires Java.

* Download and install JDK from `Oracle <http://www.oracle.com/technetwork/java/javase/downloads/index.html>`_ or use OpenJDK
* Set the JAVA_HOME environment variable:

  .. code-block:: bash

      export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64  # Linux example
      # Or: export JAVA_HOME=/usr/libexec/java_home  # macOS example

**2. Maven**

Maven is required for Bio-Formats support.

* Install from `Apache Maven <https://maven.apache.org/index.html>`_

**3. libvips**

VALIS uses pyvips for image processing, which requires the libvips library.

.. important::

    **If you skip this step, you will get an error like:** ``fatal error: glib.h: No such file or directory``

* **Ubuntu/Debian:**

  .. code-block:: bash

      sudo apt-get update
      sudo apt-get install --no-install-recommends libvips libvips-dev

* **macOS:**

  .. code-block:: bash

      brew install vips

* **Windows:**

  Download pre-built binaries from `libvips releases <https://github.com/libvips/libvips/releases>`_

  See `pyvips installation notes <https://github.com/libvips/pyvips#install>`_ for detailed Windows instructions.

* **Conda (all platforms):**

  .. code-block:: bash

      conda install -c conda-forge libvips

**4. OpenSlide (Optional but recommended)**

OpenSlide is needed for some slide formats (.vmu, .mrxs, .svslide).

* **Ubuntu/Debian:**

  .. code-block:: bash

      sudo apt-get install openslide-tools libopenslide-dev

* **macOS:**

  .. code-block:: bash

      brew install openslide

* **Windows:** Download from `OpenSlide <https://openslide.org/download/>`_

Installing VALIS
~~~~~~~~~~~~~~~~~

After installing the system dependencies above, install VALIS using pip:

.. code-block:: bash

    pip install valis-wsi

Or install from source in development mode:

.. code-block:: bash

    git clone https://github.com/MathOnco/valis.git
    cd valis
    pip install -e .

Alternative Installation Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Docker (Recommended for easy setup)**

The easiest way to use VALIS with all dependencies pre-installed:

.. code-block:: bash

    docker pull cdgatenbee/valis-wsi
    docker run -v "$HOME:$HOME" cdgatenbee/valis-wsi python3 /path/to/your_script.py

**Conda Environment**

Using conda can simplify system dependency management:

.. code-block:: bash

    conda create -n valis python=3.9
    conda activate valis
    conda install -c conda-forge libvips
    pip install valis-wsi

For complete installation instructions, troubleshooting, and optional dependencies like SimpleElastix, see the `full installation guide <https://valis.readthedocs.io/en/latest/installation.html>`_.

GPU Acceleration
----------------

VALIS automatically uses GPU acceleration when available to significantly speed up registration:

* **Feature detection and matching**: Uses GPU-accelerated deep learning models (DISK, DeDoDe, LightGlue) via PyTorch
* **Non-rigid registration**: Default RAFTWarper uses GPU via PyTorch for optical flow computation
* **SimpleElastix registration**: Attempts to use GPU/OpenCL when available (requires Elastix compiled with OpenCL support)

If no GPU is detected, VALIS automatically falls back to CPU processing. You can also force CPU usage by passing ``force_cpu=True`` to registration classes if needed.


Quick Start: Registration Script
----------------------------------

A ready-to-use registration script is provided for registering HE and CD8 qptiff files::

    python valis.py HE.qptiff CD8.qptiff

This script:

* Automatically downsamples the HE file by 2x to match CD8 magnification
* Uses CD8 channel 0 (DAPI) as the reference for coregistration
* Leverages GPU acceleration for optimal performance (tested with L40 GPU)
* Saves registered slides in ome.tiff format

**Usage:**

.. code-block:: bash

    # Basic usage
    python valis.py HE.qptiff CD8.qptiff

    # Specify custom output directories
    python valis.py HE.qptiff CD8.qptiff --output ./results --registered-output ./registered

    # Force CPU usage (disable GPU)
    python valis.py HE.qptiff CD8.qptiff --no-gpu

**Arguments:**

* ``he_file``: Path to HE.qptiff file (moving image, will be downsampled 2x)
* ``cd8_file``: Path to CD8.qptiff file (reference image with DAPI channel)
* ``--output``, ``-o``: Output directory for registration results (default: ./valis_results)
* ``--registered-output``, ``-r``: Output directory for registered slides (default: ./valis_registered)
* ``--no-gpu``: Force CPU usage instead of GPU

**Requirements:**

* NVIDIA GPU with CUDA support (recommended: L40 or equivalent)
* PyTorch with CUDA support
* All VALIS dependencies installed

**Output:**

The script generates two output directories:

1. Registration results directory (``./valis_results`` by default):
   
   * ``processed/``: Processed/normalized images used for registration
   * ``rigid_registration/``: Thumbnails after rigid registration
   * ``non_rigid_registration/``: Thumbnails after non-rigid registration
   * ``overlaps/``: Visual comparison of registration quality
   * ``data/``: Registration statistics and pickled registrar object

2. Registered slides directory (``./valis_registered`` by default):
   
   * Full-resolution registered slides in ome.tiff format


Full documentation with installation instructions and examples can be found at `ReadTheDocs <https://valis.readthedocs.io/en/latest/>`_.


License
-------

`MIT`_ © 2021-2025 Chandler Gatenbee

.. _MIT: LICENSE.txt
