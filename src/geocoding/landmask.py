# ---- This is <landmask.py> ----

"""
Module for geocoding of RS2 images
"""

import argparse
import os
import sys
import pathlib
import shutil

from loguru import logger

import numpy as np

from osgeo import gdal, ogr, osr, gdal_array
from PIL import Image, ImageDraw

import geocoding.geocoding_utils as geo_utils

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def convert_osm_landmask_2_SAR_geometry(
    lat_path,
    lon_path,
    shapefile_path,
    output_path,
    tie_points=21,
    overwrite = False,
    loglevel = 'INFO',
):

    """Create SAR geometry landmask from OSM shapefile

    Parameters
    ----------
    lat_path : path to input latiude image
    lon_path : path to input longitude image
    shapefile_path : path to OSM shapefile
    output_path : path to output mask file
    tie_points : number of tie points per dimension (default=21)
    overwrite : overwrite existing files (default=False)
    loglevel : loglevel setting (default='INFO')

    INFO
    ----
    Download shapefiles here: https://osmdata.openstreetmap.de/data/water-polygons.html
                              https://osmdata.openstreetmap.de/data/land-polygons.html
    """

    # remove default logger handler and add personal one
    logger.remove()
    logger.add(sys.stderr, level=loglevel)

    logger.info('Warping OSM shapefile to SAR geometry landmask')

# -------------------------------------------------------------------------- #

    # convert folder/file strings to paths
    lat_path       = pathlib.Path(lat_path).expanduser().absolute()
    lon_path       = pathlib.Path(lon_path).expanduser().absolute()
    shapefile_path = pathlib.Path(shapefile_path).expanduser().absolute()
    output_path    = pathlib.Path(output_path).expanduser().absolute()

    # convert tie_point string to integer
    tie_points = int(tie_points)

    logger.debug(f'lat_path:       {lat_path}')
    logger.debug(f'lon_path:       {lon_path}')
    logger.debug(f'shapefile_path: {shapefile_path}')
    logger.debug(f'output_path:    {output_path}')

    if not lat_path.is_file():
        logger.error(f'Cannot find lat_path: {lat_path}')
        raise FileNotFoundError(f'Cannot find lat_path: {lat_path}')

    if not lon_path.is_file():
        logger.error(f'Cannot find lon_path: {lon_path}')
        raise FileNotFoundError(f'Cannot find lon_path: {lon_path}')

    if not shapefile_path.is_file():
        logger.error(f'Cannot find shapefile_path: {shapefile_path}')
        raise FileNotFoundError(f'Cannot find shapefile_path: {shapefile_path}')

    # check if outfile already exists
    if output_path.is_file() and not overwrite:
        logger.info('Output file already exists, use `-overwrite` to force')
        return
    elif output_path.is_file() and overwrite:
        logger.info('Removing existing output file')
        output_path.unlink()


    logger.debug(f'tie_points:    {tie_points}')

# -------------------------------------------------------------------------- #

    # open image dataset
    ds = gdal.Open(lat_path.as_posix(), gdal.GA_ReadOnly)

    # get image dimensions
    n_rows = ds.RasterYSize
    n_cols = ds.RasterXSize
       
    # find southern latitude limits, in case we need Antarctica.
    lats = ds.ReadAsArray().astype(np.float32)
    lat_min = np.nanmin(lats)
    lat = None

    logger.debug(f'Minimum latitude: {lat_min}')

    # clean up
    del ds

# -------------------------------------------------------------------------- #

    # read lat, lon
    lat = gdal.Open(lat_path.as_posix()).ReadAsArray()
    lon = gdal.Open(lon_path.as_posix()).ReadAsArray()

    # get GCPs from lat lon bands
    gcp_list, tie_point_WKT = geo_utils.get_tie_points_from_lat_lon(
        lat,
        lon,
        tie_points = tie_points,
        loglevel = loglevel
    )

# -------------------------------------------------------------------------- #

    # create initial mask image of correct size
    # create white image (ones) and later fill land polygons to zero
    mask = Image.new('L', (n_cols, n_rows), 1)


    # create output file dummy
    driver = gdal.GetDriverByName('Envi')
    driver.Register()
    dsOut = driver.Create(output_path.as_posix(), n_cols, n_rows, 1, gdal.GDT_Byte)
    band = dsOut.GetRasterBand(1)
    band.WriteArray(np.array(mask).astype(bool))

    dsOut.SetGCPs(gcp_list, tie_point_WKT)
    dsOut.FlushCache()

    # close and clean up
    del band

# -------------------------------------------------------------------------- #

    # create coordinate transformation from image coords to lat/lon
    tr = gdal.Transformer(dsOut, None, ['METHOD=GCP_POLYNOMIAL'])

    logger.info('Masking from input shapefile')
    logger.info('Current version assumes land polygons in shapefile')
    logger.info('Resulting mask will be: water=1, land=0')

# -------------------------------------------------------------------------- #

    # open shapefile (assumes that polygons are in the first layer - true for OSM)
    shp = ogr.Open(shapefile_path.as_posix())
    layer = shp.GetLayer(0)
    n_features = layer.GetFeatureCount()

    logger.debug(f'found {n_features} features in shapefile')

    # loop through all land polygons
    points = []
    for i in range(n_features):
 
        if np.mod(i,10000) == 0:
            logger.debug(f'Processing feature {i} of {n_features}')

        # get current polygon
        feature = layer.GetFeature(i)
        geometry = feature.GetGeometryRef()
        ring = geometry.GetGeometryRef(0)
        n_points = ring.GetPointCount()

        # loop through polygon points and convert lat/lon to pixel coordinates
        points = []
        for idx, p in enumerate(ring.GetPoints()):
            # The trick is this line. The first 1 asks the transformer to do an
            # inverse transformation, so this is transforms lat/lon coords to pixel coords
            (success, point) = tr.TransformPoint(1, p[0], p[1], 0)
            if success:
                px = point[0]
                py = point[1]
                points.append((px, py))

        # Rasterize the polygon in image coordinates.
        # The polygon function requires at least two points.
        if len(points) > 2:
            # NB: given land masks=fill to zero, plus boundary zero.
            ImageDraw.Draw(mask).polygon(points, outline=0, fill=0)

# -------------------------------------------------------------------------- #

    # convert to a numpy array (not sure if this is necessary)
    mask = np.array(mask).astype(bool)

    # now re-do the output mask file, with new mask.
    # NB: geo-coding should already be embedded.
    band = dsOut.GetRasterBand(1)
    band.WriteArray(mask)

    dsOut.SetGCPs(gcp_list, tie_point_WKT)
    dsOut.FlushCache()

    # Close and clean up
    del band

    del dsOut

    return

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# ---- End of <landmask.py> ----
