### app.py
#### Setup
# Packages
from pathlib import Path
import pandas as pd 
import geopandas as gpd
import seaborn as sns
import re
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from scipy import stats
from bs4 import BeautifulSoup
import requests

#widget packages
import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.display import display, clear_output
from shiny import App, reactive, render, ui

# Paths 
project_fldr = Path.cwd().parent
raw_fldr = project_fldr /'Data'/'unprocessed' 
processed_fldr = project_fldr /'Data'/'processed'

# Import cleaned data
pest_water_categorized = pd.read_csv(processed_fldr/'pest_water_cat.csv')
pest_water_categorized.head()

#### Base Plot
#Seaborn Theme 
sns.set_theme(style='whitegrid', 
              context='notebook', 
              palette= "pastel", 
              font_scale=0.8, 
              rc={
                  "axes.titlesize": 20, 
                  "font.family": "serif"}
 )
# Filtering data

Year = "2013"
Pesticide_Category = "herbicide"

# Subset the data
pest_water_categorized_subset = pest_water_categorized.loc[
    (pest_water_categorized['Water_Year'] == Year) &
    (pest_water_categorized['Pest_Category'] == Pesticide_Category),
]
# Plotting data
Lin_reg = sns.regplot(
    data= pest_water_categorized,
    x='log_mean_pesticide_use',
    y='log_mean_concentration_water',
    line_kws={'color': 'red'}

)
Lin_reg.set(
    title=(f'Average County {Pesticide_Category} Use vs. Average Water Concentration '),
    xlabel=(f'Logged County {Pesticide_Category} Use, High Estimate  avg(kg)'),
    ylabel='Logged Water Concentration avg (µg/L)',
)


#### Convert to a function
# Plot as a Function

def plot_pesticide(Year = "2013",
    Pesticide_Category = "herbicide"):
    #Subset
    pest_water_categorized_subset = pest_water_categorized.loc[
    (pest_water_categorized['Water_Year'] == Year) &
    (pest_water_categorized['Pest_Category'] == Pesticide_Category),
    ]
    #Plot
    Lin_reg = sns.regplot(
    data= pest_water_categorized_subset,
    x='log_mean_pesticide_use',
    y='log_mean_concentration_water',
    line_kws={'color': 'red'}, 

    )
    Lin_reg.set(
        title=(f'Average County {Pesticide_Category} Use vs. Average Water Concentration '),
        xlabel=(f'Logged County {Pesticide_Category} Use, High Estimate  avg(kg)'),
        ylabel='Logged Water Concentration avg (µg/L)',
    )
    return Lin_reg

# Apply function
plot_pesticide(Year=2015, Pesticide_Category="herbicide")
#### Widgets
#Clean pesticide category column 
pest_water_categorized = pest_water_categorized.dropna(
    subset=['Pest_Category'])
# Create a dropdown widget from Pesticide Category
year_list = pest_water_categorized['Water_Year'].unique()
year_dropdown = widgets.Dropdown(
    options=year_list,
    value=year_list[0],
    description='Year:',
    )
# Create a dropdown widget from Pesticide Category
pest_list = pest_water_categorized['Pest_Category'].unique()
pest_dropdown = widgets.Dropdown(
    options=pest_list,
    value=pest_list[0],
    description='Pesticide:',
    )
# Update the plot
plot_output = widgets.Output()

# Function to update the plot
def update_plot(change=None):
    #Direct output to the plot_output widget
    with plot_output:
        # Clear the previous plot
        clear_output(wait=True)

        # Generate the new plot
        g = plot_pesticide(Year = year_dropdown.value,
        Pesticide_Category = pest_dropdown.value)

        # Explicitly display the plot
        display(g.figure)
        plt.close(g.figure)

# Attach observers
year_dropdown.observe(update_plot, names='value')
pest_dropdown.observe(update_plot, names='value')

# Display the widgets and plot together
display(
    widgets.VBox([
        year_dropdown,
        pest_dropdown,
        plot_output
    ])
)

# Generate the initial plot
update_plot()
#### Shiny 
# Create shiny controls
app_ui = ui.page_fluid(

    ui.h2("Pesticide Use and Water Concentration"),

    # Year dropdown
    ui.input_select(
        id="year",
        label="Select Year:",
        choices=[
            str(year) for year in sorted( 
            pest_water_categorized['Water_Year'].unique()
        )
        ],
        selected="2013"
    ),

    # Pesticide dropdown
    ui.input_select(
        id="pesticide",
        label="Select Pesticide Category:",
        choices=sorted(
            pest_water_categorized['Pest_Category'].unique()
        ),
        selected="herbicide"
    ),

    # Regression plot
    ui.output_plot("regression_plot")
)
# Create shiny server
def server(input, output, session):

    @render.plot
    def regression_plot():

        # Get selected values
        selected_year = input.year()
        selected_pesticide = input.pesticide()

        # Generate regression plot
        fig = plot_pesticide(
            Year=selected_year,
            Pesticide_Category=selected_pesticide
        )

        return fig
app = App(app_ui, server)

