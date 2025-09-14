"""Main module."""

import geemap
import ee
import os
from whitebox_workflows import WbEnvironment
from IPython.display import display, HTML


class RoadFloodRiskMap(geemap.Map):
    """A class to represent a road flood risk map."""

    def __init__(
        self,
        basemap="SATELLITE",
        center=[40, -100],
        zoom=4,
        height="600px",
        add_google_map=False,
        verbose=False,
    ):
        """
        Initialize the RoadFloodRiskMap with map data.

        Args:
            basemap (str): The basemap to use. Default is "SATELLITE". Other options include "ROADMAP", "TERRAIN", "HYBRID", etc.
            center (list): The center of the map as a list of [latitude, longitude]. Default is [40, -100].
            zoom (int): The initial zoom level of the map. Default is 4.
            height (str): The height of the map in CSS units. Default is "600px".
            add_google_map (bool): Whether to add Google Maps basemap. Default is False.
            verbose (bool): Whether to print verbose output. Default is False.
        """
        geemap.ee_initialize()  # Initialize Earth Engine
        super().__init__(
            basemap=basemap,
            center=center,
            zoom=zoom,
            height=height,
            add_google_map=add_google_map,
        )
        self.wbe = WbEnvironment()
        self.wbe.verbose = verbose
        self.wbe.working_directory = (
            os.getcwd()
        )  # Set the working directory to the current directory

    def retrieve_alos_palsar_data_clip(
        self,
        region_of_interest: ee.Geometry,
        output_file_name: str | None = None,
        scale: int = 30,
    ):
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
        sarHh = (
            ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH")
            .filter(ee.Filter.date("2017-01-01", "2018-01-01"))
            .select("HH")
        )

        if output_file_name != None or output_file_name != "":
            try:
                geemap.ee_export_image(
                    sarHh.mean(),
                    filename=output_file_name + ".tif",
                    region=region_of_interest,
                    scale=scale,
                )
            except Exception as e:
                print(f"Error exporting image: {e}")

        return sarHh.mean().clip(region_of_interest)

    def retrieve_sentinel_1_data_clip(
        self,
        region_of_interest: ee.Geometry,
        output_file_name: str | None = None,
        scale: int = 30,
    ):
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
        sentinel1 = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            .filter(ee.Filter.date("2024-06-01", "2025-06-01"))
            .filter(ee.Filter.eq("resolution_meters", scale))
            .select("VH")
        )

        if output_file_name != None and output_file_name != "":
            try:
                geemap.ee_export_image(
                    sentinel1.mean(),
                    filename=output_file_name + ".tif",
                    region=region_of_interest,
                    scale=scale,
                )
            except Exception as e:
                print(f"Error exporting image: {e}")

        return sentinel1.mean().clip(region_of_interest)

    def perform_hydrological_analysis(self, input_dem_file: str):
        """
        Perform a hydrological analysis on the region of interest. If `output_file_name` is provided, the results will be saved to a file.

        Args:
            input_dem_file (str): The path to the input DEM file.
            output_file_name (str): The name of the output file to save the results. If None, the results will not be saved to a file.

        Returns:
            filled_file_name (str): The filled DEM raster file name.
            d8_ptr_file_name (str): The D8 flow pointer raster file name.
            flow_accum_file_name (str): The flow accumulation raster file name.
        """
        # Retrieve DEM data
        dem = self.wbe.read_raster(input_dem_file)

        # Resolves all of the depressions in a DEM, outputting a breached DEM, an aspect-aligned non-divergent flow pointer, and a flow accumulation raster.

        filled, d8_ptr, flow_accum = self.wbe.flow_accum_full_workflow(
            dem=dem,
            out_type="sca",
            log_transform=True,
        )
        base_file = os.path.basename(input_dem_file)
        filled_file_name = f"filled_{base_file}"
        d8_ptr_file_name = f"d8_flow_{base_file}"
        flow_accum_file_name = f"flow_{base_file}"

        self.wbe.write_raster(filled, f"{filled_file_name}")
        self.wbe.write_raster(d8_ptr, f"{d8_ptr_file_name}")
        self.wbe.write_raster(flow_accum, f"{flow_accum_file_name}")

        return filled_file_name, d8_ptr_file_name, flow_accum_file_name

    def add_analyse_roi_widget(self):
        """
        Function to be run by widget to analyse the region of interest (ROI) for flood risk.

        Args:
            location (str): The location to check.

        Returns:
            None
        """
        from ipywidgets import Dropdown, VBox, HBox, Button, Layout, Text, Output
        from . import common

        data_source = [
            "Sentinel-1",
            "ALOS PALSAR",
        ]
        debug_view = Output(
            layout={
                "border": "1px solid black",
                "overflow_x": "auto",
                "width": "300px",
                "height": "150px",
            }
        )
        debug_view.add_class("wrap-output")
        display(
            HTML(
                """
        <style>
        .wrap-output {
            width: 300px; 
            height: 150px; 
            overflow-x: hidden;   /* disable horizontal scroll */
            overflow-y: auto;     /* enable vertical scroll */
        }
        .wrap-output pre {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }
        </style>
        """
            )
        )

        self.roi_name = Text(
            value="",
            placeholder="Enter file name",
            description="ROI Name:",
            disabled=True,
        )

        self.file_name = Text(
            value="",
            description="DEM File:",
            disabled=False,
        )

        self.dropdown = Dropdown(
            options=data_source,
            description="Data Source:",
            value="Sentinel-1",
            layout=Layout(width="auto", display="block"),
            disabled=True,
        )

        self.submit_button = Button(
            description="Submit",
            button_style="success",
            layout=Layout(width="auto", display="block"),
            disabled=True,
        )

        self.analyze_button = Button(
            description="Analyze DEM",
            button_style="success",
            layout=Layout(width="auto", display="block"),
            disabled=True,
        )

        @debug_view.capture(clear_output=True)
        def handle_submit(b):
            print("Submit button clicked.")
            print(f"Selected data source: {self.dropdown.value}")
            temp_file = f"temp_{self.roi_name.value}"
            img = None
            if self.dropdown.value == "Sentinel-1":
                img = self.retrieve_sentinel_1_data_clip(
                    self.user_roi, output_file_name=temp_file, scale=10
                )
            elif self.dropdown.value == "ALOS PALSAR":
                img = self.retrieve_alos_palsar_data_clip(
                    self.user_roi, output_file_name=temp_file, scale=30
                )

            self.add_ee_layer(img, name=f"{self.dropdown.value} Image")
            temp_file = f"{os.path.join(os.getcwd(),temp_file)}.tif"
            if temp_file != "" and os.path.isfile(temp_file):
                # Fix for unsupported compression method when opening raster file in WBE
                print("Reinstating compression method for the file...")
                self.file_name.value = common.fix_raster_metadata(
                    temp_file, self.roi_name.value
                )
                self.file_name.disabled = False
                self.analyze_button.disabled = False
                print(f"Done. File ready for analysis: {self.file_name.value}")

        @debug_view.capture(clear_output=True)
        def handle_analyze(b):
            print("Analyze button clicked.")
            print(f"Processing File: {self.file_name.value}")
            filled, d8_ptr, flow_accum = self.perform_hydrological_analysis(
                self.file_name.value
            )
            print("Hydrological analysis completed.")

            # Display results on the map
            self.add_raster(filled, layer_name="Filled DEM")
            self.add_raster(d8_ptr, layer_name="D8 Flow Pointer")
            self.add_raster(
                flow_accum, colormap="viridis", layer_name="Flow Accumulation"
            )

        def disable_widget(roi_count):
            if roi_count == 1:
                self.dropdown.disabled = False
                self.roi_name.disabled = False
                # self.submit_button.disabled = False
                print(
                    "Region of interest defined. You can now select a data source and enter a file name."
                )
            else:
                self.dropdown.disabled = True
                self.roi_name.disabled = True
                # self.submit_button.disabled = True
                print("Please define a single region of interest first.")

        def handle_roi_name_change(change):
            if change["new"] != "":
                self.submit_button.disabled = False
            else:
                self.submit_button.disabled = True

        def handle_file_name_change(change):
            if change["new"] != "" and os.path.isfile(self.file_name.value):
                self.analyze_button.disabled = False
            else:
                self.analyze_button.disabled = True

        @debug_view.capture(clear_output=True)
        def check_aoi(_, action, geo_json):
            print("Checking region of interest...")
            print(f"Action: {action}")
            roi_count = self.user_rois.size().getInfo()
            if action == "created":
                disable_widget(roi_count)
            elif action == "deleted":
                disable_widget(roi_count)

        def toggle_dropdown(b):
            if widget_vbox.layout.display == "none":
                widget_vbox.layout.display = "flex"
                btn.icon = "times"
            else:
                widget_vbox.layout.display = "none"
                btn.icon = "chevron-left"

        self.submit_button.on_click(handle_submit)
        self.analyze_button.on_click(handle_analyze)
        self.roi_name.observe(handle_roi_name_change, names="value")
        self.file_name.observe(handle_file_name_change, names="value")
        widget_vbox = VBox(
            [
                self.roi_name,
                self.dropdown,
                self.submit_button,
                debug_view,
                self.file_name,
                self.analyze_button,
            ],
            Layout={"overflow_x": "auto", "width": "300px", "height": "150px"},
        )
        btn = Button(
            icon="times",
            button_style="primary",
            layout=Layout(width="35px", height="35px"),
        )
        btn.on_click(toggle_dropdown)
        widget_hbox = HBox([widget_vbox, btn], layout=Layout(width="auto"))
        self.add_widget(widget_hbox)
        self.draw_control.on_draw(check_aoi)
