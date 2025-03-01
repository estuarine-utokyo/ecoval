
# %% [markdown] tags=["remove-cell"]
# ## Read in the data

# %% tags=["remove-input", "remove-cell"]
ff = glob.glob(f"../../matched/point/**/{layer}/{variable}/*_{variable}.csv")[0]
vv_source = os.path.basename(ff).split("_")[0]
vv_source = vv_source.upper()
df = pd.read_csv(ff)
ff_dict = f"../../matched/point/nws/{layer}/{variable}/matchup_dict.pkl"
point_time_res = ["year", "month", "day"]
try:
    with open(ff_dict, "rb") as f:
        matchup_dict = pickle.load(f)
        min_year = matchup_dict["start"]
        max_year = matchup_dict["end"]
        point_time_res = matchup_dict["point_time_res"]
except:
    pass

if layer_select == "surface":
    try:
        df = df.query("depth < 5").reset_index()
    except:
        pass
else:
    if layer != "bottom":
        df = df.query("bottom > 0").reset_index().drop(columns = "bottom")
    else:
        if "bottom" in df.columns:
            df = df.drop(columns = "bottom")

if variable == "ph":
    df = df.query("observation > 4").reset_index(drop = True)
# Danish part is always dubious
df = df.query("lon < 9")
df_locs = df.loc[:,["lon", "lat"]].drop_duplicates()
# bin to 0.01 resolution
df_raw = copy.deepcopy(df)
if variable == "benbio":
    df = df.assign(observation = lambda x: 1000 * 0.45 * x.observation) 
if variable not in  ["carbon", "benbio", "susfrac", "oxycons"]:
    if "year" in point_time_res:
        df = df.groupby(["lon", "lat", "year", "month"]).mean().reset_index()
    else:
        df = df.groupby(["lon", "lat",  "month"]).mean().reset_index()
else:
    df = df.groupby(["lon", "lat"]).mean().reset_index()

# %% tags=["remove-input"]
if layer == "all":
    ff = "../../matched/model_bathymetry.nc"
    import nctoolkit as nc
    ds_coords = nc.open_data(ff)
    ds_coords.assign(lon_model = lambda x: lon(x.e3t), lat_model = lambda x: lat(x.e3t))
    ds_coords.drop(variables = "e3t")
    ds_coords.run()
    ds_coords.regrid(df_raw.loc[:,["lon", "lat"]].drop_duplicates(), method = "nearest")
    df_coords = ds_coords.to_dataframe().reset_index()
    df = df.merge(df_coords, on = ["lon", "lat"], how = "left")
    if variable not in  ["carbon", "benbio", "susfrac", "oxycons"]:
        df = df.groupby(["lon_model", "lat_model", "year", "month"]).mean().reset_index()
    else:
        df = df.groupby(["lon_model", "lat_model"]).mean().reset_index()
    # drop lon/lat
    df = df.drop(columns = ["lon", "lat"])
    df = df.rename(columns = {"lon_model": "lon", "lat_model": "lat"})
    # only the surface top 5 m


# %% tags=["remove-input", "remove-cell"]
# A function for generating the data source

def data_source(vv_source, vv_name):
    if vv_name.lower() == "carbon":
        return "Diesing et al. (2021)"
    if vv_source == "NSBS":
        return "the North Sea Benthos Survey (1986)"
    if vv_source == "NSBS":
        return "the North Sea Benthos Survey (1986)"
    return vv_source


# %% tags=["remove-input"]
intro = []

if vv_source == "ICES": 

    if layer_select == "bottom":
        intro.append(f"Near-bottom values of {vv_name} were extracted from International Council for the Exploration of the Sea (ICES) bottle and CTD data.")
    if layer_select in ["surface", "all"]:
        if layer not in ["benthic"]:
            intro.append(f"Values from the **top 5 m** of the water column were extracted from International Council for the Exploration of the Sea (ICES) bottle and CTD data.")
    if layer == "benthic":
        intro.append("Benthic values were extracted from existing datasets")
else:
    if layer_select == "bottom":
        intro.append(f"This data was extracted from vertical profiles. The near-bottom value was defined as the value closest to the bottom, that was within 5 m of the bottom. Bathymetry was estimated using GEBCO Bathymetry data.")
    if layer_select == "surface":
        if layer not in ["benthic"]:
            intro.append(f"This data was extracted from vertical profiles. Values from the **top 5 m** were extracted from the database. This was compared with the model values from the surface level.")
    if variable in ["benbio"]:
        intro.append("Biomass data for macrobenthos was downloaded from the North Sea Benthos Survey 1986.")
    if variable in ["susfrac"]:
        intro.append("Abundance data for macrobenthos was downloaded from the North Sea Benthos Survey 1986. It was than converted to biomass using [traitfinder](https://github.com/pmlmodelling/traitfinder) biomasses.")

if variable in ["carbon"]:
    intro.append("Carbon data was compiled from multiple sources")

if layer_select == "bottom":
    intro.append("**Note:** this analysis has been restricted to observations on the shelf region.")


if variable == "poc":
    intro.append("Particulate organic carbon data was compiled from multiple sources")

if variable == "pco2":
    intro.append("The variable pCO2water_SST_wet was extracted from the SOCAT 2023 database.")
    intro.append("Observational values were averaged for each day in the year.")

if variable == "doc":
    intro.append("Dissolved organic carbon data was compiled from multiple sources")

df_mapping = pd.read_csv("../../matched/mapping.csv")
model_variable = list(df_mapping.query("variable == @variable").model_variable)[0]

import pickle
try:
    ff_dict = f"../../matched/point/nws/{layer}/{variable}/matchup_dict.pkl"
    with open(ff_dict, "rb") as f:
        matchup_dict = pickle.load(f)
        min_year = matchup_dict["start"]
        max_year = matchup_dict["end"]
        point_time_res = matchup_dict["point_time_res"]

    if min_year == max_year:
        intro.append(f"The model output was matched up with the observational data with model output from  the year **{min_year}**.")
    else:
        intro.append(f"The model output was matched up with the observational data with model output from the years **{min_year} to {max_year}**.")
    
    if point_time_res == ["year", "month", "day"]:
        intro.append(f"The model output was matched up precisely with the observational data for each day of the year in the years with data in both model and observations.")
    if point_time_res == ["month", "day"]:
        intro.append(f"The model output was matched up with the observational data for each day of the year. However, the year in the observational data was not considered, so the comparison is climatological.")
    if point_time_res == ["month"]:
        intro.append(f"The model output was matched up with the observational data for each month of the year. However, the year and day of month in the observational data was not considered, so the comparison is climatological.")
    
    
except:
    if "year" in df_raw.columns:
        min_year = df_raw.year.min()
        max_year = df_raw.year.max()
    if min_year == max_year:
        intro.append(f"The model output was matched up with the observational data for the year **{min_year}**.")
    else:
        intro.append(f"The model output was matched up with the observational data for the years **{min_year} to {max_year}**.")



md(" ".join(intro).strip().replace("  ", " "))

md(f"In total there were {len(df_raw)} values extracted from the observational database. The map below shows the locations of the matched up data for {vv_name}.")
md_markdown(f"The following model output was used to compare with observational values: **{model_variable}**.")

# %% tags=["remove-cell"]
# bottom 1% of observations
bot_low = df.observation.quantile(0.001)
df = df.query(f"observation >= {bot_low}")

# %% tags=["remove-input"]
# %%capture --no-display
# %%R -i df_locs -i variable -i unit -w 500
library(dplyr, warn.conflicts = FALSE)
library(ggplot2, warn.conflicts = FALSE)
library(stringr)
world_map <- map_data("world")
# get lon, lat limits from profile_mld

xlim = c(min(df_locs$lon), max(df_locs$lon))
ylim = c(min(df_locs$lat), max(df_locs$lat))



if(variable == "temperature"){
    if(str_detect(unit, "C"))
     unit = "°C"
}



gg <- df_locs %>%
# final six months of the year
    ggplot()+
    geom_point(aes(lon, lat))+
    theme_gray(base_size = 14)+
    # add colour scale. Minimum zero, label 100, ">100"
    geom_polygon(data = world_map, aes(long, lat, group = group), fill = "grey60")+
    coord_fixed(xlim = xlim, ylim = ylim, ratio = 1.5) 

# figure out if lon minimum is less than -10
if( min(df_locs$lon) < -10 ){
    # add sensible labels for longitude and latitude

    gg <- gg +
    scale_x_continuous(breaks = seq(-15, 5, 5), labels = c("15°W", "10°W","5°W", "0°", "5°E"))+ 
    scale_y_continuous(breaks = seq(45, 60, 5), labels = c("45°N", "50°N", "55°N", "60°N"))+
    labs(x = "", y = "") 


}

    # move legen

gg

# %% tags=["remove-input"]
if layer_select == "surface":
    if layer not in ["benthic"]:
        md(f"**Figure {chapter}{i_figure}:** Locations of matchups between simulated and observed {vv_name} in the top 5 m of the water column.") 
if layer_select == "bottom":
    md(f"**Figure {chapter}{i_figure}:** Locations of matchups between simulated and observed {vv_name} near the bottom of the water column.")
if layer_select == "all":
    if layer not in ["benthic"]:
        md(f"**Figure {chapter}{i_figure}:** Locations of matchups between simulated and observed {vv_name} throughout the water column.")
if layer == "benthic":
    md(f"**Figure {chapter}{i_figure}:** Locations of matchups between simulated and observed {vv_name} on the seafloor. The observational data is from {data_source(vv_source, vv_name)}.")    
i_figure = i_figure + 1

# %% tags=["remove-input"]
# %%capture --no-display
# %%R -i df -i variable -i unit -i layer_select -i vv_name -w 500 
options(warn=-1)
options(warn=-1)
library(tidyverse)
library(ggtext)

if (("month" %in% colnames(df)) == FALSE){

df_map <- df %>%
    gather(variable, value, model:observation)
    df_map
# calculate the 98th percentil of the data
p98 = quantile(df_map$value, 0.98)
# cap the value at this
df_map$value = pmin(df_map$value, p98)

world_map <- map_data("world")


if(variable == "temperature"){
    if(str_detect(unit, "C"))
     unit = "°C"
}


Layer <- str_to_title(layer_select)
name <- str_glue("{Layer} {vv_name} ({unit})")
# ensure everything is superscripted where necessary
# m-3 should be superscripted
# Note: this is for ggplot2
name <- str_replace_all(name, "m-([0-9]+)", "m<sup>-\\1</sup>")
name = str_replace(name, "/m\\^2", "m<sup>-2")


gg <- df_map %>%
    ggplot()+
    geom_tile(aes(lon, lat, fill = value))+
    theme_gray(base_size = 14)+
    coord_fixed(ratio = 1.5, xlim = c(min(df$lon), max(df$lon)), ylim = c(min(df$lat), max(df$lat)))+
    labs(color = variable)+
    # log10
    scale_color_viridis_c()+
    theme(legend.position = "bottom", legend.title = element_markdown())  +
    facet_wrap(~variable)+
      scale_fill_viridis_c(
        # use unit for the label
        name = name,
                       guide = guide_colorbar(title.position = "bottom", title.hjust = 0.5, title.theme = element_markdown(angle = 0, size = 20, family = "Helvetica"))
  )+
    theme(

    legend.position = "bottom", legend.direction = "horizontal", legend.box = "horizontal", legend.key.width = unit(3.0, "cm"),
    legend.key.height = unit(1.0, "cm"))
    # use ggtext to ensure things are superscripted
    #theme(legend.title = element_markdown()) 



y_labels <-  as.numeric(na.omit(layer_scales(gg)$y$break_positions()))
x_labels <- as.numeric(na.omit(layer_scales(gg)$x$break_positions()))
x_breaks <- x_labels
y_breaks <- y_labels

# y labels are north-south coordinates. Make them more appropriate
# i.e. 10 should be 10 °N, -10 should be 10 °S

y_labels <- ifelse(y_labels >= 0, paste0(y_labels, "°N"), paste0(abs(y_labels), "°S"))
x_labels <- ifelse(x_labels >= 0, paste0(x_labels, "°E"), paste0(abs(x_labels), "°W"))

gg <- gg + scale_x_continuous(breaks = x_breaks, labels = x_labels) + scale_y_continuous(breaks = y_breaks, labels = y_labels)+
    geom_polygon(data = world_map, aes(long, lat, group = group), fill = "grey60")

# remove x and y axis names
gg <- gg +
    labs(x = "", y = "") 

# ditch the whitespace around the plot
gg <- gg + theme(plot.margin=unit(c(0,0,0,0),"cm"))
gg


}

# %% tags=["remove-input"]
if "month" not in df.columns:
    md(f"**Figure {chapter}{i_figure}:** Map of average {layer_select} {vv_name} in the model and observational datasets.")
    i_figure += 1

# %% tags=["remove-input"]
if "month" in df_raw.columns:
    # summarize using md the number of observations in each month
    # get the minimum and maximum number in each month and report the month
    df_size = df_raw.groupby("month").size().reset_index()
    df_size.columns = ["month", "n"]
    n_min = df_size.n.min()
    n_max = df_size.n.max()
    month_min = list(df_size.query("n == @n_min").month.values)[0]
    months_max = list(df_size.query("n == @n_max").month.values)[0] 
    # convert to month names
    import calendar
    month_min = calendar.month_name[int(month_min)]
    months_max = calendar.month_name[int(months_max)] 
    
    # summarize using md
    
    fig_summary = [f"The number of observations in each month ranged from {n_min} in {month_min} to {n_max} in {months_max}."]
    
    fig_summary.append(f"Figure {chapter}{i_figure} below shows the distribution of observations in each month.")
    
    md(" ".join(fig_summary).strip().replace("  ", " "))

if "month" in df_raw.columns:
    df_totals = (
        df_raw.groupby("month").size().reset_index()
        # rename
        .rename(columns = {0: "n"})
    )
else:
    df_totals = pd.DataFrame({"month": ["All"], "n": [len(df_raw)]})


# %% tags=["remove-input"]
# %%capture --no-display
# %%R -i df_totals -i variable -i unit -w 500 
# calculate number of observations per month
# figure out if "month" in df
if("month" %in% colnames(df_totals)){

df1 <- df_totals %>%
    rename(observation = n) %>%
    ungroup()   

# plot number of observations per month using plotnine and geom_bar

# change month to month name
df1$month <- factor(df1$month, levels = 1:12, labels = c("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))

gg <- df1 %>%
    ggplot(aes(x = month, y = observation))+
    theme_gray(base_size = 14)+
    geom_bar(stat = "identity")+
    labs(y = "Number of observations", x= "")

gg
}

# %% tags=["remove-input"]
if "month" in df.columns:
    md(f"**Figure {chapter}{i_figure}:** Number of {layer_select} observations per month for {vv_name}.")
    i_figure += 1

# %% tags=["remove-input"]
bias_text = []

bias_text.append(f"Figure {chapter}{i_figure} below shows the bias between the model and observational data for {vv_name}.")
bias_text.append(f"The bias is calculated as the model value minus the observational value, and it is shown for each month of the year.")

md(" ".join(bias_text).strip().replace("  ", " "))

# %% tags=["remove-input"]
# %%capture --no-display
# %%R -i df -i variable -i unit -i layer_select -w 1000 -h 1200 -i vv_name
options(warn=-1)
# #%%R -i df -i variable -i unit -w 1600 -h 1000
options(warn=-1)

library(dplyr, warn.conflicts = FALSE)
library(ggplot2, warn.conflicts = FALSE)
library(stringr)
library(tidyverse)
world_map <- map_data("world")
# get lon, lat limits from profile_mld

xlim = c(min(df$lon), max(df$lon))
ylim = c(min(df$lat), max(df$lat))


if(vv_name == "temperature"){
    if(str_detect(unit, "C"))
     unit = "°C"
}



df <- df %>%
    mutate(bias = model - observation) 

# calculate the absolate bias

df1 <- df %>%
    mutate(bias = abs(bias))
# calculate the 98th percentile of the absolute bias
bias_high <- df1$bias %>% quantile(0.98)
# cap the bias to +/1 98th percentile
df$bias[df$bias > bias_high] <- bias_high
df$bias[df$bias < -bias_high] <- -bias_high



plot_month <- FALSE
if("month" %in% colnames(df))
    plot_month <- TRUE

# # convert month number to month in profile_mld
if(plot_month){
    df <- df %>%
        arrange(month)
df$month <- factor(df$month, levels = df$month, labels = month.abb[df$month])
}
# df$month <- factor(df$month, labels = month.abb)

title <- str_glue("Bias in {layer_select} {vv_name} ({unit})")

out = str_glue("../../results/{layer_select}/{variable}/{layer_select}_{variable}_bias.csv")

# # check directory exists for out
if (!dir.exists(dirname(out))){
    dir.create(dirname(out), recursive = TRUE)
}
df %>% write_csv(out)

# df.to_csv(out, index = False)

# export to csv

title = str_replace(title, "/m\\^3", "m<sup>-3")
title = str_replace(title, "/m\\^2", "m<sup>-2")


title <- str_replace_all(title, "m-([0-9]+)", "m<sup>-\\1</sup>")


gg <- df %>%
# final six months of the year
    ggplot()+
    geom_point(aes(lon, lat, colour = bias))+
    theme_gray(base_size = 24)+
    # add colour scale. Minimum zero, label 100, ">100"
    coord_fixed(xlim = xlim, ylim = ylim, ratio = 1.5) +
    # move legend to the top. Make it 3 cm wide
    # move legend title to the bottom and centre it
    scale_colour_gradient2(low = "blue", high = "red",
    limits = c(-bias_high, bias_high),
                       guide = guide_colorbar(title.position = "bottom", title.hjust = 0.5, title.theme = ggtext::element_markdown(angle = 0, size = 20, family = "Helvetica"))
                    #    guide = guide_colorbar(title.position = "bottom", title.hjust = 0.5, title.theme = element_text(angle = 0, size = 20, family = "Helvetica"))
  )+
    theme(
    legend.position = "bottom", legend.direction = "horizontal", legend.box = "horizontal", legend.key.width = unit(6.0, "cm"),
    # legend.title = ggtext::element_markdown(),
    legend.key.height = unit(1.0, "cm"))+
    # set the legend title to bias
    labs(fill = title)
  #  .title.x = ggtext::element_markdown())

if (plot_month){
    #  option: figure out how many months are in the data
    # and wrap appropriately. this requires the w to be fixed in %%R. Not sure how to do this
    gg <- gg + facet_wrap(~month)
}


y_labels <-  as.numeric(na.omit(layer_scales(gg)$y$break_positions()))
x_labels <- as.numeric(na.omit(layer_scales(gg)$x$break_positions()))
x_breaks <- x_labels
y_breaks <- y_labels

# y labels are north-south coordinates. Make them more appropriate
# i.e. 10 should be 10 °N, -10 should be 10 °S

y_labels <- ifelse(y_labels >= 0, paste0(y_labels, "°N"), paste0(abs(y_labels), "°S"))
x_labels <- ifelse(x_labels >= 0, paste0(x_labels, "°E"), paste0(abs(x_labels), "°W"))

gg <- gg + scale_x_continuous(breaks = x_breaks, labels = x_labels) + scale_y_continuous(breaks = y_breaks, labels = y_labels)+
    geom_polygon(data = world_map, aes(long, lat, group = group), fill = "grey60")

gg <- gg +
    labs(x = "", y = "")

    # move legen

gg

# %% tags=["remove-input"]
if layer not in ["benthic"]:
    md(f"**Figure {chapter}{i_figure}**: Bias in {layer_select} {vv_name}. The bias is calculated as model - observation. The colour scale is from blue (negative bias) to red (positive bias). The colour scale is capped at the 98th percentile of the absolute bias. This is to avoid a few extreme outliers from dominating the colour scale. **Note:** values have been binned and averaged to the resolution of the model.") 
else:
    md(f"**Figure {chapter}{i_figure}**: Bias in {layer_select} {vv_name}. The bias is calculated as model - observation. The colour scale is from blue (negative bias) to red (positive bias). The colour scale is capped at the 98th percentile of the absolute bias. This is to avoid a few extreme outliers from dominating the colour scale.") 
i_figure += 1

#"adhoc/tmp/df_raw.feather"
# create directory if non-existent, recursive
if os.path.isdir("adhoc/tmp") == False:
    os.makedirs("adhoc/tmp")
df_raw.to_feather("adhoc/tmp/df_raw.feather")
df.to_feather("adhoc/tmp/df.feather")


# %% tags=["remove-input"]
scatter_text = []
scatter_text.append(f"Figures {chapter}{i_figure} and {chapter}{i_figure + 1} show the distribution of {layer_select} {vv_name} observations in the model and observational datasets.") 
scatter_text.append(f"This is shown for each month of the year (Figure {chapter}{i_figure}) and for the entire year (Figure {chapter}{i_figure + 1}).")

md(" ".join(scatter_text).strip().replace("  ", " "))

# %% tags=["remove-input"]
# %%capture --no-display
# %%R -i df -i compact -i vv_name -i unit -w 1000 -h 1200
# #%%R -i df -i variable -i unit -w 1600 -h 1000
#df <- arrow::read_feather("adhoc/tmp/df_raw.feather")
if("month" %in% colnames(df) & compact == FALSE){


library(tidyverse, warn.conflicts = FALSE)

if(vv_name == "temperature"){
    if(str_detect(unit, "C"))
     unit = "°C"
}

x_lab <- str_glue("Model {vv_name} ({unit})")
y_lab <- str_glue("Observed {vv_name} ({unit})")


x_lab <- str_replace(x_lab, "/m\\^3", "m<sup>-3</sup>")
y_lab <- str_replace(y_lab, "/m\\^3", "m<sup>-3</sup>")
x_lab <- str_replace(x_lab, "/m\\^2", "m<sup>-2</sup>")
y_lab <- str_replace(y_lab, "/m\\^2", "m<sup>-2</sup>")
#title <- str_replace_all(title, "m-([0-9]+)", "m<sup>-\\1</sup>")
x_lab <- str_replace_all(x_lab, "m-([0-9]+)", "m<sup>-\\1</sup>")
y_lab <- str_replace_all(y_lab, "m-([0-9]+)", "m<sup>-\\1</sup>")


df <- df %>%
# convert month number to name, e.g. 1=Jan
# do not use a factor
    mutate(month = month.abb[month]) %>%
    ungroup()

df <- df %>%
    mutate(month = "All months") %>%
    ungroup() %>%
    bind_rows(df)

# convert month to factor
df$month <- factor(df$month, levels = c("All months", month.abb))



gg <- df %>%
# final six months of the year
    ggplot()+
    geom_point(aes(model, observation))+
    facet_wrap(~month)+
    theme_gray(base_size = 24)+
    labs(fill = title)+
    geom_abline()+
    geom_smooth(aes(model, observation), method = "gam")+
    labs(x = x_lab, y = y_lab)+
    theme(axis.title.x = ggtext::element_markdown())+
    theme(axis.title.y = ggtext::element_markdown())

    # move legen

gg
}

# %% tags=["remove-input"]
if variable not in ["carbon", "benbio", "susfrac", "oxycons"]:
    if compact is False:
        if layer_select == "surface":
            md(f"**Figure {chapter}{i_figure}**: Simulated versus observed {vv_name} in the top 5 m of the water column. The blue curve is a generalized additive model (GAM) fit to the data, and the black line represents 1-1 relationship between the simulation and observations. The data has been averaged per model grid cell.") 
        if layer_select == "bottom":
            md(f"**Figure {chapter}{i_figure}**: Simulated versus observed {vv_name} near the bottom of the water column. The blue curve is a generalized additive model (GAM) fit to the data, and the black line represents 1-1 relationship between the simulation and observations. The data has been averaged per model grid cell.") 
        i_figure = i_figure + 1

# %% tags=["remove-input"]
# %%capture --no-display
# %%R -i vv_name -i unit -i compact -w 500 

if(compact){
library(dplyr, warn.conflicts = FALSE)
library(ggplot2, warn.conflicts = FALSE)
library(stringr)


df <- arrow::read_feather("adhoc/tmp/df.feather")



x_lab <- str_glue("Model {vv_name} ({unit})")
y_lab <- str_glue("Observed {vv_name} ({unit})")
x_lab <- str_replace(x_lab, "/m\\^3", "m<sup>-3</sup>")
y_lab <- str_replace(y_lab, "/m\\^3", "m<sup>-3</sup>")
x_lab <- str_replace(x_lab, "/m\\^2", "m<sup>-2</sup>")
y_lab <- str_replace(y_lab, "/m\\^2", "m<sup>-2</sup>")
x_lab <- str_replace_all(x_lab, "m-([0-9]+)", "m<sup>-\\1</sup>")
y_lab <- str_replace_all(y_lab, "m-([0-9]+)", "m<sup>-\\1</sup>")

gg <- df %>%
# final six months of the year
    ggplot()+
    geom_point(aes(model, observation))+
    theme_gray(base_size = 14)+
    labs(fill = title)+
    geom_abline()+
    geom_smooth(aes(model, observation), method = "gam")+
    labs(x = x_lab, y = y_lab)+
    theme(axis.title.x = ggtext::element_markdown())+
    theme(axis.title.y = ggtext::element_markdown())
    # move legen

gg
}

# %% tags=["remove-input"]
if compact:
    md(f"**Figure {chapter}{i_figure}**: Model vs observed {vv_name} for {layer_select} values. The observations are from {data_source(vv_source, vv_name)}. The line is a generalized additive model (GAM) fit to the data. The shaded area is the 95% confidence interval of the GAM fit.")
    i_figure += 1
if layer_select == "surface":
    if layer not in ["benthic"]:
        md(f"## Summary statistics for {vv_name} at the sea surface")
    else:
        md(f"## Summary statistics for {vv_name} in the sediment layer") 
else:
    md(f"## Summary statistics for {vv_name} at the near-bottom")

# %% tags=["remove-input"]
md(f"The overall ability of the model to predict the observed {vv_name} was assessed by calculating the average bias, the root mean square error (RMSE) and the correlation coefficient (R). The bias was calculated as the model value minus the observed value. The RMSE was calculated as the square root of the mean squared error. The correlation coefficient was calculated as the Pearson correlation coefficient between the model and observed values.") 
md(f"This was calculated for each month and for the entire dataset. The results are shown in the tables below.")

# %% tags=["remove-input"]
if variable not in ["carbon", "benbio", "susfrac", "oxycons"]:
    df_bias = (
        df_raw
        .assign(bias = lambda x: x.model - x.observation)
        .groupby("month")
        .mean()
        .reset_index()
        .loc[:,["month", "bias"]]
        # convert month number to name
        .assign(month = lambda x: x.month.apply(lambda y: calendar.month_abbr[y]))
    )
    # add average bias to df_bias as a separate row
    annual_bias = df_raw.model.mean() - df_raw.observation.mean() 
    df_bias = pd.concat([df_bias, pd.DataFrame({"month": ["All"], "bias": [annual_bias]})])

    # move the final row to the top
    df_bias = pd.concat([df_bias.iloc[[-1]], df_bias.iloc[:-1]])
else:
    # only want annual
    df_bias = pd.DataFrame({"month": ["All"], "bias": [df_raw.model.mean() - df_raw.observation.mean()]})
if variable not in ["carbon", "benbio", "susfrac", "oxycons"]:
    # now create an rmse dataframe
    df_rmse = (
        df_raw
        .assign(month = lambda x: x.month.apply(lambda y: calendar.month_abbr[y]))
        .groupby("month")
        .apply(lambda x: np.sqrt((x.model - x.observation).pow(2).mean()))
        .reset_index()
        .rename(columns={0: "rmse"})
    )
    # add average rmse to df_rmse as a separate row
    annual_rmse = np.sqrt(((df_raw.model - df_raw.observation).pow(2)).mean())
    df_rmse = pd.concat([df_rmse, pd.DataFrame({"month": ["All"], "rmse": [annual_rmse]})])
    # move the final row to the top
    df_rmse = pd.concat([df_rmse.iloc[[-1]], df_rmse.iloc[:-1]])
else:
    # only want annual
    df_rmse = pd.DataFrame({"month": ["All"], "rmse": [np.sqrt(((df_raw.model - df_raw.observation).pow(2)).mean())]})
# rename the month column to Month
# merge the two dataframes
df_table = copy.deepcopy(df_bias).merge(df_rmse)
df_table = df_table.round(2)
# create df_corr
if variable not in ["carbon", "benbio", "susfrac", "oxycons"]:
    df_corr = (
        df_raw
        .groupby("month")
        .apply(lambda x: x.model.corr(x.observation))
        .reset_index()
        .rename(columns={0: "correlation"})
        .assign(month = lambda x: x.month.apply(lambda y: calendar.month_abbr[y]))
    )
    # add average correlation to df_corr as a separate row
    # calculate annual correlation using all data
    annual_corr = df_raw.model.corr(df_raw.observation)
    df_corr = pd.concat([df_corr, pd.DataFrame({"month": ["All"], "correlation": [annual_corr]})])
    # df_corr = df_corr.append({"month": "All", "correlation": annual_corr}, ignore_index=True)

    # move the final row to the top
    df_corr = pd.concat([df_corr.iloc[[-1]], df_corr.iloc[:-1]])
else:
    # only want annual
    df_corr = pd.DataFrame({"month": ["All"], "correlation": [df_raw.model.corr(df_raw.observation)]})
df_table = df_table.merge(df_corr)
df_table = df_table.round(2)
df_table = df_table.rename(columns={"month": "Month", "bias": "Bias", "rmse": "RMSE", "correlation": "Correlation"})
df_table = df_table[["Month", "Bias", "RMSE", "Correlation"]]
# change Month to Period
df_table = df_table.rename(columns={"Month": "Time period"})

if variable not in ["carbon", "benbio", "susfrac", "oxycons"]:
    # add commas to bias and rmse
    df_number = df_raw.groupby("month").count().reset_index().loc[:,["month", "observation"]]
# convert month number to name
    df_number["month"] = df_number["month"].apply(lambda x: calendar.month_abbr[x])
    df_number = df_number.rename(columns={"month": "Time period", "observation": "Number of observations"})
else:
    df_number = pd.DataFrame({"Time period": ["All"], "Number of observations": [len(df_raw)]})

# add total number of observations
annual_number = len(df_raw)
if variable not in ["carbon", "benbio", "susfrac", "oxycons"]:
    df_number = pd.concat([df_number, pd.DataFrame({"Time period": ["All"], "Number of observations": [annual_number]})])
# df_number = df_number.append({"Time period": "All", "Number of observations": annual_number}, ignore_index=True)
df_table = df_table.merge(df_number)

# include commas in the number of observations
df_table["Number of observations"] = df_table["Number of observations"].apply(lambda x: "{:,}".format(x))

df_display(df_table)

# %% tags=["remove-input"]
md(f"**Table {chapter}{i_table}:** Average bias and root-mean square error in {layer_select} {vv_name} for each month using the raw {data_source(vv_source, vv_name)} data. The bias is calculated as model - observation. The average bias is calculated as the mean of the monthly biases.")
i_table += 1


# %% tags=["remove-input"]
md(f"A linear regression analysis of modelled and observed {vv_name} was performed. The modelled {vv_name} was used as the independent variable and the observed {vv_name} was used as the dependent variable. The results are shown in the table below.")

md("The regression was carried out using the Python package statsmodels.")

# %% tags=["remove-input"]

# do a linear regression of model vs observed in df
X = df.model.values
Y = df.observation.values
# linear regression using statsmodels
import statsmodels.api as sm
X = sm.add_constant(X)
# make X and Y random numbers between 0 and 1
X = sm.add_constant(X)
model = sm.OLS(Y, X).fit()
# get the slope and intercept
intercept, slope = model.params
# calculate the r squared
r2 = model.rsquared
# calculate the p value of the slope
p = model.f_pvalue

p = model.f_pvalue
# put that in a dataframe
df_stats = pd.DataFrame({"Slope": slope, "Intercept": intercept, "R2": r2, "P": p}, index = ["All"]).assign(Period = "All")
# do this month by month append to df_stats

for month in range(1, 13):
    try:
        X = df.query("month == @month").model.values
        Y = df.query("month == @month").observation.values
        X = sm.add_constant(X)
        model = sm.OLS(Y, X).fit()
        intercept, slope = model.params
        r2 = model.rsquared
        p = model.f_pvalue
        df_stats = pd.concat([df_stats, pd.DataFrame({"Slope": slope, "Intercept": intercept, "R2": r2, "P": p}, index = [month]).assign(Period = month)])
        df_stats.loc[df_stats.index[-1], "Period"] = calendar.month_abbr[month]
    except:
        pass
# sort period appropriately, so All is first then ordered by month
df_stats["Period"] = pd.Categorical(df_stats["Period"], [calendar.month_abbr[x] for x in range(1, 13)] + ["All"])
# round p-value to 3 dp
df_stats["P"] = df_stats["P"].round(5)
# change P to p-value
df_stats = df_stats.rename(columns={"P": "p-value"})
# put Period first
df_stats = df_stats[["Period", "Slope", "Intercept", "R2", "p-value"]]
# 
df_display(df_stats)

# %% tags=["remove-input"]
md(f"**Table {chapter}{i_table}:** Linear regression analysis of modelled and observed {vv_name}. The modelled {vv_name} was used as the independent variable and the observed {vv_name} was used as the dependent variable. The slope and intercept of the regression line are shown, along with the R<sup>2</sup> value and the p-value of the slope. The p-value is a measure of the significance of the slope. A p-value less than 0.05 is considered statistically significant. Note: only months with sufficient values for a regression are shown.")
i_table += 1 
