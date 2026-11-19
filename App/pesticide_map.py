# %% [markdown]
# # Pesticide Use and Stream Concentrations Map
# - County pesticide use (high estimate, kg), mean 2013–2017
# - USGS stream monitoring sites, mean pesticide concentration in water (µg/L)
#
# **CONDA RECIPE**
# ```bash
# conda create -n env700-shiny -c conda-forge python=3.12 shiny geopandas pandas matplotlib folium mapclassify jupyterlab ipykernel
# ```
#
# 
#
# ---
# %%
# SETUP
# Packages
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import folium

# Paths
# All data lives in App/data so the app can be deployed on its own
app_path = Path(__file__).parent.resolve()
data_path = app_path / 'data'
out_path = data_path

# %%
# LOAD COUNTIES
map_df = gpd.read_file(data_path / 'counties_pesticide.gpkg').to_crs('EPSG:4326')

#Simplify Data so the map loads faster 
states = map_df[['STATEFP', 'geometry']].dissolve(by='STATEFP')
states['geometry'] = states.geometry.simplify(0.01)

map_df['geometry'] = map_df.geometry.simplify(0.01)

# %%
# LOAD SITES
sites = gpd.read_file(data_path / 'sites.gpkg').to_crs('EPSG:4326')

# Needed to fix my poor mergining in the cleaned_ecotox 
sites = sites.drop(columns=[c for c in sites.columns if c.endswith('_y')])
sites.columns = [c.removesuffix('_x') for c in sites.columns]

# Round data for popups 
sites['mean_concentration_water'] = sites['mean_concentration_water'].round(3)
sites['mean_pesticide_use'] = sites['mean_pesticide_use'].round(0)
map_df['pest_kg'] = map_df['pest_kg'].round(0)

# Log10 versions for coloring, so the legend has evenly spaced labels
map_df['log_pest_kg'] = np.log10(map_df['pest_kg'].where(map_df['pest_kg'] > 0))
sites['log_conc'] = np.log10(sites['mean_concentration_water'].where(sites['mean_concentration_water'] > 0))


#Things far beyond my coding ability that I had to ask AI to do because I hate making dashboards 
# %%
# FUNCTIONS
def make_map(counties, stations):
    """Build an interactive map with clickable counties and monitoring sites."""
    m = counties.explore(
        column='log_pest_kg',
        cmap='YlOrBr',
        style_kwds={'color': '#999999', 'weight': 0.3},
        missing_kwds={'color': 'white', 'fillOpacity': 0.3},
        highlight_kwds={'color': '#1f4e79', 'weight': 3, 'fillOpacity': 0.8},
        tooltip=['NAME', 'pest_kg'],
        tooltip_kwds={'aliases': ['County', 'Pesticide use (kg)']},
        popup=['NAME', 'GEOID', 'pest_kg'],
        popup_kwds={'aliases': ['County', 'FIPS', 'Pesticide use (kg)']},
        legend_kwds={'caption': 'Mean Annual Pesticide Use, High Estimate (log10 kg)'},
        name='Counties',
        tiles='Esri.WorldGrayCanvas',
    )

    # State boundaries (drawn on top of counties, not clickable)
    folium.GeoJson(
        states,
        name='State boundaries',
        style_function=lambda f: {'color': '#333333', 'weight': 1.2, 'fillOpacity': 0},
        interactive=False,
    ).add_to(m)

    stations.explore(
        m=m,
        column='log_conc',
        cmap='Blues',
        missing_kwds={'color': 'lightgray'},
        marker_kwds={'radius': 4},
        style_kwds={'color': 'black', 'weight': 0.5, 'fillOpacity': 0.9},
        tooltip=['station_nm', 'mean_concentration_water', 'mean_pesticide_use'],
        tooltip_kwds={'aliases': ['Station', 'Concentration (µg/L)', 'Pesticide use (kg)']},
        popup=['station_nm', 'site_id', 'state_cd', 'huc_cd', 'Drainage_area_km2',
               'mean_concentration_water', 'mean_pesticide_use'],
        popup_kwds={'aliases': ['Station', 'Site ID', 'State', 'HUC', 'Drainage area (km²)',
                                'Concentration (µg/L)', 'Pesticide use (kg)']},
        legend_kwds={'caption': 'Stream Concentration (log10 µg/L)'},
        name='Monitoring sites',
    )

    folium.LayerControl().add_to(m)

    # Move the zoom buttons below the legends so they don't overlap
    m.get_root().header.add_child(folium.Element(
        '<style>'
        '.leaflet-top.leaflet-left { top: 130px; }'
        '.leaflet-interactive:focus { outline: none; }'  # remove the square click box
        '</style>'
    ))
    return m

# %%
# MAKE MAP
# Only runs when this file is run directly, not when app.py imports it
if __name__ == '__main__':
    m = make_map(map_df, sites)
    m.save(out_path / 'pesticide_map.html')