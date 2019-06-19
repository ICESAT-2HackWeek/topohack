import rasterio as rio
from pyproj import Proj, transform

def subsetBBox(rast,proj_in,proj_out):

    # rasterio open data
    rB = rio.open(rast)
    # rasterio get bounding box
    [L,B,R,T] = rB.bounds

    if proj_in == proj_out:
        return L, R, T, B
    else:
        incord = Proj(init=proj_in)
        outcord = Proj(init=proj_out)

        [Left,Bottom] = transform(incord,outcord,L,B)
        [Right,Top] = transform(incord,outcord,R,T)
        return Left, Right, Top, Bottom
