# %% [markdown]
# # Pesticides in U.S. Streams Dashboard
# Run from the App folder: shiny run --reload text.py
#
# 
#
# ---
# %%
# SETUP
# I for some reason thought it would be a good idea to put the text in another .py and then decided to make 
# a third tab and now it's all a mess and I'm too scared to change anything 

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy import stats
import statsmodels.formula.api as smf
from shiny import reactive
from shiny.express import input, render, ui, app_opts
import base64

sys.path.insert(0, str(Path(__file__).parent))  # so pesticide_map.py can be imported
from pesticide_map import make_map, map_df, sites, data_path


img_path = Path(__file__).parent / 'images' / 'dashboardIMG.png'
img_b64 = base64.b64encode(img_path.read_bytes()).decode()

# Site-year averages by pesticide 
pest = pd.read_csv(data_path / 'pest_water_cat.csv')
pest = pest[(pest['mean_pesticide_use'] > 0) & (pest['mean_concentration_water'] > 0)]
pest['Pest_Category'] = pest['Pest_Category'].fillna('Unclassified')

years = sorted(pest['Water_Year'].unique())
categories = sorted(pest['Pest_Category'].unique())

# colors for years and shapes for pesticide types
year_colors = dict(zip(years, ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#D55E00', '#56B4E9']))
cat_markers = dict(zip(categories, ['o', 's', '^', 'D', 'v', 'P', 'X', '*']))


#Again scary things. I am so glad I never have to go into webdev. 
# %%
# MODELS (fit once when the app starts)
pest['log_use'] = np.log10(pest['mean_pesticide_use'])
pest['log_conc'] = np.log10(pest['mean_concentration_water'])

def fit_models(d):
    """Fit use-only and use + pesticide type models on a subset of the data."""
    pooled = smf.ols('log_conc ~ log_use', data=d).fit()
    full = smf.ols('log_conc ~ log_use + C(Pesticide_Name)', data=d).fit()
    return pooled, full

# Model on all pesticides (used for the Model details table)
pooled_all, full_all = fit_models(pest)

# Each pesticide's own baseline (no shared intercept), relative to the average pesticide
by_pest = smf.ols('log_conc ~ log_use + C(Pesticide_Name) - 1', data=pest).fit()
levels = by_pest.params.filter(like='Pesticide_Name')
ci = by_pest.conf_int().loc[levels.index]
center = levels.mean()
pest_effects = pd.DataFrame({
    'pesticide': levels.index.str.extract(r'\[(.*)\]')[0].values,
    'times': 10**(levels.values - center),
    'low': 10**(ci[0].values - center),
    'high': 10**(ci[1].values - center),
}).sort_values('times')

# Pesticides selected by default on the Model tab
top_pests = list(pest['Pesticide_Name'].value_counts().head(5).index)
all_pests = sorted(pest['Pesticide_Name'].unique())


# Pesticide name -> category, for labels
pest_cat = pest.groupby('Pesticide_Name')['Pest_Category'].first().to_dict()

line_colors = ['#0072B2', '#E69F00', '#009E73', '#CC79A7',
               '#D55E00', '#56B4E9', '#F0E442', '#000000']

def p_label(p):
    return 'p < 0.001' if p < 0.001 else f'p = {p:.3f}'

#Creation of the actual dashboard pages 
# %%
# PAGE
ui.page_opts(window_title='Pesticides in U.S. Streams', fillable=False)

# ---------------------------------------------------------------
# PAGE 1: OVERVIEW
# ---------------------------------------------------------------
with ui.nav_panel('Overview'):
    ui.h1('Pesticides in U.S. Streams',
          style='font-weight: 700; margin-top: 1.5rem; margin-bottom: 0.25rem;')
    ui.p('County pesticide use and stream concentrations, 2013–2017',
         class_='text-muted', style='font-size: 1.2rem;')
    ui.hr()

    ui.markdown("""
### Introduction

This dashboard compares how much pesticide is applied to farmland in each 
U.S. county with how much shows up in nearby streams. It maps estimated 
agricultural pesticide use alongside concentrations measured at USGS stream 
monitoring sites from 2013 to 2017, so you can see where 
heavy use and high stream levels overlap. The data is organized both by pesticide 
types and individual pesticides. 


### Background

Pesticides are widely used across the United States to support agricultural 
production, but their effects can extend well beyond the fields where they 
are applied. Understanding the relationship between pesticide use and surface 
water contamination is important for identifying potential environmental and 
human health impacts. By investigating these patterns, we hope to help farmers 
and communities make more informed decisions about pesticide use and its 
consequences.

Herbicides now make up about two-thirds of U.S. pesticide use, and have increased 
in use since the early 2000s because of glyphosate and the spread 
of herbicide-tolerant corn and soybeans. 

Changing weather patterns are also making runoff worse and increasing the amount of 
pesticides that are ending up in water systems. A growing share of 
U.S. rainfall now arrives in intense single-day storms. Heavy downpours wash more 
pesticide off fields before it can break down or bind to soil.

#### Data

- **Pesticide use:** USGS county-level estimates of agricultural pesticide use, averaged
  across 2013–2017. 
- **Stream concentrations:** Mean pesticide concentrations in water (µg/L) measured at
  USGS stream monitoring sites, averaged across sampling events at each site.
""")

    with ui.layout_columns(col_widths=[7, 5], class_='align-items-center'):
        ui.markdown("""
#### How to use the map

- **Counties** are shaded from light yellow (less use) to dark brown (more use).
  Counties in white have no estimate.
- **Dots** are monitoring sites, shaded from light to dark blue by concentration.
- Hover over a county or site for a quick summary, or click for full details.
- Use the layer control in the top right to turn counties or sites on and off.
""")
        with ui.div():
            ui.img(src=f'data:image/png;base64,{img_b64}',
                   alt='Example of hovering over a monitoring site on the map',
                   style='width: 100%; max-width: 380px; border: 1px solid #ddd; '
                         'border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);')
            ui.p('Example: hovering over a monitoring site shows its name, '
                 'stream concentration, and county pesticide use.',
                 class_='text-muted',
                 style='font-size: 0.85rem; margin-top: 0.4rem; max-width: 380px;')

    with ui.card(height='650px'):
        @render.ui
        def pest_map():
            return ui.HTML(make_map(map_df, sites)._repr_html_())

# ---------------------------------------------------------------
# PAGE 2: RESULTS
# ---------------------------------------------------------------
#my perfect child
with ui.nav_panel('Results'):
    with ui.layout_sidebar():
        with ui.sidebar():
            ui.input_checkbox_group('years', 'Years',
                                    choices=[str(y) for y in years],
                                    selected=[str(y) for y in years])
            ui.input_checkbox_group('category', 'Pesticide type',
                                    choices={c: c.capitalize() for c in categories},
                                    selected=categories)

        @reactive.calc
        def filtered():
            d = pest[pest['Water_Year'].isin([int(y) for y in input.years()])]
            return d[d['Pest_Category'].isin(input.category())]

        with ui.card(full_screen=True):
            ui.card_header('County Pesticide Use vs. Stream Concentration')

            @render.plot(height=550)
            def use_vs_conc():
                d = filtered()
                fig, ax = plt.subplots(figsize=(10, 6))

                if len(d) < 3:
                    ax.text(0.5, 0.5, 'Not enough data for this selection',
                            ha='center', va='center', transform=ax.transAxes)
                    ax.axis('off')
                    return fig

                # Points: color = year, shape = pesticide type
                for (yr, cat), g in d.groupby(['Water_Year', 'Pest_Category']):
                    ax.scatter(g['mean_pesticide_use'], g['mean_concentration_water'],
                               color=year_colors[yr], marker=cat_markers[cat],
                               s=14, alpha=0.35, edgecolors='none')

                # Log-log regression line
                fit = stats.linregress(np.log10(d['mean_pesticide_use']),
                                       np.log10(d['mean_concentration_water']))
                xs = np.logspace(np.log10(d['mean_pesticide_use'].min()),
                                 np.log10(d['mean_pesticide_use'].max()), 100)
                ax.plot(xs, 10**(fit.intercept + fit.slope * np.log10(xs)),
                        color='red', linewidth=2)

                p_text = 'p < 0.001' if fit.pvalue < 0.001 else f'p = {fit.pvalue:.3f}'
                ax.set(xscale='log', yscale='log',
                       xlabel='County Pesticide Use, High Estimate (kg)',
                       ylabel='Water Concentration (µg/L)',
                       title=f'n = {len(d):,}   ·   R² = {fit.rvalue**2:.2f}   ·   {p_text}')

                # Two legends: years (colors) and pesticide types (shapes)
                year_handles = [Line2D([], [], marker='o', linestyle='', color=year_colors[y],
                                       markersize=8, label=str(y))
                                for y in sorted(d['Water_Year'].unique())]
                cat_handles = [Line2D([], [], marker=cat_markers[c], linestyle='', color='gray',
                                      markersize=8, label=c.capitalize())
                               for c in sorted(d['Pest_Category'].unique())]

                year_legend = ax.legend(handles=year_handles, title='Year', frameon=False,
                                        loc='upper left', bbox_to_anchor=(1.02, 1))
                ax.add_artist(year_legend)
                ax.legend(handles=cat_handles, title='Pesticide type', frameon=False,
                          loc='upper left', bbox_to_anchor=(1.02, 0.55))

                fig.tight_layout()
                return fig

# ---------------------------------------------------------------
# PAGE 3: MODEL
# ---------------------------------------------------------------
pest_cat = pest.groupby('Pesticide_Name')['Pest_Category'].first().to_dict()

with ui.nav_panel('Model'):
    ui.h2('How the Model Works', style='margin-top: 1.5rem;')
    ui.markdown(f"""
### Building the model

Each data point is one pesticide at one USGS stream monitoring site averaged over one year, 
paired with the estimated agricultural use of that pesticide in the surrounding 
county in one year. In total the model uses **{len(pest):,} data points** covering 
**{pest['Pesticide_Name'].nunique()} pesticides**.

Both county use and stream concentration span several orders of magnitude and are 
heavily right skewed. To make the relationship easier to model, both were converted to a 
log10 scale. Rows with zero use or zero concentration were removed, since the log of zero is undefined.

We then fit a multiple linear regression (ordinary least squares) with two 
predictors, county use and pesticide name:

**log10(stream concentration) = intercept + slope × log10(county use) + pesticide adjustment**


Including pesticide adjustment allows for the data to be normalized for pesticide type. Since 
pesticides are used in different amounts it says holding which pesticide it is constant how 
much of an impact does use of the pesticide in ag have on streams. 


### Overall results (all pesticides)
""")

    with ui.layout_columns(col_widths=[4, 4, 4]):
        with ui.value_box():
            'R²'
            f'{full_all.rsquared:.2f}'
            f'Use + pesticide explain {full_all.rsquared:.0%} of the variation in stream levels'

        with ui.value_box():
            'p-value (county use)'
            p_label(full_all.pvalues['log_use']).removeprefix('p ').strip()
            'Chance of a use effect this strong if there were no real link'

        with ui.value_box():
            'OLS slope (log use)'
            f'{full_all.params["log_use"]:.3f}'
            'log₁₀ concentration per log₁₀ county use, same pesticide'

    ui.markdown(f"""
**What this means:** together, county use and pesticide identity explain 
{full_all.rsquared:.0%} of the differences in stream concentrations. Almost all of 
that comes from which pesticide it is: county use on its own explains only 
{pooled_all.rsquared:.0%}. For the same pesticide, counties using 10 times more 
have about {(10**full_all.params["log_use"] - 1) * 100:.0f}% higher stream levels. 
That link is statistically clear but modest, so the chemical matters far more than 
the amount applied.

The chart below fits a separate line to each pesticide on its own. Those R² values 
are much lower than {full_all.rsquared:.2f} because they only measure how well use 
predicts stream levels *within* one pesticide, which is the part the overall model 
shows is weak.
""")

    ui.h3('Individual pesticides', style='margin-top: 1.5rem;')
    ui.input_selectize(
        'model_pests', 'Choose pesticides (8 max)',
        choices={p: f'{p} ({pest_cat[p].capitalize()})' for p in all_pests},
        selected=top_pests, multiple=True,
        options={'maxItems': 8, 'plugins': ['remove_button']},
        width='100%',
    )

    with ui.card(full_screen=True):
        ui.card_header('Stream concentration vs. county use, one trend line per pesticide')

        @render.plot(height=550)
        def pest_lines():
            chosen = list(input.model_pests())
            fig, ax = plt.subplots(figsize=(11, 6))

            # Background: all other pesticides
            other = pest[~pest['Pesticide_Name'].isin(chosen)]
            ax.scatter(other['mean_pesticide_use'], other['mean_concentration_water'],
                       color='lightgray', s=5, alpha=0.3, label='Other pesticides')

            # Overall model line
            xs_all = np.linspace(pest['log_use'].min(), pest['log_use'].max(), 50)
            ys_all = pooled_all.params['Intercept'] + pooled_all.params['log_use'] * xs_all
            ax.plot(10**xs_all, 10**ys_all, color='black', linestyle='--', linewidth=1.5,
                    label='All pesticides')
            ax.text(10**xs_all[-1] * 1.2, 10**ys_all[-1],
                    f'R² = {pooled_all.rsquared:.2f}',
                    fontsize=9, fontweight='bold', va='center')

            # One fitted line per selected pesticide, R² at the end of each line
            for name, color in zip(chosen, line_colors):
                d = pest[pest['Pesticide_Name'] == name]
                ax.scatter(d['mean_pesticide_use'], d['mean_concentration_water'],
                           color=color, s=8, alpha=0.4)

                if len(d) < 3 or d['log_use'].nunique() < 2:
                    continue
                fit = stats.linregress(d['log_use'], d['log_conc'])
                xs = np.linspace(d['log_use'].min(), d['log_use'].max(), 50)
                ys = fit.intercept + fit.slope * xs
                ax.plot(10**xs, 10**ys, color=color, linewidth=2.5,
                        label=f'{name} ({pest_cat[name].capitalize()})')
                ax.text(10**xs[-1] * 1.2, 10**ys[-1], f'R² = {fit.rvalue**2:.2f}',
                        color=color, fontsize=9, fontweight='bold', va='center')

            ax.set(xscale='log', yscale='log',
                   xlabel='County Pesticide Use, High Estimate (kg)',
                   ylabel='Water Concentration (µg/L)')
            ax.set_xlim(right=pest['mean_pesticide_use'].max() * 30)  # room for R² labels
            ax.legend(frameon=False, fontsize=9, loc='upper left',
                      bbox_to_anchor=(1.01, 1))
            fig.tight_layout()
            return fig

        ui.markdown("""
Each colored line is a separate regression fit only to that pesticide's data. 
The **R²** at the end of each line shows how much of that pesticide's variation 
in stream levels is explained by county use. Values near 0 mean use tells you 
little about stream levels for that pesticide; higher values mean a closer link.
""", )

    with ui.card(full_screen=True):
        ui.card_header('Which pesticides run higher or lower than expected')
        ui.markdown("""
Typical stream concentration for each pesticide at the same level of county use, 
compared to the average pesticide, grouped by pesticide type. Values to the right 
of the red line run higher than average; values to the left run lower. Pesticides 
selected above are highlighted in the same colors as the chart. Bars show 95% 
confidence intervals.
""")

        @render.plot(height=1000)
        def pest_effects_plot():
            colors = dict(zip(input.model_pests(), line_colors))
            d = pest_effects.assign(
                category=pest_effects['pesticide'].map(pest_cat).str.capitalize())

            cat_order = sorted(d['category'].unique(),
                               key=lambda c: (c == 'Unclassified', c))

            parts, headers, y = [], [], 0
            for cat in cat_order:
                g = d[d['category'] == cat].sort_values('times', ascending=False)
                headers.append((y, cat))
                parts.append(g.assign(y=np.arange(y + 1, y + 1 + len(g))))
                y += len(g) + 1.5
            r = pd.concat(parts)

            fig, ax = plt.subplots(figsize=(9, 14))
            point_colors = [colors.get(p, '#9aa5b1') for p in r['pesticide']]

            ax.errorbar(r['times'], r['y'],
                        xerr=[r['times'] - r['low'], r['high'] - r['times']],
                        fmt='none', ecolor='lightgray')
            ax.scatter(r['times'], r['y'], color=point_colors, s=30, zorder=3)
            ax.axvline(1, color='red', linestyle='--', linewidth=1)

            for hy, cat in headers:
                ax.text(0.01, hy, cat, transform=ax.get_yaxis_transform(),
                        fontweight='bold', fontsize=11, va='center')
                if hy > 0:
                    ax.axhline(hy - 0.75, color='#dddddd', linewidth=0.8)

            ax.set_yticks(r['y'])
            ax.set_yticklabels(r['pesticide'])
            ax.set_ylim(y - 1, -1)
            ax.set(xscale='log', xlabel='Times higher or lower than the average pesticide')
            ax.tick_params(axis='y', labelsize=8)

            for label in ax.get_yticklabels():
                if label.get_text() in colors:
                    label.set_fontweight('bold')
                    label.set_color(colors[label.get_text()])

            fig.tight_layout()
            return fig