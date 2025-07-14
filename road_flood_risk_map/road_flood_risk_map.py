"""Main module."""
import geemap
import ee
import os
from whitebox_workflows import WbEnvironment

class RoadFloodRiskMap(geemap.Map):
    """A class to represent a road flood risk map."""

    def __init__(self, center= [40, -100], zoom= 4, height= "600px", add_google_map= False, verbose= False):
        """
        Initialize the RoadFloodRiskMap with map data.

        Args:
            center (list): The center of the map as a list of [latitude, longitude]. Default is [40, -100].
            zoom (int): The initial zoom level of the map. Default is 4.
            height (str): The height of the map in CSS units. Default is "600px".
            add_google_map (bool): Whether to add Google Maps basemap. Default is False.
            verbose (bool): Whether to print verbose output. Default is False.
        """
        geemap.ee_initialize()  # Initialize Earth Engine
        super().__init__(center=center, zoom=zoom, height=height, add_google_map=add_google_map)
        self.wbe = WbEnvironment()
        self.wbe.verbose = verbose
        self.wbe.working_directory = os.getcwd()  # Set the working directory to the current directory

    def retrieve_alos_palsar_data_clip(self, region_of_interest: ee.Geometry, output_file_name: str | None=None, scale: int=30):
        """
        Retrieve ALOS PALSAR data clipped to a region of interest. If `output_file_name` is provided, the data will be saved to a file.

        Args:
            region_of_interest (Geometry.BBox): The region to clip the ALOS PALSAR data to. It follows the following format: `ee.Geometry.BBox(west, south, east, north)`. **west** The westernmost enclosed longitude. Will be adjusted to lie in the range -180° to 180°. **south** The southernmost enclosed latitude. If less than -90° (south pole), will be treated as -90°. **east** The easternmost enclosed longitude. **north** The northernmost enclosed latitude. If greater than +90° (north pole), will be treated as +90°.
            output_file_name (str | None): The name of the output file to save the data. If None, the data will not be saved to a file.
            scale (int): The scale in meters at which to export the image. Default is 30.

        Returns:
            image: The ALOS PALSAR data clipped to the region of interest.
        """
        # Placeholder for actual data retrieval logic
        sarHh = ee.ImageCollection('JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH').filter(ee.Filter.date('2017-01-01', '2018-01-01')).select('HH')

        if output_file_name != None or output_file_name != '':
            try:
                geemap.ee_export_image(sarHh.mean(), filename=output_file_name+'.tif', region=region_of_interest, scale=scale)
            except Exception as e:
                print(f"Error exporting image: {e}")

        return sarHh.mean().clip(region_of_interest)
    
    def retrieve_sentinel_1_data_clip(self, region_of_interest: ee.Geometry, output_file_name: str | None=None, scale: int=30):
        """
        Retrieve Sentinel-1 data clipped to a region of interest. If `output_file_name` is provided, the data will be saved to a file.

        Args:
            region_of_interest (Geometry.BBox): The region to clip the Sentinel-1 data to. It follows the following format: `ee.Geometry.BBox(west, south, east, north)`. **west** The westernmost enclosed longitude. Will be adjusted to lie in the range -180° to 180°. **south** The southernmost enclosed latitude. If less than -90° (south pole), will be treated as -90°. **east** The easternmost enclosed longitude. **north** The northernmost enclosed latitude. If greater than +90° (north pole), will be treated as +90°.
            output_file_name (str | None): The name of the output file to save the data. If None, the data will not be saved to a file.
            scale (int): The scale in meters at which to export the image. Default is 30.

        Returns:
            image: The Sentinel-1 data clipped to the region of interest.
        """
        # Placeholder for actual data retrieval logic
        sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')).filter(ee.Filter.date('2024-01-01', '2024-12-31')).filter(ee.Filter.eq('resolution_meters', 10)).select('VH')

        if output_file_name != None and output_file_name != '':
            try:
                geemap.ee_export_image(sentinel1.mean(), filename=output_file_name+'.tif', region=region_of_interest, scale=scale)
            except Exception as e:
                print(f"Error exporting image: {e}")

        return sentinel1.mean().clip(region_of_interest)

    def perform_hydrological_analysis(self, input_dem_file: str, output_file_name: str):
        """
        Perform a hydrological analysis on the region of interest. If `output_file_name` is provided, the results will be saved to a file.

        Args:
            input_dem_file (str): The path to the input DEM file.
            output_file_name (str): The name of the output file to save the results. If None, the results will not be saved to a file.

        Returns:
            image: The results of the hydrological analysis.
        """
        # Retrieve DEM data
        dem = self.wbe.read_raster(input_dem_file)
        # Smooth the DEM(Optional depending on the input DEM quality)
        dem = self.wbe.feature_preserving_smoothing(dem, filter_size=9)

        # Generate Hillshade from DEM
        hillshade = self.wbe.multidirectional_hillshade(dem)

        # Fill depressions
        #wbt.fill_depressions(input_dem_file, output_file_name+'_filled.tif')
        # or Breach depression
        dem_filled = self.wbe.breach_depressions_least_cost(dem)
        dem_filled = self.wbe.fill_depressions(dem_filled)

        # Delineate flow direction
        d8_dem = self.wbe.d8_pointer(dem_filled)

        # Calculate flow accumulation
        flow_accum = self.wbe.d8_flow_accum(dem_filled)

        return d8_dem, flow_accum

    def get_risk_level(self, location):
        """
        Get the flood risk level for a specific location.

        Args:
            location (str): The location to check.

        Returns:
            str: The flood risk level for the location.
        """
        return self.map_data.get(location, "Unknown risk level")