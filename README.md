# topohack
Taking ICESat-2 to the mountains: a workflow using satellite laser altimetry to resolve topography over complex terrain  

### Data Science Objective
Compare and evaluate ICESat-2 data with airborne lidar data collected at lower latitudes over bare ground. 

### Datasets
- ICESat-2 ATL06 (20 m resolution)
- ICESat-2 ATL03 (geolocated points along track)

### Validation Datasets
- [WADNR Lidar](http://lidarportal.dnr.wa.gov/)

### Tools
- Python: geopandas, rasterio, demcoreg
- [NASA Ames Stereo Pipeline](https://github.com/NeoGeographyToolkit/StereoPipeline)

### Tasks
- Learn how to download the ICESat-2 data by lat lon bounding box
- Explore ATL03 and ATL06 products
- Learn how to subset ATL03 and ATL06 data based on flags
- Intersect ICESat-2 tracks with [RGI glacier polygons](https://www.glims.org/RGI/) to get a sense of bare ground coverage near glaciers.
- Evaluate accuracy of ICESat-2 products against airborne lidar. 

### Other Questions 
Are notebooks available that show how the comparison between IceBridge lidar and ICESat-2 tracks was done?
