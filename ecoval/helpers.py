import glob
import os
import warnings
import xarray as xr
def matchup_starting_point(ff, val_dir = None, sim_dir = None):
    valid_vars = [
        "temperature",
        "salinity",
        "oxygen",
        "phosphate",
        "silicate",
        "nitrate",
        "ammonium",
        "alkalinity",
        "ph",
        "chlorophyll",
        "co2flux",
        "pco2",
        "doc",
        "poc",
        "carbon",
        "benbio",
    ]
    if sim_dir is None:
        raise ValueError("sim_dir must be set")
    data_dir = val_dir
    with warnings.catch_warnings(record=True) as w:
        if data_dir is None:
            data_dir = "/data/proteus1/scratch/rwi/evaldata/data/"
        ds = xr.open_dataset(ff)
        lon_name = [x for x in ds.coords if "lon" in x]
        lat_name = [x for x in ds.coords if "lat" in x]
        lon = ds[lon_name[0]].values
        lat = ds[lat_name[0]].values
        lon_max = lon.max()
        lon_min = lon.min()
        lat_max = lat.max()
        lat_min = lat.min()

    global_grid = False
    if lon_max - lon_min > 350:
        global_grid = True
    if lat_max - lat_min > 170:
        global_grid = True
    if lon_max > 50:
        global_grid = True

    if global_grid:
        model_domain = "global"
    else:
        model_domain = "nws"            
    if global_grid:
        valid_points = list(set([x for x in glob.glob(data_dir + "/point/user/all/*")]))
    else:
        valid_points = list(set([x for x in glob.glob(data_dir + "/point/**/all/*")]))
    # extract directory base name
    valid_points = [os.path.basename(x) for x in valid_points]

    if global_grid:
        valid_surface = [os.path.basename(x) for x in glob.glob(data_dir + "/gridded/user/*")]
        valid_surface += [os.path.basename(x) for x in glob.glob(data_dir + "/gridded/global/*")]
    else:
        valid_surface = [os.path.basename(x) for x in glob.glob(data_dir + "/gridded/nws/*")]
        valid_surface += [os.path.basename(x) for x in glob.glob(data_dir + "/gridded/user/*")]
    
    # now do bottom
    valid_bottom = [os.path.basename(x) for x in glob.glob(data_dir + "/point/user/bottom/*")]
    if not global_grid:
        valid_bottom += [os.path.basename(x) for x in glob.glob(data_dir + "/point/nws/bottom/*")]
    valid_bottom = list(set(valid_bottom))
    #

    valid_benthic = [
        os.path.basename(x) for x in glob.glob(data_dir + "/point/nws/benthic/*")
    ]

    # restrict to valid_vars
    valid_surface = [x for x in valid_surface if x in valid_vars]
    valid_benthic = [x for x in valid_benthic if x in valid_vars]
    valid_bottom = [x for x in valid_bottom if x in valid_vars]
    valid_points = [x for x in valid_points if x in valid_vars]
    # now, convert this to an ecoval call
    valid_surface = [f"'{x}'" for x in valid_surface]
    valid_bottom = [f"'{x}'" for x in valid_bottom]
    valid_points = [f"'{x}'" for x in valid_points]
    valid_benthic = [f"'{x}'" for x in valid_benthic]

    lines = ["ecoval.matchup("]
    lines.append(f"folder = '{sim_dir}',")
    lines.append("cores = 6,")
    lines.append("start = 1999,")
    lines.append("end = 1999,")
    lines.append("surface_level = 'top',")
    lines.append(f"surface = {{'gridded': [{','.join(valid_surface)}],")
    lines.append(f"'point': [{','.join(valid_points)}]}},")
    lines.append(f"bottom = [{','.join(valid_bottom)}],")
    lines.append(f"benthic = [{','.join(valid_benthic)}])")
    # merge the lines into a single string
    lines = " ".join(lines)
    return lines

        # "/data/thaumus2/scratch/hpo/COMFORT/baseline_archerfull", cores = 6, start = 1999, end = 1999, surface_level = "top", bottom = [], benthic = [], surface = surface) 
