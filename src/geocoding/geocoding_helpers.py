# ---- This is <geocoding_helpers.py> ----

"""
Module with small general helpers for geocoding 
"""

import argparse
import os
import sys
import pathlib
import shutil

from loguru import logger

import numpy as np

from osgeo import gdal, osr, gdal_array

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def warp_image_to_target_projection(
    input_img_path,
    output_tif_path,
    target_epsg,
    pixel_spacing,
    resampling = 'near',
    order = 3
):
    """Warp input image to target projection (epsg) using gdalwarp
       
    Parameters
    ----------
    input_img_path : path to input image file containing with embedded gcps
    output_tif_path: path to output geo-coded image file (tif format)
    target_epsg : output epsg code
    pixel_spacing : output pixel spacing in units of the target projection
    resampling : resampling method to use for gdalwarp (default='near')
    order: order of polynomial used for gdalwarp (default=3)    
    """ 

    # gdalwarp command to project the input image and save output tif to output_tif_path
    gdal_cmd = f'gdalwarp ' + \
        f'-overwrite -srcnodata 0 -dstnodata 0 ' + \
        f'-t_srs epsg:{target_epsg} ' + \
        f'-tr {pixel_spacing} {pixel_spacing} ' + \
        f'-r {resampling} ' + \
        f'-order {order} ' + \
        f'{input_img_path.as_posix()} {output_tif_path.as_posix()}'

    logger.info(f'Running gdalwarp to warp image to desired projection ({target_epsg})')
    logger.info(f'Executing: {gdal_cmd}')

    os.system(gdal_cmd)
    
    return

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def create_srs_and_WKT(source_epsg = 4326):
    """create spatial reference system (srs) and corresponding WKT string
      
    Parameters
    ----------
    source_epsg : epsg code for srs (default = 4326, which is WGS84 geographic lat/lon)
      
    Returns
    -------
    srs : spatial reference system object
    tie_point_WKT : srs in WKT string format
    """

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(source_epsg)
    tie_point_WKT = srs.ExportToWkt()
    
    return srs, tie_point_WKT

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def get_tie_points_from_lat_lon(
    lat,
    lon,
    tie_points=21,
    loglevel='INFO'
):

    """Create tie-point grid from lat/lon bands

    Parameters
    ----------
    lat : path to input latitude array
    lon : path to input longitude array
    tie_points : number of tie points per dimension (default=21)
    loglevel : loglevel setting (default='INFO')

    Returns
    -------
    gcps : list of tie points
    tie_point_WKT : tie-point well-known text projection
    """

    # remove default logger handler and add personal one
    logger.remove()
    logger.add(sys.stderr, level=loglevel)

    logger.info('Extracting tie points (GCPs) from lat/lon arrays')

    logger.debug(f'{locals()}')
    logger.debug(f'file location: {__file__}')

    # get directory where module is installed
    module_path = pathlib.Path(__file__).parent.parent
    logger.debug(f'module_path: {module_path}')

# -------------------------------------------------------------------------- #

    # check that lat and lon dimenesions match
    if lat.shape != lon.shape :
        logger.error('lat and lon arrays must have the same shape')
        raise ValueError(f'lat and lon arrays must have the same shape')

    # get dimensions
    lines, samples = lat.shape

    logger.debug(f'number of lines-x-samples: {lines}-x-{samples}')


    # extract tie-point-grid.
    tie_points_x = np.linspace(0, samples-1, tie_points, endpoint=True).astype(int)
    tie_points_y = np.linspace(0, lines-1, tie_points, endpoint=True).astype(int)

    # extract lats and lons for tie points
    tie_points_lat = lat[np.ix_(tie_points_y, tie_points_x)]
    tie_points_lon = lon[np.ix_(tie_points_y, tie_points_x)]


    # build list of gcps
    gcps = []
    for xi in range(tie_points):
        for yi in range(tie_points):
            tpgcp = gdal.GCP(
                tie_points_lon[yi, xi].astype(float),
                tie_points_lat[yi, xi].astype(float),
                0,
                tie_points_x[xi].astype(float)+1.0,
                tie_points_y[yi].astype(float)+1.0
            )
            gcps.append(tpgcp)


    # make WKT at this time too.
    srs, tie_point_WKT = create_srs_and_WKT()

    return (gcps, tie_point_WKT)

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# ---- End of <geocoding_helpers.py> ----
