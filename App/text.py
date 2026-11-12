# %% [markdown]
# # Pesticides in U.S. Streams Dashboard
# Run from the App folder: shiny run --reload text.py
#
# Peyton Smith · Fall 2026
#
# ---
# %%
# SETUP
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy import stats
import statsmodels.formula.api as smf
from shiny import reactive
from shiny.express import input, render, ui

sys.path.insert(0, str(Path(__file__).parent))  # so pesticide_map.py can be imported
from pesticide_map import make_map, map_df, sites, data_path

# Site-year averages by pesticide (saved from the notebook)
pest = pd.read_csv(data_path / 'pest_water_cat.csv')
pest = pest[(pest['mean_pesticide_use'] > 0) & (pest['mean_concentration_water'] > 0)]
pest['Pest_Category'] = pest['Pest_Category'].fillna('Unclassified')

years = sorted(pest['Water_Year'].unique())
categories = sorted(pest['Pest_Category'].unique())

# Colorblind-friendly colors for years, shapes for pesticide types
year_colors = dict(zip(years, ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#D55E00', '#56B4E9']))
cat_markers = dict(zip(categories, ['o', 's', '^', 'D', 'v', 'P', 'X', '*']))

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

line_colors = ['#0072B2', '#E69F00', '#009E73', '#CC79A7',
               '#D55E00', '#56B4E9', '#F0E442', '#000000']

def p_label(p):
    return 'p < 0.001' if p < 0.001 else f'p = {p:.3f}'

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

This research focuses on the central question of whether counties with higher pesticide use also experience higher concentrations of pesticide contamination in surface water. To further explore this relationship, a supporting question examines whether the strength of this correlation differs among pesticide categories, including herbicides, fungicides, and insecticides. The research is intended for residents concerned about pesticide use and water quality in their communities, farmers, and pesticide companies interested in understanding the environmental impacts of pesticide use.

Question: **Do streams in counties with heavy pesticide use
show higher pesticide concentrations in streams?**

#### Data

- **Pesticide use:** USGS county-level estimates of agricultural pesticide use, averaged
  across 2013–2017. The map shows the *high* estimate, which fills in gaps where survey
  data were not reported rather than treating them as zero.
- **Stream concentrations:** Mean pesticide concentrations in water (µg/L) measured at
  USGS stream monitoring sites, averaged across sampling events at each site.

#### How to use the map

- **Counties** are shaded from light yellow (less use) to dark brown (more use).
  Counties in white have no estimate.
- **Dots** are monitoring sites, shaded from light to dark blue by concentration.
- Hover over a county or site for a quick summary, or click for full details.
- Use the layer control in the top right to turn counties or sites on and off.

#### Keep in mind

County use estimates and stream samples don't line up perfectly. A stream can drain land
from several counties, and concentrations depend on rainfall, timing of application, and
how often a site was sampled. Patterns on this map show where use and concentrations
overlap, not proof that one causes the other.
""")

    with ui.card(height='650px'):
        @render.ui
        def pest_map():
            return ui.HTML(make_map(map_df, sites)._repr_html_())

# ---------------------------------------------------------------
# PAGE 2: RESULTS
# ---------------------------------------------------------------
with ui.nav_panel('Results'):
    with ui.layout_sidebar():
        with ui.sidebar():
            ui.input_checkbox_group('years', 'Years',
                                    choices=[str(y) for y in years],
                                    selected=[str(y) for y in years])
            ui.input_select('category', 'Pesticide type',
                            choices=['All'] + categories)

        @reactive.calc
        def filtered():
            d = pest[pest['Water_Year'].isin([int(y) for y in input.years()])]
            if input.category() != 'All':
                d = d[d['Pest_Category'] == input.category()]
            return d

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
with ui.nav_panel('Model'):
    ui.h2('What the Model Shows', style='margin-top: 1.5rem;')
    ui.markdown("""
Different pesticides are used in very different amounts and behave differently once they reach
water, so comparing all of them at once can be misleading. This model compares each pesticide
**only to itself**: atrazine in a high-use county against atrazine in a low-use county, and so on.
That separates two questions: does *more use* raise stream levels, and does *which pesticide*
it is matter?
""")

    ui.input_selectize('model_pests',
                       'Choose pesticides (up to 8). Clear the box to use all pesticides.',
                       choices=all_pests, selected=top_pests, multiple=True,
                       options={'maxItems': 8, 'plugins': ['remove_button']},
                       width='100%')

    @reactive.calc
    def chosen():
        return list(input.model_pests())

    @reactive.calc
    def models():
        d = pest[pest['Pesticide_Name'].isin(chosen())] if chosen() else pest
        return fit_models(d)

    @render.ui
    def selection_note():
        n = len(chosen())
        text = f'Results below use the {n} selected pesticide{"s" if n != 1 else ""}.' if n \
            else 'Results below use all pesticides.'
        return ui.p(text, class_='text-muted')

    with ui.layout_columns(col_widths=[4, 4, 4]):
        with ui.value_box():
            'Effect of 10× more county use'

            @render.text
            def effect_value():
                slope = models()[1].params['log_use']
                return f'{(10**slope - 1) * 100:+.0f}%'

            @render.text
            def effect_note():
                return f'stream concentration, same pesticide ({p_label(models()[1].pvalues["log_use"])})'

        with ui.value_box():
            'Variation explained by use alone'

            @render.text
            def r2_pooled():
                return f'{models()[0].rsquared:.0%}'

            'of differences between samples'

        with ui.value_box():
            'Explained by use + pesticide type'

            @render.text
            def r2_full():
                return f'{models()[1].rsquared:.0%}'

            'of differences between samples'

    with ui.layout_columns(col_widths=[8, 4]):
        with ui.card(full_screen=True):
            ui.card_header('Each pesticide has its own level, but use has the same effect')

            @render.plot(height=480)
            def parallel_lines():
                full = models()[1]
                fig, ax = plt.subplots(figsize=(9, 6))

                other = pest[~pest['Pesticide_Name'].isin(chosen())]
                ax.scatter(other['mean_pesticide_use'], other['mean_concentration_water'],
                           color='lightgray', s=5, alpha=0.3, label='Other pesticides')

                for name, color in zip(chosen(), line_colors):
                    d = pest[pest['Pesticide_Name'] == name]
                    ax.scatter(d['mean_pesticide_use'], d['mean_concentration_water'],
                               color=color, s=8, alpha=0.4)
                    line = pd.DataFrame({'Pesticide_Name': name,
                                         'log_use': np.linspace(d['log_use'].min(), d['log_use'].max(), 50)})
                    ax.plot(10**line['log_use'], 10**full.predict(line),
                            color=color, linewidth=2.5, label=name)

                ax.set(xscale='log', yscale='log',
                       xlabel='County Pesticide Use, High Estimate (kg)',
                       ylabel='Water Concentration (µg/L)')
                ax.legend(frameon=False, fontsize=9)
                fig.tight_layout()
                return fig

        with ui.card():
            ui.card_header('Before and after accounting for pesticide type')

            @render.table
            def model_compare():
                pooled, full = models()
                return pd.DataFrame({
                    '': ['Use slope', '10× use →', 'R²', 'p-value (use)'],
                    'Use only': [f'{pooled.params["log_use"]:.3f}',
                                 f'{(10**pooled.params["log_use"] - 1) * 100:+.0f}%',
                                 f'{pooled.rsquared:.2f}',
                                 p_label(pooled.pvalues['log_use']).removeprefix('p ')],
                    'Use + type': [f'{full.params["log_use"]:.3f}',
                                   f'{(10**full.params["log_use"] - 1) * 100:+.0f}%',
                                   f'{full.rsquared:.2f}',
                                   p_label(full.pvalues['log_use']).removeprefix('p ')],
                })

            @render.ui
            def model_interpretation():
                pooled, full = models()
                s0, s1 = pooled.params['log_use'], full.params['log_use']
                r0, r1 = pooled.rsquared, full.rsquared
                p1 = full.pvalues['log_use']
                n = len(chosen())
                group = 'the selected pesticides' if n else 'all pesticides'

                # 1. The use effect
                if p1 < 0.05:
                    text = (f'For {group}, a county using 10× more of a pesticide tends to have about '
                            f'**{10**s1:.1f} times** the concentration in its streams '
                            f'({(10**s1 - 1) * 100:+.0f}%, {p_label(p1)}).')
                else:
                    text = (f'For {group}, there is no clear link between county use and stream '
                            f'levels ({p_label(p1)}).')

                # 2. What adding pesticide type changed
                if n == 1:
                    text += ' With one pesticide, type adds nothing, so both models match.'
                elif r1 - r0 < 0.05:
                    text += (' Adding pesticide type barely changes the results, so these pesticides '
                             'sit at similar typical levels and the pattern is mostly about how much is used.')
                else:
                    text += (f' Adding pesticide type raises R² from {r0:.2f} to {r1:.2f}, so which '
                             'pesticide it is explains much of the difference between samples.')
                if abs(s1 - s0) > 0.25 * abs(s0):
                    text += (f' The use slope changes from {s0:.2f} to {s1:.2f} once type is included, '
                             'so part of the use-only trend came from differences between pesticides.')

                # 3. Compared with all pesticides
                if n:
                    s_all = full_all.params['log_use']
                    closer = 'more' if s1 > s_all else 'less'
                    text += (f' These pesticides track county use {closer} closely than pesticides '
                             f'overall ({(10**s_all - 1) * 100:+.0f}% per 10× use).')

                return ui.markdown(text)

    with ui.card(full_screen=True):
        ui.card_header('Which pesticides run higher or lower than expected')
        ui.markdown("""
Typical stream concentration for each pesticide at the same level of use, compared to the
average pesticide (all pesticides in the data). Selected pesticides are highlighted in the
same colors as the chart above. Bars show 95% confidence intervals.
""")

        @render.plot(height=900)
        def pest_effects_plot():
            fig, ax = plt.subplots(figsize=(9, 12))
            d = pest_effects
            colors = dict(zip(chosen(), line_colors))
            point_colors = [colors.get(p, '#9aa5b1') for p in d['pesticide']]

            ax.errorbar(d['times'], d['pesticide'],
                        xerr=[d['times'] - d['low'], d['high'] - d['times']],
                        fmt='none', ecolor='lightgray')
            ax.scatter(d['times'], d['pesticide'], color=point_colors, s=30, zorder=3)
            ax.axvline(1, color='red', linestyle='--', linewidth=1)
            ax.set(xscale='log', xlabel='Times higher or lower than the average pesticide')
            ax.tick_params(axis='y', labelsize=8)
            for label in ax.get_yticklabels():
                if label.get_text() in colors:
                    label.set_fontweight('bold')
                    label.set_color(colors[label.get_text()])
            fig.tight_layout()
            return fig

    with ui.accordion(open=False):
        with ui.accordion_panel('Model details (all pesticides)'):
            ui.markdown("""
**Model:** log10(concentration) ~ log10(county use) + pesticide, ordinary least squares.
Both variables were log10-transformed because they were strongly right-skewed and spanned
several orders of magnitude. Rows with zero county use were dropped. Each row is one
site, pesticide, and year, so sites appear more than once; p-values do not adjust for this
and should be read as somewhat optimistic.
""")
            ui.HTML(full_all.summary().tables[0].as_html())
            ui.HTML(full_all.summary().tables[1].as_html())