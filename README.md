# geocoding
This library provides methods for geocoding of image data from different satellite sensors. The geo-information is stored in the form of ground control points (GCPs) which are embedded in the images and then allow gdal to warp the image into the desired projection. This works well for marine and sea ice applications. For more precise geocoding or over areas with significant topography changes, other methods such as *Range-Doppler Terrain Correction* will provide beter results.



### Preparation
The Geospatial Data Abstraction Layer ([GDAL]) library is required to run the code.  
The simplest way to use GDAL with Python is to get the Anaconda Python distribution.  
It is recommended to run the code in a virtual environment.

    # create new environment
    conda create -y -n geocoding gdal
    
    # activate environment
    conda activate geocoding
    
    # install required packages
    conda install -y scipy loguru pillow
    pip install ipython


### Installation
You can install this library directly from github (1) or locally after cloning (2).  
For both installation options, first set up the environment as described above.

1. **Installation from github**

       # install this package
       pip install git+https://github.com/jlo031/geocoding

2. **Local installation**

       # clone the repository
       git clone git@github.com:jlo031/geocoding.git

   Change into the main directory of the cloned repository (it should contain the *setup.py* file) and install the library:

       # installation
       pip install .



### Usage Examples
