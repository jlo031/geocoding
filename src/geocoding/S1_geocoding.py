# ---- This is <S1_geocoding.py> ----

"""
Module for geocoding of S1 images
"""

import argparse
import os
import sys
import pathlib
import shutil

from loguru import logger

import numpy as np

from osgeo import gdal, osr, gdal_array

import geocoding.geocoding_utils as geo_utils

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def geocode_S1_image_from_safe_gcps(
    img_path,
    safe_folder,
    output_tiff_path,
    target_epsg,
    pixel_spacing,
    srcnodata = 0,
    dstnodata = 0,
    order = 3,
    resampling = 'near',
    keep_gcp_file = False,
    overwrite = False,
    loglevel = 'INFO',
):

    """Geocode image using GCPS extracted from lat/lon bands

    Parameters
    ----------
    img_path : path to input image file (feature, labels, etc)
    safe_folder : path to S1 image SAFE folder
    output_tiff_path : path to geocoded output tiff file
    target_epsg : output epsg code
    pixel_spacing : output pixel spacing in units of the target projection
    srcnodata : source no data value (default=0), set to None to avoid
    dstnodata : output no data value (default=0), set to None to avoid
    order : order of polynomial used for gdalwarp (default=3)
    resampling : resampling method to use for gdalwarp(default='near')
    keep_gcp_file : keeo temporary file with embedded GCPs (default=False)
    overwrite : overwrite existing files (default=False)
    loglevel : loglevel setting (default='INFO')
    """

    # remove default logger handler and add personal one
    logger.remove()
    logger.add(sys.stderr, level=loglevel)

    logger.info('Geocoding input image using GCPs from S1 SAFE')

# -------------------------------------------------------------------------- #

    # convert folder/file strings to paths
    img_path         = pathlib.Path(img_path).expanduser().absolute()
    safe_folder      = pathlib.Path(safe_folder).expanduser().absolute()
    output_tiff_path = pathlib.Path(output_tiff_path).expanduser().absolute()

    logger.debug(f'img_path:         {img_path}')
    logger.debug(f'safe_folder:      {safe_folder}')
    logger.debug(f'output_tiff_path: {output_tiff_path}')

    if not img_path.is_file():
        logger.error(f'Cannot find img_path: {img_path}')
        raise FileNotFoundError(f'Cannot find img_path: {img_path}')

    if not safe_folder.is_dir():
        logger.error(f'Cannot find Sentinel-1 SAFE folder: {safe_folder}')
        raise NotADirectoryError(f'Cannot find Sentinel-1 SAFE folder: {safe_folder}')


    # check if outfile already exists
    if output_tiff_path.is_file() and not overwrite:
        logger.info('Output file already exists, use `-overwrite` to force')
        return
    elif output_tiff_path.is_file() and overwrite:
        logger.info('Removing existing output file')
        output_tiff_path.unlink()


    logger.debug(f'target_epsg:   {target_epsg}')
    logger.debug(f'pixel_spacing: {pixel_spacing}')
    logger.debug(f'order:         {order}')
    logger.debug(f'resampling:    {resampling}')
    logger.debug(f'srcnodata:     {srcnodata}')
    logger.debug(f'dstnodata:     {dstnodata}')

# -------------------------------------------------------------------------- #

    # read img
    img = gdal.Open(img_path.as_posix()).ReadAsArray()

    # set temporary path for tiff file with GCPs (and remove if it exists
    tiff_path_with_gcps = output_tiff_path.parent / f'{output_tiff_path.stem}_with_gcps.tiff'
    logger.debug(f'tiff_path_with_gcps: {tiff_path_with_gcps}')
    if tiff_path_with_gcps.is_file():
        logger.debug(f'Removing existing tiff_path_with_gcps')
        tiff_path_with_gcps.unlink()

    # create output dir (if needed)
    output_tiff_path.parent.mkdir(parents=True, exist_ok=True)

    # get GCPs from safe_folder
    gcp_list, tie_point_WKT = geo_utils.get_tie_points_from_S1_product(
        safe_folder.as_posix(),
        loglevel = loglevel
    )

    # embed GCPs into img and write to tiff
    geo_utils.embed_tie_points_in_array_to_tiff(
        img,
        gcp_list,
        tiff_path_with_gcps.as_posix(),
        tie_point_WKT,
        loglevel = loglevel
    )

    # warp to final projection
    geo_utils.warp_image_to_target_projection(
        tiff_path_with_gcps.as_posix(),
        output_tiff_path.as_posix(),
        target_epsg,
        pixel_spacing,
        srcnodata = srcnodata,
        dstnodata = dstnodata,
        resampling = resampling,
        order = order,
    )

    # clean up
    if keep_gcp_file:
        logger.info('Keeping temporary tiff file with embedded GCPs')
    else:
        tiff_path_with_gcps.unlink()

    return

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #


info = 'THIS MODULE IS CURRENTLY UNDER DEVELOPMENT. STAY TUNED FOR UPDATES'

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# ---- End of <S1_geocoding.py> ----
