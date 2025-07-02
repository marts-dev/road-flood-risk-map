"""Main module."""
import geemap
import ee

class RoadFloodRiskMap(geemap.Map):
    """A class to represent a road flood risk map."""

    def __init__(self, center= [40, -100], zoom= 4, height= "600px", add_google_map= False):
        """
        Initialize the RoadFloodRiskMap with map data.

        Args:
            center (list): The center of the map as a list of [latitude, longitude]. Default is [40, -100].
            zoom (int): The initial zoom level of the map. Default is 4.
            height (str): The height of the map in CSS units. Default is "600px".
            add_google_map (bool): Whether to add Google Maps basemap. Default is False.
        """
        geemap.ee_initialize()  # Initialize Earth Engine
        super().__init__(center=center, zoom=zoom, height=height, add_google_map=add_google_map)

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
        sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')).filter(ee.Filter.date('2024-01-01', '2024-12-31')).select('VH')

        if output_file_name != None or output_file_name != '':
            try:
                geemap.ee_export_image(sentinel1.mean(), filename=output_file_name+'.tif', region=region_of_interest, scale=scale)
            except Exception as e:
                print(f"Error exporting image: {e}")

        return sentinel1.mean().clip(region_of_interest)

    def get_risk_level(self, location):
        """
        Get the flood risk level for a specific location.

        Args:
            location (str): The location to check.

        Returns:
            str: The flood risk level for the location.
        """
        return self.map_data.get(location, "Unknown risk level")