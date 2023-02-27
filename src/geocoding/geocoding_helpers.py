# ---- This is <geocoding_utils.py> ----

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

def stack_geocoded_images(
    input_tif_path1,
    input_tif_path2,
    output_tif_path
):
    """Stack geocoded input images to combined multi-layer tiff file
       
    Parameters
    ----------
    input_tif_path1 : path to first input tiff file
    input_tif_path2 : path to second input tiff file
    output_tif_path: path to stacked output tiff file
    loglevel : loglevel setting (default='INFO')
    """ 

    gdal_cmd = f'gdal_merge.py ' + \
        f'-o {output_tif_path} ' + \
        f'-separate ' + \
        f'{input_tif_path1} ' + \
        f'{input_tif_path2} '

    logger.info(f'Running gdal_merge.py to stack input bands to combined tiff file')
    logger.info(f'Executing: {gdal_cmd}')

    os.system(gdal_cmd)
    
    return

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def warp_image_to_target_projection(
    input_img_path,
    output_tif_path,
    target_epsg,
    pixel_spacing,
    srcnodata = 0,
    dstnodata = 0,
    resampling = 'near',
    order = 3,
    loglevel='INFO'
):
    """Warp input image to target projection (epsg) using gdalwarp
       
    Parameters
    ----------
    input_img_path : path to input image file with embedded gcps
    output_tif_path: path to output geo-coded image file (tif format)
    target_epsg : output epsg code
    pixel_spacing : output pixel spacing in units of the target projection
    srcnodata : source no data value (default=0), set to None to avoid
    dstnodata : output no data value (default=0), set to None to avoid
    resampling : resampling method to use for gdalwarp (default='near')
    order: order of polynomial used for gdalwarp (default=3)
    loglevel : loglevel setting (default='INFO')
    """ 

    # gdalwarp command to project the input image and save output tif to output_tif_path
    if srcnodata == None and dstnodata == None:
        logger.debug('Nodata values set to None')
        gdal_cmd = f'gdalwarp ' + \
            f'-overwrite ' + \
            f'-t_srs epsg:{target_epsg} ' + \
            f'-tr {pixel_spacing} {pixel_spacing} ' + \
            f'-r {resampling} ' + \
            f'-order {order} ' + \
            f'{input_img_path} {output_tif_path}'

    else:
        logger.debug(f'Nodata values set to {srcnodata} and {dstnodata}')
        gdal_cmd = f'gdalwarp ' + \
            f'-overwrite -srcnodata {srcnodata} -dstnodata {dstnodata} ' + \
            f'-t_srs epsg:{target_epsg} ' + \
            f'-tr {pixel_spacing} {pixel_spacing} ' + \
            f'-r {resampling} ' + \
            f'-order {order} ' + \
            f'{input_img_path} {output_tif_path}'

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

def get_tie_points_from_S1_product(
    safe_folder,
    loglevel='INFO'
):

    """Get tie-point grid from original S1 product

    Parameters
    ----------
    safe_folder : path to S1 image SAFE folder
    loglevel : loglevel setting (default='INFO')

    Returns
    -------
    gcps : list of tie points
    tie_point_WKT : tie-point well-known text projection
    """

    # remove default logger handler and add personal one
    logger.remove()
    logger.add(sys.stderr, level=loglevel)

    logger.info('Getting tie points (GCPs) from S1 manifest.safe')

# -------------------------------------------------------------------------- #

    # convert folder strings to paths
    safe_folder = pathlib.Path(safe_folder).expanduser().absolute()

    logger.debug(f'safe_folder: {safe_folder}')

    if not safe_folder.is_dir():
        logger.error(f'Cannot find Sentinel-1 SAFE folder: {safe_folder}')
        raise NotADirectoryError(f'Cannot find Sentinel-1 SAFE folder: {safe_folder}')

# -------------------------------------------------------------------------- #

    # build path to manifest.safe file
    safe_path = safe_folder / 'manifest.safe'

    # open manifest.sate
    geo = gdal.Open(safe_path.as_posix())

    # get gcps from safe file
    gcps = geo.GetGCPs()

    # make WKT at this time too
    srs, tie_point_WKT = create_srs_and_WKT()

    return (gcps, tie_point_WKT)

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


    # make WKT at this time too
    srs, tie_point_WKT = create_srs_and_WKT()

    return (gcps, tie_point_WKT)

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

def embed_tie_points_in_array_to_tiff(
    input_array,
    gcp_list,
    output_tif_path,
    tie_point_WKT,
    loglevel='INFO'
):

    """Embed gcps into feature (array) and write to geotiff

    Parameters
    ----------
    input_array : array containing the image data to be geo-refenced (bands, lines, samples))
    gcp_list: list with gcps
    output_tif_path : path to output geotif file with embedded gcps
    tie_point_WKT : srs.ExportToWkt(), srs: spatial reference system object
    loglevel : loglevel setting (default='INFO')
    """

    # remove default logger handler and add personal one
    logger.remove()
    logger.add(sys.stderr, level=loglevel)

    logger.info('Embedding tie points (GCPs) into input array')

# -------------------------------------------------------------------------- #

    # get dims and data type of input_array
    if len(input_array.shape) == 2:
        lines, samples = input_array.shape
        bands = 1
    elif len(input_array.shape) == 3:
        bands, lines, samples = input_array.shape
    else:
        logger.error('input_array.shape must be (lines,samples) or (bands,lines,samples)')

    data_type_in = gdal_array.NumericTypeCodeToGDALTypeCode(input_array.dtype.type)
    
    logger.debug(f'bands: {bands}, lines: {lines}, samples: {samples}')
    logger.debug(f'data_type_in: {data_type_in}')

    if bands > lines or bands > samples:
        logger.error('Number of bands is larger than image dimensions')
        logger.error('input_array.shape must be (lines,samples) or (bands,lines,samples)')
        

    # initialize new GTiff file for output
    GTdriver = gdal.GetDriverByName('GTiff')
    out = GTdriver.Create(
      output_tif_path,
      samples,
      lines,
      bands,
      data_type_in
    )


    # write input_array to tiff file
    if bands == 1:
        band_out = out.GetRasterBand(1)
        band_out.WriteArray(input_array)
        band_out.FlushCache()
    elif bands > 1:
        for b in range(1,bands+1):
            band_out = out.GetRasterBand(b)
            band_out.WriteArray(input_array[b-1,:,:])
            band_out.FlushCache()

    # embed the tie_points
    out.SetGCPs(gcp_list, tie_point_WKT) # or srs.ExportToWkt() for second argument
    out.FlushCache()
    del out
    
    return

# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #

# ---- End of <geocoding_utils.py> ----
