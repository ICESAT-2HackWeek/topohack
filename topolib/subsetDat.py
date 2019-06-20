import rasterio as rio
from pyproj import Proj, transform
import xarray as xr
import h5py

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
        return Left, Bottom, Right, Top

def subSetDatQual(fname,varname,dat_metric,upper,lower):
    
    # we talked about making this a function output....
    group = ['/gt1l', '/gt1r', '/gt2l', '/gt2r', '/gt3l', '/gt3r']
    
    # for the case where we have multiple files
    for f in fname:
        # for each group
        for g in group:
         # I would actually consider this a groupname?? maybe also import
            for h in varname:
                # port into an xarray
                temp = xr.open_dataset(f,group=g+h)
                
                # if the first, instantiate xarray dataframe
                if g == group[0]:
                    dSet = temp
                # otherwise 
                else:
                    dSet = xr.merge([temp,dSet])
     
    # if only filtering by a single value (e.g. data quality flag)
    if upper == lower:
        dSet = dSet.where(dSet[dat_metric] != upper,drop=True)
    else
        dSet = dSet.where(dSet[dat_metric] < upper,drop=True)
        dSet = dSet.where(dSet[dat_metric] > lower,drop=True)

    return dSet