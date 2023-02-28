# ---- This is <geocode_intensities_from_feature_folder.py> ----

"""
Example for easy use of 'geocoding' library for geocoding S1 intensities.
"""

import pathlib

import geocoding.generic_geocoding as geocoding
import geocoding.generic_geocoding as geocoding

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# define the basic data directory for your project
BASE_DIR = pathlib.Path('/media/jo/EO_disk/data/CIRFA_22/satellite_data/Sentinel-1')

# define S1 name
S1_name = 'S1A_EW_GRDM_1SDH_20220501T070432_20220501T070537_043014_0522C4_5982'

# build the path to output feature folder
feat_folder = BASE_DIR / f'features/ML_1x1/{S1_name}'

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# The feat_folder should contain the following files:
# Sigma0_HH_db.img
# Sigma0_HH_db.hdr
# Sigma0_HH_db.img
# Sigma0_HH_db.hdr
# lat.img
# lat.hdr
# lon.img
# lon.hdr
# You can for example use the S1_processing library to create these features
# https://github.com/jlo031/S1_processing



# Use the generic_geocoding module to geocode HH and HV intensities

# input files 
lat_path = feat_folder / 'lat.img'
lon_path = feat_folder / 'lon.img'
HH_path = feat_folder / 'Sigma0_HH_db.img'
HV_path = feat_folder / 'Sigma0_HV_db.img'

# geocoding parameters (choose according to your image and region

target_epsg = 3996
pixel_spacing = 40
srcnodata = 0
dstnodata = 0
tie_points = 21
order = 3
resampling = 'near'
keep_gcp_file = False
overwrite = False
loglevel = 'INFO'

# output files (write to your current folder, or build a different output path)
HH_geo_path = f'{S1_name}_{HH_path.stem}_epsg{target_epsg}_pixelspacing{pixel_spacing}.tiff'
HV_geo_path = f'{S1_name}_{HV_path.stem}_epsg{target_epsg}_pixelspacing{pixel_spacing}.tiff'
intensities_geo_path = f'{S1_name}_intensities_epsg{target_epsg}_pixelspacing{pixel_spacing}.tiff'


# geocode HH
geocoding.geocode_image_from_lat_lon(
    HH_path,
    lat_path,
    lon_path,
    HH_geo_path,
    target_epsg,
    pixel_spacing,
    tie_points = tie_points,
    srcnodata = srcnodata,
    dstnodata = dstnodata,
    order = order,
    resampling = resampling,
    keep_gcp_file = keep_gcp_file,
    overwrite = overwrite,
    loglevel = loglevel,
)

# geocode HV
geocoding.geocode_image_from_lat_lon(
    HV_path,
    lat_path,
    lon_path,
    HV_geo_path,
    target_epsg,
    pixel_spacing,
    tie_points = tie_points,
    srcnodata = srcnodata,
    dstnodata = dstnodata,
    order = order,
    resampling = resampling,
    keep_gcp_file = keep_gcp_file,
    overwrite = overwrite,
    loglevel = loglevel,
)


# for false-color representations (for example in QGIS), you might want the geocoded HH and HV channel stacked in one file
# Use the 'geocoding_utils' module for this (which is imported in 'generic_geocoding'
geocoding.geo_utils.stack_geocoded_images(
    HH_geo_path,
    HV_geo_path,
    intensities_geo_path,
)

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# ---- End of <geocode_intensities_from_feature_folder.py> ----

