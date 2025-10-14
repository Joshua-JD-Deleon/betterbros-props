"""
NFL Props Analyzer - Streamlit Application

Main UI for analyzing NFL player props with advanced modeling and optimization.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
from datetime import datetime
from io import BytesIO
import base64

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_user_prefs, save_user_prefs, get_default_config
from src.ingest import (
    fetch_current_props,
    fetch_current_props_from_odds_api,
    fetch_injury_report,
    fetch_weather_data
)
from src.features import build_features, generate_trend_chips
from src.models import estimate_probabilities
from src.corr import estimate_correlations
from src.optimize import optimize_slips, apply_what_if_adjustments
from src.eval import (
    filter_by_ci_width,
    evaluate_backtest,
    export_props_csv,
    export_slips_csv,
    export_backtest_results_csv,
    record_experiment,
    query_experiments,
    EVENT_TYPES
)
from src.snapshots import lock_snapshot, load_snapshot, list_snapshots, delete_snapshot
from src.keys import keys_set, keys_test, keys_list
from src.share import build_share_zip, list_shares


# Page configuration
st.set_page_config(
    page_title="BetterBros Props",
    page_icon="🏈",
    layout="wide"
)


def apply_theme_css(night_mode: bool = False):
    """
    Apply centralized theme styling with CSS custom properties.

    Uses semantic color variables for maintainability and consistency.
    All colors are defined as CSS custom properties in :root for easy theming.
    """

    # Base theme colors (light theme)
    bg_primary = "#ffffff"        # Pure white background
    bg_secondary = "#f5f5f5"      # Light gray for sidebar/cards
    bg_card = "#fafafa"           # Very light gray for elevated elements
    text_primary = "#1a1a1a"      # Dark gray text
    text_secondary = "#666666"    # Medium gray for secondary text
    border_color = "#e0e0e0"      # Light border

    st.markdown(f"""
        <style>
        /* ========================================
           CSS CUSTOM PROPERTIES (CSS VARIABLES)
           ======================================== */
        :root {{
            /* Base Theme Colors */
            --color-bg-primary: {bg_primary};
            --color-bg-secondary: {bg_secondary};
            --color-bg-card: {bg_card};
            --color-text-primary: {text_primary};
            --color-text-secondary: {text_secondary};
            --color-border: {border_color};

            /* Semantic Status Colors */
            --color-success: #28a745;
            --color-success-bg: rgba(40, 167, 69, 0.1);
            --color-success-border: #28a745;

            --color-warning: #ffc107;
            --color-warning-bg: rgba(255, 193, 7, 0.1);
            --color-warning-border: #ffc107;
            --color-warning-dark: #d39e00;

            --color-danger: #dc3545;
            --color-danger-bg: rgba(220, 53, 69, 0.1);
            --color-danger-border: #dc3545;

            --color-info: #008057;
            --color-info-bg: rgba(0, 128, 87, 0.1);
            --color-info-border: #008057;

            --color-neutral: #6c757d;
            --color-neutral-bg: rgba(108, 117, 125, 0.1);
            --color-neutral-border: #6c757d;

            /* Quick Actions Colors (lighter green) */
            --color-action-primary: #33AA77;
            --color-action-primary-hover: #2A9966;
            --color-action-primary-text: #ffffff;

            /* Spacing & Layout */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;

            /* Border Radius */
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;

            /* Transitions */
            --transition-fast: 150ms ease;
            --transition-normal: 250ms ease;
        }}

        /* ========================================
           GLOBAL LAYOUT
           ======================================== */

        /* Main container */
        [data-testid="stAppViewContainer"] {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
        }}

        /* Reduce top padding in main content area - force with !important */
        section.main > div.block-container,
        [data-testid="stAppViewContainer"] section.main > div.block-container,
        div[data-testid="stAppViewContainer"] > div > section.main > div.block-container {{
            padding-top: 0rem !important;
            padding-bottom: 1rem !important;
        }}

        /* Remove top margin from first heading */
        .block-container h1:first-child {{
            margin-top: 0 !important;
            padding-top: 0.5rem !important;
        }}

        /* Hide sidebar completely for app-like layout */
        [data-testid="stSidebar"] {{
            display: none !important;
        }}

        /* Expand main content to full width */
        [data-testid="stAppViewContainer"] .main {{
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}

        /* ========================================
           TYPOGRAPHY
           ======================================== */

        body, p, span, div, label {{
            color: var(--color-text-primary);
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--color-text-primary);
        }}

        /* Field labels - bold */
        label {{
            font-weight: 700 !important;
        }}

        /* Streamlit widget labels */
        .stSelectbox label,
        .stNumberInput label,
        .stSlider label,
        .stMultiSelect label,
        .stTextInput label,
        .stTextArea label,
        .stCheckbox label,
        .stRadio label,
        [data-testid="stWidgetLabel"] {{
            font-weight: 700 !important;
        }}

        /* Additional slider label specificity */
        .stSlider > label,
        .stSlider div[data-testid="stWidgetLabel"],
        div[data-baseweb="slider"] ~ label,
        [data-testid="stSlider"] label {{
            font-weight: 700 !important;
        }}

        /* Align slider bar with label */
        .stSlider [data-baseweb="slider"] {{
            padding-left: 0 !important;
        }}

        .stSlider > div {{
            padding-left: 0 !important;
        }}

        /* Reduce horizontal length of all bars (sliders, number inputs, etc) */
        .stSlider,
        .stNumberInput,
        .stTextInput,
        .stSelectbox {{
            max-width: 80% !important;
        }}

        .stSlider > div,
        .stNumberInput > div,
        .stTextInput > div {{
            max-width: 100% !important;
        }}

        /* Ensure all fields align properly on left */
        .stSlider,
        .stNumberInput,
        .stTextInput,
        .stSelectbox,
        .stMultiSelect {{
            margin-left: 0 !important;
            padding-left: 0 !important;
        }}

        /* ========================================
           SECTION HEADERS
           ======================================== */

        /* Section headers (subheaders) with background color - not h1 title */
        .block-container h2,
        .block-container h3,
        div[data-testid="stSubheader"],
        .element-container h2,
        .element-container h3,
        [data-testid="stTabPanel"] h2 {{
            background-color: #D9D8DF !important;
            padding: 0.75rem 1rem !important;
            border-radius: var(--radius-md) !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }}

        /* Ensure text in headers is visible */
        div[data-testid="stSubheader"],
        .block-container h2,
        .block-container h3,
        [data-testid="stTabPanel"] h2,
        [data-testid="stTabPanel"] h3 {{
            color: var(--color-text-primary) !important;
        }}

        /* Tab panel headers use standard font size, not larger */
        [data-testid="stTabPanel"] h2,
        [data-testid="stTabPanel"] h3,
        [data-testid="stTabPanel"] div[data-testid="stSubheader"] {{
            font-size: 1rem;
            font-weight: 700;
        }}

        /* Hide the link button next to main title */
        h1 [data-testid="stHeaderActionElements"],
        .block-container h1:first-child [data-testid="stHeaderActionElements"] {{
            display: none !important;
        }}

        /* ========================================
           SECTION CONTAINERS (EXPANDERS)
           ======================================== */

        /* Expander container - consistent padding all around */
        [data-testid="stExpander"],
        div[data-testid="stExpander"] {{
            padding: 0 !important;
        }}

        /* Expander content area - equal left and right padding */
        [data-testid="stExpander"] details > div,
        details[data-testid="stExpander"] > div,
        div[data-testid="stExpander"] > div,
        [data-testid="stExpander"] [data-testid="stExpanderDetails"],
        details > div:last-child {{
            padding: 1.5rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}

        /* Ensure all content within expanders aligns properly - no extra padding */
        [data-testid="stExpander"] .element-container,
        [data-testid="stExpander"] .stColumn,
        [data-testid="stExpander"] [data-testid="column"] {{
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
        }}

        /* Ensure columns within expanders have no extra padding */
        [data-testid="stExpander"] [data-testid="column"] > div,
        [data-testid="stExpander"] [data-testid="column"] div {{
            padding-left: 0 !important;
            padding-right: 0 !important;
        }}

        /* Remove gaps between columns within expanders */
        [data-testid="stExpander"] [data-testid="column"] {{
            gap: 0 !important;
        }}

        /* Ensure horizontal layout within expanders has no gaps */
        [data-testid="stExpander"] [data-testid="stHorizontalBlock"] {{
            gap: 1rem !important;
        }}

        /* Align all form elements flush with container */
        [data-testid="stExpander"] .stSlider,
        [data-testid="stExpander"] .stNumberInput,
        [data-testid="stExpander"] .stTextInput,
        [data-testid="stExpander"] .stSelectbox,
        [data-testid="stExpander"] .stMultiSelect {{
            width: 100% !important;
        }}

        /* ========================================
           FORM CONTROLS
           ======================================== */

        /* Input fields */
        input, select, textarea {{
            color: var(--color-text-primary);
            background-color: transparent !important;
        }}

        /* Number input fields - transparent background */
        .stNumberInput input {{
            background-color: transparent !important;
        }}

        .stNumberInput > div > div {{
            background-color: transparent !important;
        }}

        .stNumberInput [data-baseweb="input"] {{
            background-color: transparent !important;
        }}

        .stNumberInput [data-baseweb="input"] > div {{
            background-color: transparent !important;
        }}

        /* Number input +/- buttons - remove default colors */
        section.main div.stNumberInput button,
        [data-testid="stAppViewContainer"] div.stNumberInput button,
        div[data-testid="stAppViewContainer"] section.main div.stNumberInput button {{
            background-color: transparent;
            border: 1px solid var(--color-border);
            transition: background-color var(--transition-fast);
        }}

        section.main div.stNumberInput button:hover,
        [data-testid="stAppViewContainer"] div.stNumberInput button:hover,
        div[data-testid="stAppViewContainer"] section.main div.stNumberInput button:hover {{
            background-color: var(--color-info);
            color: white;
            border-color: var(--color-info);
        }}

        section.main div.stNumberInput button:active,
        [data-testid="stAppViewContainer"] div.stNumberInput button:active,
        div[data-testid="stAppViewContainer"] section.main div.stNumberInput button:active {{
            background-color: #006844;
            color: white;
            border-color: #006844;
        }}

        /* Number input field - remove default focus colors */
        section.main div.stNumberInput input,
        section.main div.stNumberInput div[data-baseweb="input"],
        [data-testid="stAppViewContainer"] div.stNumberInput input {{
            border-color: var(--color-border);
            outline: none;
        }}

        section.main div.stNumberInput input:focus,
        section.main div.stNumberInput div[data-baseweb="input"]:focus-within,
        [data-testid="stAppViewContainer"] div.stNumberInput input:focus,
        [data-testid="stAppViewContainer"] div.stNumberInput div[data-baseweb="input"]:focus-within {{
            border-color: var(--color-info);
            box-shadow: 0 0 0 1px var(--color-info);
            outline: none;
        }}

        /* Remove default red outlines from all inputs */
        input:focus,
        textarea:focus,
        select:focus,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"]:focus-within {{
            outline: none;
        }}

        /* Select boxes - white backgrounds and rounded corners */
        .stSelectbox div[data-baseweb="select"] {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
            border-radius: var(--radius-md);
        }}

        .stSelectbox div[data-baseweb="select"] > div {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
            border-radius: var(--radius-md);
        }}

        .stSelectbox div[data-baseweb="select"] div {{
            background-color: var(--color-bg-primary);
            border-radius: var(--radius-md);
        }}

        div[data-baseweb="select"] {{
            background-color: var(--color-bg-primary);
            border-radius: var(--radius-md);
        }}

        /* Selectbox - remove default focus colors, apply green */
        section.main div.stSelectbox div[data-baseweb="select"],
        [data-testid="stAppViewContainer"] div.stSelectbox div[data-baseweb="select"] {{
            border: 1px solid var(--color-border);
        }}

        section.main div.stSelectbox div[data-baseweb="select"]:focus-within,
        section.main div.stSelectbox div[data-baseweb="select"][aria-expanded="true"],
        [data-testid="stAppViewContainer"] div.stSelectbox div[data-baseweb="select"]:focus-within,
        [data-testid="stAppViewContainer"] div.stSelectbox div[data-baseweb="select"][aria-expanded="true"] {{
            border-color: var(--color-info);
            box-shadow: 0 0 0 1px var(--color-info);
            outline: none;
        }}

        /* Multiselect - remove default focus colors, apply green */
        section.main div.stMultiSelect div[data-baseweb="select"],
        [data-testid="stAppViewContainer"] div.stMultiSelect div[data-baseweb="select"] {{
            border: 1px solid var(--color-border);
        }}

        section.main div.stMultiSelect div[data-baseweb="select"]:focus-within,
        section.main div.stMultiSelect div[data-baseweb="select"][aria-expanded="true"],
        [data-testid="stAppViewContainer"] div.stMultiSelect div[data-baseweb="select"]:focus-within,
        [data-testid="stAppViewContainer"] div.stMultiSelect div[data-baseweb="select"][aria-expanded="true"] {{
            border-color: var(--color-info);
            box-shadow: 0 0 0 1px var(--color-info);
            outline: none;
        }}

        /* Text input - remove default focus colors, apply green */
        section.main div.stTextInput input,
        section.main div.stTextInput div[data-baseweb="input"],
        section.main div.stTextArea textarea,
        [data-testid="stAppViewContainer"] div.stTextInput input,
        [data-testid="stAppViewContainer"] div.stTextArea textarea {{
            border: 1px solid var(--color-border);
        }}

        section.main div.stTextInput input:focus,
        section.main div.stTextInput div[data-baseweb="input"]:focus-within,
        section.main div.stTextArea textarea:focus,
        [data-testid="stAppViewContainer"] div.stTextInput input:focus,
        [data-testid="stAppViewContainer"] div.stTextInput div[data-baseweb="input"]:focus-within,
        [data-testid="stAppViewContainer"] div.stTextArea textarea:focus {{
            border-color: var(--color-info);
            box-shadow: 0 0 0 1px var(--color-info);
            outline: none;
        }}

        /* Dropdown menu hover effects - match +/- button styling with high specificity */

        /* Dropdown options - hover effect with green background and white text */
        [data-testid="stAppViewContainer"] div[data-baseweb="popover"] div[role="option"]:hover,
        [data-testid="stAppViewContainer"] div[data-baseweb="popover"] li[role="option"]:hover,
        section.main div.stSelectbox div[data-baseweb="menu"] div[role="option"]:hover,
        section.main div.stSelectbox div[data-baseweb="menu"] li[role="option"]:hover,
        [data-baseweb="popover"] div[data-baseweb="menu"] div[role="option"]:hover,
        [data-baseweb="popover"] div[data-baseweb="menu"] li[role="option"]:hover {{
            background-color: var(--color-info);
            color: white;
            transition: background-color var(--transition-fast), color var(--transition-fast);
        }}

        /* Additional specificity for list options */
        div[data-baseweb="popover"] ul[role="listbox"] > li:hover,
        div[data-baseweb="popover"] div[role="listbox"] > div:hover {{
            background-color: var(--color-info);
            color: white;
        }}

        /* Selected option styling */
        [data-baseweb="popover"] div[data-baseweb="menu"] div[aria-selected="true"],
        [data-baseweb="popover"] div[data-baseweb="menu"] li[aria-selected="true"] {{
            background-color: var(--color-info-bg);
            color: var(--color-text-primary);
        }}

        /* Selected option on hover - darker green */
        [data-baseweb="popover"] div[data-baseweb="menu"] div[aria-selected="true"]:hover,
        [data-baseweb="popover"] div[data-baseweb="menu"] li[aria-selected="true"]:hover {{
            background-color: #006844;
            color: white;
        }}

        /* Override Streamlit's default blue for dropdown arrows only, not help icons */
        .stSelectbox div[data-baseweb="select"] > div > div > svg,
        [data-baseweb="select"] > div > div > svg {{
            color: var(--color-text-primary) !important;
            fill: var(--color-text-primary) !important;
        }}

        /* Dropdown menus */
        div[role="listbox"],
        ul[role="listbox"] {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
        }}

        div[role="option"],
        li[role="option"] {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
        }}

        /* Multiselect selected items (tags) with higher specificity */
        section.main div.stMultiSelect div[data-baseweb="tag"] {{
            background-color: var(--color-info);
            color: white;
        }}

        section.main div.stMultiSelect div[data-baseweb="tag"] span {{
            color: white;
        }}

        /* Multiselect dropdown options hover effects */
        [data-testid="stAppViewContainer"] div.stMultiSelect div[data-baseweb="popover"] div[role="option"]:hover,
        [data-testid="stAppViewContainer"] div.stMultiSelect div[data-baseweb="popover"] li[role="option"]:hover {{
            background-color: var(--color-info);
            color: white;
            transition: background-color var(--transition-fast), color var(--transition-fast);
        }}

        /* Multiselect selected options in dropdown */
        section.main div.stMultiSelect div[data-baseweb="popover"] div[aria-selected="true"],
        section.main div.stMultiSelect div[data-baseweb="popover"] li[aria-selected="true"] {{
            background-color: var(--color-info-bg);
            color: var(--color-text-primary);
        }}

        section.main div.stMultiSelect div[data-baseweb="popover"] div[aria-selected="true"]:hover,
        section.main div.stMultiSelect div[data-baseweb="popover"] li[aria-selected="true"]:hover {{
            background-color: #006844;
            color: white;
        }}

        /* ========================================
           SLIDERS & INPUTS - Strategic !important only on colors
           ======================================== */

        /* GLOBAL: Remove ALL red colors completely */
        * {{
            accent-color: var(--color-info) !important;
        }}

        /* Remove highlighted backgrounds from all slider containers */
        div.stSlider,
        div.stSlider > div,
        div.stSlider > label {{
            background-color: transparent !important;
            background: transparent !important;
        }}

        /* Slider thumb - green only (all states) */
        div.stSlider div[data-baseweb="slider"] div[role="slider"],
        div.stSlider div[data-baseweb="slider"] div[role="slider"][aria-valuenow],
        div[data-baseweb="slider"] div[role="slider"],
        div[data-baseweb="slider"] div[role="slider"][aria-valuenow] {{
            background-color: var(--color-info) !important;
            background: var(--color-info) !important;
            border: 2px solid var(--color-info) !important;
            transition: background-color var(--transition-fast), border-color var(--transition-fast);
        }}

        /* Slider track - gray (all instances) */
        div.stSlider div[data-baseweb="slider"] > div:first-child,
        div[data-baseweb="slider"] > div:first-child {{
            background-color: #e0e0e0 !important;
            background: #e0e0e0 !important;
        }}

        /* Slider track fill - green only (all instances) */
        div.stSlider div[data-baseweb="slider"] > div > div,
        div.stSlider div[data-baseweb="slider"] > div > div > div,
        div[data-baseweb="slider"] > div > div,
        div[data-baseweb="slider"] > div > div > div {{
            background-color: var(--color-info) !important;
            background: var(--color-info) !important;
        }}

        /* Slider hover - darker green (all instances) */
        div.stSlider div[data-baseweb="slider"] div[role="slider"]:hover,
        div[data-baseweb="slider"] div[role="slider"]:hover {{
            background-color: #006844 !important;
            background: #006844 !important;
            border-color: #006844 !important;
        }}

        /* Slider active/focus - darker green (all instances and states) */
        div.stSlider div[data-baseweb="slider"] div[role="slider"]:active,
        div.stSlider div[data-baseweb="slider"] div[role="slider"]:focus,
        div.stSlider div[data-baseweb="slider"] div[role="slider"][aria-valuenow]:active,
        div[data-baseweb="slider"] div[role="slider"]:active,
        div[data-baseweb="slider"] div[role="slider"]:focus,
        div[data-baseweb="slider"] div[role="slider"][aria-valuenow]:focus {{
            background-color: #006844 !important;
            background: #006844 !important;
            border-color: #006844 !important;
        }}

        /* ALL INPUT FIELDS: Remove red, force green borders only */
        input:focus,
        textarea:focus,
        select:focus,
        input:focus-visible,
        textarea:focus-visible,
        select:focus-visible {{
            outline: none !important;
            outline-width: 0 !important;
            outline-style: none !important;
            outline-color: transparent !important;
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 1px var(--color-info) !important;
        }}

        /* ALL BASEWEB INPUTS: Remove red, force green borders only */
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"]:focus-within,
        div[data-baseweb="base-input"]:focus-within {{
            outline: none !important;
            outline-width: 0 !important;
            outline-style: none !important;
            outline-color: transparent !important;
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 1px var(--color-info) !important;
        }}

        /* Number inputs: Remove red entirely */
        .stNumberInput input:focus,
        .stNumberInput div[data-baseweb="input"]:focus-within,
        .stNumberInput input:focus-visible {{
            outline: none !important;
            outline-width: 0 !important;
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 1px var(--color-info) !important;
        }}

        /* Text inputs: Remove red entirely */
        .stTextInput input:focus,
        .stTextInput div[data-baseweb="input"]:focus-within,
        .stTextInput input:focus-visible {{
            outline: none !important;
            outline-width: 0 !important;
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 1px var(--color-info) !important;
        }}

        /* Selectboxes: Remove red entirely */
        .stSelectbox div[data-baseweb="select"]:focus-within,
        .stSelectbox div[data-baseweb="select"][aria-expanded="true"] {{
            outline: none !important;
            outline-width: 0 !important;
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 1px var(--color-info) !important;
        }}

        /* Multiselect: Remove red entirely */
        .stMultiSelect div[data-baseweb="select"]:focus-within,
        .stMultiSelect div[data-baseweb="select"][aria-expanded="true"] {{
            outline: none !important;
            outline-width: 0 !important;
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 1px var(--color-info) !important;
        }}

        /* ========================================
           METRICS & CARDS
           ======================================== */

        /* Metric components */
        .stMetric {{
            background-color: var(--color-bg-card);
            padding: 10px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--color-border);
        }}

        .stMetric label {{
            color: var(--color-text-secondary);
        }}

        .stMetric [data-testid="stMetricValue"] {{
            color: var(--color-text-primary);
        }}

        /* Prop cards */
        .prop-card {{
            background-color: var(--color-bg-card);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 12px;
        }}

        /* ========================================
           TREND CHIPS (Semantic Status Colors)
           ======================================== */

        .trend-chip {{
            border-radius: var(--radius-md);
            padding: 12px;
            margin: 8px 0;
        }}

        .trend-chip-positive {{
            background-color: var(--color-success-bg);
            border-left: 4px solid var(--color-success-border);
        }}

        .trend-chip-negative {{
            background-color: var(--color-danger-bg);
            border-left: 4px solid var(--color-danger-border);
        }}

        .trend-chip-neutral {{
            background-color: var(--color-warning-bg);
            border-left: 4px solid var(--color-warning-border);
        }}

        /* ========================================
           EV BOXES (Expected Value Indicators)
           ======================================== */

        .ev-box {{
            padding: 12px;
            border-radius: var(--radius-md);
            text-align: center;
            border: 1px solid;
            transition: transform var(--transition-fast);
        }}

        .ev-box:hover {{
            transform: scale(1.02);
        }}

        .ev-high {{
            background-color: var(--color-success-bg);
            border-color: var(--color-success-border);
            color: var(--color-success);
        }}

        .ev-medium {{
            background-color: var(--color-warning-bg);
            border-color: var(--color-warning-border);
            color: var(--color-warning-dark);
        }}

        .ev-low {{
            background-color: var(--color-danger-bg);
            border-color: var(--color-danger-border);
            color: var(--color-danger);
        }}

        /* ========================================
           DATA TABLES
           ======================================== */

        .dataframe {{
            color: var(--color-text-primary);
            background-color: var(--color-bg-primary);
        }}

        .dataframe th {{
            background-color: var(--color-bg-card);
            color: var(--color-text-primary);
        }}

        .dataframe td {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
        }}

        /* ========================================
           TABS & NAVIGATION
           ======================================== */

        .stTabs [data-baseweb="tab"] {{
            color: var(--color-text-primary);
        }}

        /* ========================================
           BUTTONS
           ======================================== */

        /* All buttons */
        .stButton button {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
            border: 1px solid var(--color-border);
            transition: all var(--transition-normal);
        }}

        .stButton button:hover {{
            background-color: var(--color-bg-card);
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        /* Primary buttons - ensure white text with high specificity */
        .stButton button[kind="primary"],
        section.main .stButton button[kind="primary"],
        [data-testid="stAppViewContainer"] .stButton button[kind="primary"] {{
            background-color: var(--color-info);
            color: white;
            border: none;
        }}

        .stButton button[kind="primary"]:hover,
        section.main .stButton button[kind="primary"]:hover,
        [data-testid="stAppViewContainer"] .stButton button[kind="primary"]:hover {{
            background-color: #006844;
            color: white;
        }}

        /* Button text - force white color on primary buttons */
        .stButton button[kind="primary"] p,
        .stButton button[kind="primary"] span,
        section.main .stButton button[kind="primary"] p,
        section.main .stButton button[kind="primary"] span {{
            color: white;
        }}

        /* Download buttons */
        .stDownloadButton button {{
            background-color: var(--color-bg-primary);
            color: var(--color-text-primary);
            border: 1px solid var(--color-border);
        }}

        .stDownloadButton button:hover {{
            background-color: var(--color-bg-card);
        }}

        /* ========================================
           CAPTIONS & HELPER TEXT
           ======================================== */

        .stCaption {{
            color: var(--color-text-secondary);
        }}

        /* ========================================
           CONTENT CARDS & CONTAINERS
           ======================================== */

        .content-card {{
            background-color: var(--color-bg-card);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
        }}

        .content-card h2, .content-card h3 {{
            margin-top: 0;
            color: var(--color-text-primary);
        }}

        /* ========================================
           HELP ICONS
           ======================================== */

        /* Fix help icon (?) display - override aggressive SVG rules */
        .stTooltipIcon svg,
        [data-testid="stTooltipIcon"] svg {{
            color: #666666 !important;
        }}

        /* Exclude help icons from the aggressive dropdown SVG overrides */
        .stSelectbox svg:not(.stTooltipIcon svg),
        [data-baseweb="select"] svg:not(.stTooltipIcon svg) {{
            color: var(--color-text-primary) !important;
            fill: var(--color-text-primary) !important;
        }}

        /* ========================================
           COLUMN ALIGNMENT
           ======================================== */

        /* Right-align content in the fourth column of 4-column layouts */
        section.main div[data-testid="column"]:nth-child(4) {{
            text-align: right;
        }}

        /* Ensure input fields themselves remain properly sized */
        section.main div[data-testid="column"]:nth-child(4) input,
        section.main div[data-testid="column"]:nth-child(4) div[data-baseweb="select"],
        section.main div[data-testid="column"]:nth-child(4) .stSelectbox {{
            text-align: left;
        }}

        /* Right-align labels in fourth column */
        section.main div[data-testid="column"]:nth-child(4) label {{
            display: block;
            text-align: right;
        }}

        /* ========================================
           TAB STYLING - MATCH EXPANDERS
           ======================================== */

        /* Tab panel content area - consistent padding like expanders */
        [data-testid="stTabPanel"] {{
            padding: 1.5rem !important;
            background-color: var(--color-bg-card);
            border-radius: var(--radius-md);
            margin-top: 0.5rem;
        }}

        /* Ensure tab content aligns properly */
        [data-testid="stTabPanel"] .element-container,
        [data-testid="stTabPanel"] .stColumn,
        [data-testid="stTabPanel"] [data-testid="column"] {{
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
        }}

        /* ========================================
           PHASE 1 UX ENHANCEMENTS
           ======================================== */

        /* Quick Actions Bar - sticky at top */
        .quick-actions-bar {{
            position: sticky;
            top: 0;
            z-index: 100;
            background-color: var(--color-bg-primary);
            padding: 1rem 0;
            border-bottom: 2px solid var(--color-border);
            margin-bottom: 1rem;
        }}

        /* Quick Actions buttons - enhanced styling */
        button[data-testid="baseButton-primary"] {{
            background-color: var(--color-info) !important;
            border-color: var(--color-info) !important;
            transition: all var(--transition-fast);
        }}

        button[data-testid="baseButton-primary"]:hover {{
            background-color: #006644 !important;
            border-color: #006644 !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Quick Actions buttons - green border with transparent background */
        .quick-actions-wrapper button[data-testid="baseButton-primary"] {{
            background-color: transparent !important;
            border: 2px solid var(--color-action-primary) !important;
            color: var(--color-action-primary) !important;
            font-size: 18px;
        }}

        .quick-actions-wrapper button[data-testid="baseButton-primary"]:hover {{
            background-color: rgba(51, 170, 119, 0.1) !important;
            border-color: var(--color-action-primary-hover) !important;
            color: var(--color-action-primary-hover) !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Secondary buttons for filter chips */
        button[data-testid="baseButton-secondary"] {{
            background-color: transparent !important;
            border: 2px solid #e0e0e0 !important;
            color: var(--color-text-primary) !important;
            transition: all var(--transition-fast);
        }}

        button[data-testid="baseButton-secondary"]:hover {{
            background-color: #f5f5f5 !important;
            border-color: #c0c0c0 !important;
        }}

        /* Search bar styling */
        .stTextInput input {{
            font-size: 16px !important;
            padding: 12px !important;
            border: 2px solid #e0e0e0 !important;
            border-radius: var(--radius-md) !important;
            transition: border-color var(--transition-fast);
        }}

        .stTextInput input:focus {{
            border-color: var(--color-info) !important;
            box-shadow: 0 0 0 3px rgba(0, 128, 87, 0.1) !important;
        }}

        /* Filter chips container */
        .filter-chips {{
            display: flex;
            gap: 0.5rem;
            margin: 0.5rem 0;
            flex-wrap: wrap;
        }}

        /* Favorite star button styling */
        button[key*="fav_"] {{
            font-size: 20px !important;
            padding: 0 !important;
            min-height: 30px !important;
            background: transparent !important;
            border: none !important;
        }}

        button[key*="fav_"]:hover {{
            transform: scale(1.2);
            transition: transform var(--transition-fast);
        }}

        /* Search result count caption */
        .search-results-count {{
            font-size: 14px;
            color: var(--color-text-secondary);
            margin: 0.5rem 0;
        }}

        /* Sorting controls */
        .sort-controls {{
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
            align-items: center;
        }}

        /* Keyboard shortcuts modal */
        .shortcuts-modal {{
            background-color: var(--color-bg-card);
            border: 2px solid var(--color-info);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin: 1rem 0;
        }}

        /* Shortcuts table */
        .shortcuts-modal table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .shortcuts-modal td, .shortcuts-modal th {{
            padding: 0.5rem;
            border-bottom: 1px solid var(--color-border);
        }}

        .shortcuts-modal code {{
            background-color: #f5f5f5;
            padding: 0.2rem 0.5rem;
            border-radius: var(--radius-sm);
            font-family: 'Courier New', monospace;
            font-weight: 600;
        }}

        /* Progress indicators */
        .progress-indicator {{
            display: inline-block;
            margin: 0 0.5rem;
        }}

        /* Enhanced expander headers with step numbers */
        [data-testid="stExpander"] summary {{
            font-size: 18px !important;
            font-weight: 600 !important;
            padding: 1rem !important;
        }}

        /* Visual hierarchy - step numbers */
        [data-testid="stExpander"] summary::before {{
            margin-right: 0.5rem;
        }}

        /* Horizontal rule styling */
        hr {{
            border: none;
            border-top: 2px solid var(--color-border);
            margin: 1.5rem 0;
        }}

        /* Toast/notification styling */
        .stToast {{
            background-color: var(--color-bg-card) !important;
            border-left: 4px solid var(--color-info) !important;
        }}

        /* Hide theme chooser in Settings menu */
        button[data-testid="stToolbarActionButton"]:last-child > div > div {{
            pointer-events: none;
        }}
        button[data-testid="stToolbarActionButton"]:last-child > div > div > div:nth-child(2) {{
            display: none !important;
        }}
        </style>
        """, unsafe_allow_html=True)


def load_config():
    """Load user preferences."""
    try:
        return load_user_prefs("user_prefs.yaml")
    except:
        return get_default_config()


def initialize_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = load_config()
    if 'props_df' not in st.session_state:
        st.session_state.props_df = None
    if 'slips' not in st.session_state:
        st.session_state.slips = []
    if 'snapshot_id' not in st.session_state:
        st.session_state.snapshot_id = None
    if 'corr_matrix' not in st.session_state:
        st.session_state.corr_matrix = None
    if 'manual_slip' not in st.session_state:
        st.session_state.manual_slip = []
    if 'what_if_adjustments' not in st.session_state:
        st.session_state.what_if_adjustments = {}
    if 'night_mode' not in st.session_state:
        st.session_state.night_mode = False
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None

    # Phase 1 UX Enhancement Features
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'quick_filters' not in st.session_state:
        st.session_state.quick_filters = []
    if 'favorited_props' not in st.session_state:
        st.session_state.favorited_props = set()
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = "ev"
    if 'sort_direction' not in st.session_state:
        st.session_state.sort_direction = "desc"
    if 'show_shortcuts_modal' not in st.session_state:
        st.session_state.show_shortcuts_modal = False
    if 'show_guide_modal' not in st.session_state:
        st.session_state.show_guide_modal = False



def render_calibration_banner():
    """Render calibration monitoring banner."""
    try:
        # Query recent experiments for calibration metrics
        recent_experiments = query_experiments(
            filters={'event_type': EVENT_TYPES['CALIBRATION_CHECK']},
            limit=10
        )

        if not recent_experiments.empty and 'metrics' in recent_experiments.columns:
            # Extract calibration metrics
            metrics_list = recent_experiments['metrics'].tolist()

            if metrics_list:
                # Calculate rolling metrics
                ece_values = [m.get('ece', 0) for m in metrics_list if isinstance(m, dict)]
                brier_values = [m.get('brier_score', 0) for m in metrics_list if isinstance(m, dict)]

                if ece_values:
                    latest_ece = ece_values[0]
                    avg_ece = np.mean(ece_values)
                    ece_trend = latest_ece - avg_ece

                    # Determine status
                    if latest_ece < 0.1:
                        status = "🟢 Good"
                        color = "green"
                    elif latest_ece < 0.15:
                        status = "🟡 Warning"
                        color = "orange"
                    else:
                        status = "🔴 Alert"
                        color = "red"

                    # Show banner
                    if ece_trend > 0.02:
                        st.warning(f"Calibration Status: {status} | ECE: {latest_ece:.3f} | Brier: {brier_values[0]:.3f} | Trend: ↑ {ece_trend:.3f}")
                    else:
                        st.info(f"Calibration Status: {status} | ECE: {latest_ece:.3f} | Brier: {brier_values[0]:.3f} | Trend: ↓ {abs(ece_trend):.3f}")
    except Exception as e:
        # Silently fail if calibration data not available
        pass


def render_trend_chips(trends):
    """Render trend chips with diagnostics."""
    if not trends:
        return


    # Create columns for trends
    n_trends = len(trends)
    cols = st.columns(min(n_trends, 4))

    for idx, trend in enumerate(trends):
        col = cols[idx % len(cols)]
        with col:
            # Determine CSS class based on impact direction
            if trend['impact_direction'] == "positive":
                css_class = "trend-chip-positive"
            elif trend['impact_direction'] == "negative":
                css_class = "trend-chip-negative"
            else:
                css_class = "trend-chip-neutral"

            # Render card using standardized CSS (no icons)
            st.markdown(f"""
            <div class="trend-chip {css_class}">
                <h4>{trend['title']}</h4>
                <p>{trend['description']}</p>
                <p><small>Confidence: {trend['confidence']:.0%}</small></p>
            </div>
            """, unsafe_allow_html=True)

            # Expandable diagnostics
            with st.expander("View Details"):
                st.json(trend['diagnostics'])

                # Show impacted props if available
                if 'affected_props' in trend['diagnostics']:
                    st.caption("Impacted Props:")
                    for prop in trend['diagnostics']['affected_props'][:5]:
                        st.caption(f"  • {prop}")


def render_prop_cards(props_df):
    """Render prop cards in grid layout."""
    if props_df is None or len(props_df) == 0:
        st.warning("No props available")
        return

    # Add filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        position_filter = st.multiselect(
            "Position",
            options=props_df['position'].unique().tolist() if 'position' in props_df.columns else [],
            default=[]
        )
    with col2:
        prop_type_filter = st.multiselect(
            "Prop Type",
            options=props_df['prop_type'].unique().tolist() if 'prop_type' in props_df.columns else [],
            default=[]
        )
    with col3:
        # Game selector with game times
        game_filter = []
        if 'away_team' in props_df.columns and 'home_team' in props_df.columns:
            # Create unique game matchups with times
            game_cols = ['away_team', 'home_team']
            if 'game_time' in props_df.columns:
                game_cols.append('game_time')

            games_df = props_df[game_cols].drop_duplicates()

            game_options = []
            for _, row in games_df.iterrows():
                matchup = f"{row['away_team']} @ {row['home_team']}"

                # Add game time if available - with capitalized day
                if 'game_time' in row and row['game_time'] is not None:
                    try:
                        import pytz
                        # Parse game_time
                        if isinstance(row['game_time'], str):
                            game_dt = datetime.fromisoformat(row['game_time'].replace('Z', '+00:00'))
                        else:
                            game_dt = row['game_time']

                        # Convert to local timezone
                        local_tz = pytz.timezone('America/New_York')
                        game_dt_local = game_dt.astimezone(local_tz)
                        # Format with capitalized day
                        day_str = game_dt_local.strftime('%a')  # Get day
                        time_str = game_dt_local.strftime('%m/%d %I:%M%p').lower()

                        # Capitalize first letter of day
                        day_str = day_str.capitalize()

                        # Format: Teams | Day - Time (compact on one line since newlines don't work in multiselect)
                        matchup = f"{matchup} | {day_str} - {time_str}"
                    except:
                        pass  # If time parsing fails, just show matchup

                game_options.append(matchup)

            game_options = sorted(game_options)

            game_filter = st.multiselect(
                "Game",
                options=game_options,
                default=[]
            )

    with col4:
        sort_by = st.selectbox("Sort By", ["EV", "Probability", "Player Name", "Game Time"])

    # Apply filters
    filtered_df = props_df.copy()
    if position_filter and 'position' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['position'].isin(position_filter)]
    if prop_type_filter and 'prop_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['prop_type'].isin(prop_type_filter)]

    # Apply game filter
    if game_filter and 'away_team' in filtered_df.columns and 'home_team' in filtered_df.columns:
        # Filter by selected game matchups
        game_matches = []
        for selected_game in game_filter:
            # Parse "Away Team @ Home Team | Day - time" or "Away Team @ Home Team" format
            # Remove time portion if present (anything after " | ")
            if ' | ' in selected_game:
                matchup = selected_game.split(' | ')[0].strip()
            else:
                matchup = selected_game

            if ' @ ' in matchup:
                away, home = matchup.split(' @ ')
                # Filter props matching this game
                game_mask = (filtered_df['away_team'] == away.strip()) & (filtered_df['home_team'] == home.strip())
                game_matches.append(game_mask)

        # Combine all game masks with OR
        if game_matches:
            combined_mask = game_matches[0]
            for mask in game_matches[1:]:
                combined_mask = combined_mask | mask
            filtered_df = filtered_df[combined_mask]

    # Calculate EV for sorting
    if 'over_odds' in filtered_df.columns and 'prob_over' in filtered_df.columns:
        filtered_df['ev'] = filtered_df.apply(
            lambda row: row['prob_over'] * (1 + abs(row['over_odds']) / 100) if row['over_odds'] < 0
            else row['prob_over'] * (1 + row['over_odds'] / 100),
            axis=1
        )
    else:
        filtered_df['ev'] = 1.0

    # Sort
    if sort_by == "EV":
        filtered_df = filtered_df.sort_values('ev', ascending=False)
    elif sort_by == "Probability":
        filtered_df = filtered_df.sort_values('prob_over', ascending=False)
    elif sort_by == "Game Time":
        if 'game_time' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('game_time', ascending=True)
        else:
            st.warning("Game time data not available")
            filtered_df = filtered_df.sort_values('player_name')
    else:
        filtered_df = filtered_df.sort_values('player_name')

    st.caption(f"Showing {len(filtered_df)} of {len(props_df)} props")

    # Create grid layout (3 columns)
    n_cols = 3
    rows = [filtered_df.iloc[i:i+n_cols] for i in range(0, len(filtered_df), n_cols)]

    for row in rows:
        cols = st.columns(n_cols)
        for col, (idx, prop) in zip(cols, row.iterrows()):
            with col:
                # Determine badges
                badges = []
                ci_width = prop.get('ci_upper', 1) - prop.get('ci_lower', 0)

                if prop['ev'] > 1.08:
                    badges.append("HIGH_EDGE")
                if ci_width > 0.2:
                    badges.append("HIGH_UNCERTAINTY")

                # Card container
                with st.container():
                    # Favorite button and player name
                    col_star, col_name = st.columns([1, 11])

                    with col_star:
                        prop_id = f"{prop['player_name']}_{prop['prop_type']}"
                        is_favorited = prop_id in st.session_state.favorited_props

                        if st.button(
                            "⭐" if is_favorited else "☆",
                            key=f"fav_{idx}_{prop['player_name']}_{prop['prop_type']}",
                            help="Add to favorites"
                        ):
                            if is_favorited:
                                st.session_state.favorited_props.remove(prop_id)
                            else:
                                st.session_state.favorited_props.add(prop_id)
                            st.rerun()

                    with col_name:
                        st.markdown(f"### {prop['player_name']}")

                    st.caption(f"{prop['position']} - {prop['team']}" if 'position' in prop and 'team' in prop else "")

                    # Show game time and matchup if available
                    if 'game_time' in prop and prop['game_time'] is not None:
                        try:
                            from datetime import datetime
                            import pytz
                            # Parse game_time if it's a string
                            if isinstance(prop['game_time'], str):
                                game_dt = datetime.fromisoformat(prop['game_time'].replace('Z', '+00:00'))
                            else:
                                game_dt = prop['game_time']

                            # Convert to local timezone for display
                            local_tz = pytz.timezone('America/New_York')  # Change to your timezone
                            game_dt_local = game_dt.astimezone(local_tz)
                            game_time_str = game_dt_local.strftime('%a %m/%d %I:%M %p %Z')

                            # Add team matchup if available
                            matchup = ""
                            if 'away_team' in prop and 'home_team' in prop and prop['away_team'] and prop['home_team']:
                                matchup = f" - {prop['away_team']} @ {prop['home_team']}"

                            st.caption(f"⏰ Game: {game_time_str}{matchup}")
                        except:
                            pass

                    st.markdown(f"**{prop['prop_type'].replace('_', ' ').title()}** | Line: **{prop['line']}**")

                    # Badges
                    if badges:
                        st.caption(" ".join(badges))

                    # Probabilities
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric(
                            "Over Prob",
                            f"{prop['prob_over']:.1%}",
                        )
                    with col_b:
                        # Determine EV class
                        if prop['ev'] > 1.08:
                            ev_class = "ev-high"
                        elif prop['ev'] > 1.03:
                            ev_class = "ev-medium"
                        else:
                            ev_class = "ev-low"

                        st.markdown(f"""
                        <div class="ev-box {ev_class}">
                            <small>EV</small><br>
                            <b>{prop['ev']:.2f}x</b>
                        </div>
                        """, unsafe_allow_html=True)

                    # CI Range
                    if 'ci_lower' in prop and 'ci_upper' in prop:
                        st.caption(f"95% CI: [{prop['ci_lower']:.2f}, {prop['ci_upper']:.2f}]")

                    # Add to slip button
                    if st.button(f"Add to Slip", key=f"add_{idx}", use_container_width=True):
                        leg = {
                            'player_name': prop['player_name'],
                            'prop_type': prop['prop_type'],
                            'line': prop['line'],
                            'direction': 'over',
                            'probability': prop['prob_over'],
                            'odds': prop.get('over_odds', -110)
                        }
                        if leg not in st.session_state.manual_slip:
                            st.session_state.manual_slip.append(leg)
                            st.success("Added!")
                            st.rerun()

                    st.divider()


def render_correlation_heatmap(props_df, corr_matrix):
    """Render correlation matrix heatmap."""
    if props_df is None or corr_matrix is None or len(corr_matrix) == 0:
        st.info("Generate props first to view correlations")
        return


    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 10))

    # Create labels
    labels = [f"{prop['player_name'][:15]}\n{prop['prop_type'][:10]}"
              for _, prop in props_df.iterrows()]

    # Plot heatmap
    sns.heatmap(
        corr_matrix,
        annot=False,
        cmap="RdYlGn",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax
    )

    ax.set_title("Prop Correlation Matrix", fontsize=14, fontweight='bold')

    # Set labels (show every nth label to avoid crowding)
    step = max(1, len(labels) // 20)
    ax.set_xticks(np.arange(0, len(labels), step) + 0.5)
    ax.set_xticklabels(labels[::step], rotation=45, ha='right', fontsize=8)
    ax.set_yticks(np.arange(0, len(labels), step) + 0.5)
    ax.set_yticklabels(labels[::step], rotation=0, fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # High correlation pairs
    st.markdown("**High Correlation Pairs**")

    # Correlation strength filter
    min_corr = st.slider("Minimum |Correlation|", 0.0, 1.0, 0.5, 0.05)

    high_corr_pairs = []
    n = len(corr_matrix)
    for i in range(n):
        for j in range(i+1, n):
            if abs(corr_matrix[i, j]) >= min_corr:
                high_corr_pairs.append({
                    "Player 1": props_df.iloc[i]['player_name'],
                    "Prop 1": props_df.iloc[i]['prop_type'],
                    "Player 2": props_df.iloc[j]['player_name'],
                    "Prop 2": props_df.iloc[j]['prop_type'],
                    "Correlation": corr_matrix[i, j]
                })

    if high_corr_pairs:
        corr_df = pd.DataFrame(high_corr_pairs)
        corr_df = corr_df.sort_values('Correlation', key=abs, ascending=False)

        st.dataframe(
            corr_df.style.background_gradient(subset=['Correlation'], cmap='RdYlGn', vmin=-1, vmax=1),
            use_container_width=True
        )
    else:
        st.info(f"No correlation pairs found with |ρ| >= {min_corr}")


def render_what_if_sandbox(slip):
    """Render what-if analysis sandbox."""
    st.markdown("**What-If Sandbox**")
    st.caption("Adjust probabilities to see impact on slip metrics")

    # Initialize adjustments for this slip
    slip_id = slip.get('slip_id', 'temp')
    if slip_id not in st.session_state.what_if_adjustments:
        st.session_state.what_if_adjustments[slip_id] = {}

    # Original metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Original Win Prob", f"{slip['correlation_adjusted_prob']:.1%}")
    with col2:
        st.metric("Original EV", f"{slip['expected_value']:.2f}x")
    with col3:
        st.metric("Original Bet", f"${slip['suggested_bet']:.2f}")

    st.divider()

    # Adjustment sliders
    adjusted_probs = []
    for i, leg in enumerate(slip['legs']):
        orig_prob = leg.get('probability', leg.get('prob', 0.5))

        col1, col2 = st.columns([3, 1])
        with col1:
            adj_prob = st.slider(
                f"{leg['player_name']} - {leg['prop_type']}",
                min_value=max(0.0, orig_prob - 0.1),
                max_value=min(1.0, orig_prob + 0.1),
                value=st.session_state.what_if_adjustments[slip_id].get(i, orig_prob),
                step=0.01,
                key=f"whatif_{slip_id}_{i}",
                format="%.2f"
            )
        with col2:
            delta = adj_prob - orig_prob
            st.metric("Δ", f"{delta:+.1%}")

        st.session_state.what_if_adjustments[slip_id][i] = adj_prob
        adjusted_probs.append(adj_prob)

    # Calculate adjusted metrics
    raw_win_prob = np.prod(adjusted_probs)

    # Apply simple correlation adjustment (use original correlation factor)
    corr_factor = slip['correlation_adjusted_prob'] / slip.get('raw_win_prob', slip['correlation_adjusted_prob'])
    adjusted_win_prob = raw_win_prob * corr_factor

    adjusted_ev = adjusted_win_prob * slip['total_odds']

    # Simple Kelly calculation
    kelly_fraction = 0.25  # Conservative Kelly
    adjusted_bet = kelly_fraction * (adjusted_win_prob * slip['total_odds'] - 1) / (slip['total_odds'] - 1)
    adjusted_bet = max(0, adjusted_bet * 100)  # Assuming $100 bankroll for demo

    st.divider()

    # Adjusted metrics
    st.markdown("**Adjusted Metrics**")
    col1, col2, col3 = st.columns(3)
    with col1:
        delta_prob = adjusted_win_prob - slip['correlation_adjusted_prob']
        st.metric("Adjusted Win Prob", f"{adjusted_win_prob:.1%}", f"{delta_prob:+.1%}")
    with col2:
        delta_ev = adjusted_ev - slip['expected_value']
        st.metric("Adjusted EV", f"{adjusted_ev:.2f}x", f"{delta_ev:+.2f}")
    with col3:
        delta_bet = adjusted_bet - slip['suggested_bet']
        st.metric("Adjusted Bet", f"${adjusted_bet:.2f}", f"${delta_bet:+.2f}")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset Adjustments", use_container_width=True):
            st.session_state.what_if_adjustments[slip_id] = {}
            st.rerun()
    with col2:
        if st.button("Apply Adjustments", use_container_width=True):
            st.info("Adjustments applied! (In production, this would update the slip)")


def render_slip_builder(slips, props_df, bankroll):
    """Render slip builder with manual construction."""

    # Manual slip construction
    with st.expander("Manual Slip Construction", expanded=False):
        if st.session_state.manual_slip:
            st.caption(f"Current slip: {len(st.session_state.manual_slip)} legs")

            # Show legs
            for i, leg in enumerate(st.session_state.manual_slip):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.caption(f"{leg['player_name']} - {leg['prop_type']} {leg['direction']} {leg['line']}")
                with col2:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.manual_slip.pop(i)
                        st.rerun()

            # Calculate metrics
            if len(st.session_state.manual_slip) >= 2:
                raw_prob = np.prod([leg['probability'] for leg in st.session_state.manual_slip])
                total_odds = np.prod([1 + abs(leg['odds']) / 100 if leg['odds'] < 0
                                     else 1 + leg['odds'] / 100
                                     for leg in st.session_state.manual_slip])

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Odds", f"{total_odds:.2f}")
                with col2:
                    st.metric("Raw Win Prob", f"{raw_prob:.1%}")
                with col3:
                    st.metric("Expected Value", f"{raw_prob * total_odds:.2f}x")

                if st.button("Clear Slip", use_container_width=True):
                    st.session_state.manual_slip = []
                    st.rerun()
        else:
            st.info("Add props from the Props Grid to build a manual slip")

    st.divider()

    # Display optimized slips
    if not slips:
        st.info("Click 'Generate Optimized Slips' to create optimized parlays")
        return

    st.caption(f"Showing {min(len(slips), 10)} optimized slips")

    # Display top slips
    for i, slip in enumerate(slips[:10]):
        # Risk level - colors handled by CSS variables
        risk_level = slip['risk_level'].title()

        with st.expander(f"Slip {i+1} - {risk_level} | EV: {slip['expected_value']:.2f}x | Prob: {slip['correlation_adjusted_prob']:.1%}"):
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Odds", f"{slip['total_odds']:.2f}")
            with col2:
                st.metric("Win Probability", f"{slip['correlation_adjusted_prob']:.1%}")
            with col3:
                st.metric("Expected Value", f"{slip['expected_value']:.2f}x")
            with col4:
                st.metric("Suggested Bet", f"${slip['suggested_bet']:.2f}")

            # Diversity score
            if 'diversity_score' in slip:
                st.progress(slip['diversity_score'], text=f"Diversity: {slip['diversity_score']:.0%}")

            # Correlation warnings
            if 'correlation_notes' in slip and slip['correlation_notes']:
                st.warning(f"⚠️ {slip['correlation_notes']}")

            # Legs table
            st.markdown("**Legs:**")
            legs_df = pd.DataFrame(slip['legs'])
            display_cols = ['player_name', 'prop_type', 'line', 'direction']
            if 'probability' in legs_df.columns:
                display_cols.append('probability')
            elif 'prob' in legs_df.columns:
                display_cols.append('prob')

            st.dataframe(legs_df[display_cols], use_container_width=True)

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("What-If Analysis", key=f"whatif_{i}", use_container_width=True):
                    st.session_state.selected_slip_for_whatif = i
            with col2:
                if st.button("Create Safer Alt", key=f"safer_{i}", use_container_width=True):
                    # Remove lowest probability leg
                    legs = slip['legs'].copy()
                    if len(legs) > 2:
                        legs.sort(key=lambda x: x.get('probability', x.get('prob', 0)))
                        legs.pop(0)
                        st.info(f"Removed lowest prob leg: {legs[0]['player_name']}")
            with col3:
                if st.button("Copy to Clipboard", key=f"copy_{i}", use_container_width=True):
                    st.info("Slip copied! (Feature coming soon)")

            # What-If sandbox
            if st.session_state.get('selected_slip_for_whatif') == i:
                with st.container():
                    render_what_if_sandbox(slip)


def render_top_sets(slips):
    """Render top recommended sets."""
    if not slips:
        return

    st.markdown("**Top Recommended Sets**")
    st.caption("Quick view of the best opportunities")

    # Show top 5 slips in condensed format
    for i, slip in enumerate(slips[:5]):
        # Risk level text only (no icons)
        risk_level = slip['risk_level'].title()

        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        with col1:
            players = ", ".join([leg['player_name'][:15] for leg in slip['legs'][:3]])
            if len(slip['legs']) > 3:
                players += f" +{len(slip['legs']) - 3} more"
            st.write(f"**{i+1}. {risk_level}:** {players}")
        with col2:
            st.write(f"EV: {slip['expected_value']:.2f}x")
        with col3:
            st.write(f"Prob: {slip['correlation_adjusted_prob']:.1%}")
        with col4:
            st.write(f"Odds: {slip['total_odds']:.1f}")
        with col5:
            st.write(f"${slip['suggested_bet']:.2f}")


def render_backtest_tab(settings):
    """Render backtest analysis tab."""
    st.caption("Simulate strategy performance across historical data")

    # Backtest configuration
    col1, col2, col3 = st.columns(3)
    with col1:
        start_week = st.selectbox("Start Week", options=list(range(1, 19)), index=0)
    with col2:
        end_week = st.selectbox("End Week", options=list(range(1, 19)), index=9)
    with col3:
        BACKTEST_BANKROLL_PRESETS = {
            "$50": 50,
            "$100": 100,
            "$250": 250,
            "$500": 500,
            "$1000": 1000,
            "$2500": 2500,
            "$5000": 5000
        }
        initial_bankroll_selection = st.selectbox(
            "Initial Bankroll",
            options=list(BACKTEST_BANKROLL_PRESETS.keys()),
            index=3  # Default to $500
        )
        initial_bankroll = BACKTEST_BANKROLL_PRESETS[initial_bankroll_selection]

    if st.button("Run Backtest", type="primary", use_container_width=True):
        with st.spinner("Running backtest simulation..."):
            try:
                results = evaluate_backtest(
                    start_week=start_week,
                    end_week=end_week,
                    season=2024,
                    initial_bankroll=initial_bankroll
                )
                st.session_state.backtest_results = results

                # Record experiment
                record_experiment({
                    'event_type': EVENT_TYPES['BACKTEST_RUN'],
                    'week': start_week,
                    'season': 2024,
                    'metrics': {
                        'total_return': results['total_return'],
                        'win_rate': results['win_rate'],
                        'sharpe_ratio': results['sharpe_ratio']
                    }
                })

                st.success("Backtest complete!")
            except Exception as e:
                st.error(f"Error running backtest: {str(e)}")

    # Display results
    if st.session_state.backtest_results:
        results = st.session_state.backtest_results

        st.divider()

        # Performance metrics
        st.markdown("**Performance Metrics**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            delta = results['total_return']
            st.metric("Total Return", f"{delta:.1f}%", delta=f"{delta:.1f}%")
        with col2:
            st.metric("Win Rate", f"{results['win_rate']:.1%}")
        with col3:
            st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
        with col4:
            st.metric("Max Drawdown", f"{results['max_drawdown']:.1f}%")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Slips", f"{results['total_slips']}")
        with col2:
            st.metric("Winning Slips", f"{results['winning_slips']}")
        with col3:
            st.metric("Final Bankroll", f"${results['final_bankroll']:.2f}")

        st.divider()

        # Bankroll progression
        st.markdown("**Bankroll Progression**")
        bankroll_df = results['bankroll_history']
        st.line_chart(bankroll_df.set_index('week')['bankroll'])

        # Calibration metrics
        st.markdown("**Calibration Metrics**")
        col1, col2, col3 = st.columns(3)
        with col1:
            ece = results['calibration_metrics']['ece']
            st.metric("ECE", f"{ece:.3f}", help="Expected Calibration Error (lower is better)")
        with col2:
            brier = results['calibration_metrics']['brier_score']
            st.metric("Brier Score", f"{brier:.3f}", help="Brier score (lower is better)")
        with col3:
            log_loss = results['calibration_metrics']['log_loss']
            st.metric("Log Loss", f"{log_loss:.3f}", help="Logarithmic loss (lower is better)")

        # Win rate by leg count
        if 'win_rate_by_legs' in results:
            st.markdown("**Win Rate by Leg Count**")
            leg_data = results['win_rate_by_legs']
            st.bar_chart(pd.DataFrame(leg_data.items(), columns=['Legs', 'Win Rate']).set_index('Legs'))

        # Best and worst slips
        col1, col2 = st.columns(2)
        with col1:
            if 'best_slips' in results:
                with st.expander("🏆 Best Slips"):
                    for slip in results['best_slips'][:5]:
                        st.caption(f"ROI: {slip.get('roi', 0):.1%} | Odds: {slip.get('total_odds', 0):.1f}")

        with col2:
            if 'worst_slips' in results:
                with st.expander("❌ Worst Slips"):
                    for slip in results['worst_slips'][:5]:
                        st.caption(f"ROI: {slip.get('roi', 0):.1%} | Odds: {slip.get('total_odds', 0):.1f}")

        # Export button
        if st.button("Export Backtest Results", use_container_width=True):
            try:
                export_path = f"./exports/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_backtest_results_csv(results, export_path)
                st.success(f"Exported to {export_path}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_top_controls():
    """Render top navigation bar with essential controls."""

    # Data Fetch Controls
    with st.expander("Data Fetch Controls", expanded=False):
        # Row 0: Sport Selection
        sport = st.selectbox(
            "Sport",
            options=["NFL", "NBA", "MLB"],
            index=0,
            key="sport_selector",
            help="Select sport to analyze"
        )

        # Row 1: Data Source, Test API, Snapshot, Export
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            data_source = st.selectbox(
                "Data Source",
                options=["Odds API (Real Props)", "Mock Data (Testing)"],
                index=0,
                key="top_data_source"
            )

        with col2:
            # Test API dropdown-style selector
            TEST_ODDS_API = "Test Odds API"
            TEST_WEATHER_API = "Test Weather API"

            test_api_options = [TEST_ODDS_API, TEST_WEATHER_API]

            # Initialize session state to prevent immediate trigger on first render
            if 'test_api_initialized' not in st.session_state:
                st.session_state.last_test_action = TEST_ODDS_API
                st.session_state.test_api_initialized = True

            selected_test = st.selectbox(
                "Test API",
                options=test_api_options,
                key="test_api_selector"
            )

            # Handle test action when selection changes
            if selected_test == TEST_ODDS_API and selected_test != st.session_state.get('last_test_action'):
                with st.spinner("Testing Odds API..."):
                    result = keys_test("odds_api")
                    if result['valid']:
                        st.success("✓ Odds API Connected")
                        if 'details' in result and 'games_count' in result['details']:
                            st.caption(f"Found {result['details']['games_count']} games")
                    else:
                        st.error("✗ " + result['message'])
                    st.session_state.last_test_action = selected_test
            elif selected_test == TEST_WEATHER_API and selected_test != st.session_state.get('last_test_action'):
                with st.spinner("Testing Weather API..."):
                    result = keys_test("openweather")
                    if result['valid']:
                        st.success("✓ Weather API Connected")
                    else:
                        st.error("✗ " + result['message'])
                    st.session_state.last_test_action = selected_test

        with col3:
            # Snapshot selector with Lock as first option
            snapshots = list_snapshots()

            # Build options: Lock first, then all snapshots
            LOCK_OPTION = "Lock Current Analysis"
            snapshot_options = [LOCK_OPTION]
            if snapshots:
                snapshot_options.extend([s['snapshot_id'] for s in snapshots])

            # Get current snapshot index
            current_index = 0
            current_snapshot_id = st.session_state.get('snapshot_id')
            if current_snapshot_id and current_snapshot_id in snapshot_options:
                current_index = snapshot_options.index(current_snapshot_id)

            # Initialize session state to prevent immediate lock on first render
            if 'snapshot_initialized' not in st.session_state:
                st.session_state.last_snapshot_action = LOCK_OPTION
                st.session_state.snapshot_initialized = True

            selected_snapshot = st.selectbox(
                "Snapshot",
                options=snapshot_options,
                index=current_index,
                key="top_snapshot_selector"
            )

            # Handle selection
            if selected_snapshot == LOCK_OPTION:
                # User selected Lock option - trigger lock if props exist
                if st.session_state.props_df is not None and selected_snapshot != st.session_state.get('last_snapshot_action'):
                    try:
                        # Get week and season from session state or use defaults
                        week = st.session_state.get('current_week', 1)
                        season = st.session_state.get('current_season', 2025)

                        snapshot_id = lock_snapshot(
                            props_df=st.session_state.props_df,
                            slips=st.session_state.slips,
                            config=st.session_state.config.model_dump() if hasattr(st.session_state.config, 'model_dump') else {},
                            week=week,
                            season=season
                        )
                        st.session_state.snapshot_id = snapshot_id
                        st.session_state.last_snapshot_action = LOCK_OPTION

                        # Record experiment
                        record_experiment({
                            'event_type': EVENT_TYPES['SNAPSHOT_CREATED'],
                            'snapshot_id': snapshot_id,
                            'week': week,
                            'season': season,
                            'num_props': len(st.session_state.props_df),
                            'num_slips': len(st.session_state.slips)
                        })

                        st.success(f"✓ Locked: {snapshot_id[:8]}...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                # User selected an existing snapshot - load it
                if selected_snapshot != st.session_state.get('last_loaded_snapshot'):
                    try:
                        snapshot_data = load_snapshot(selected_snapshot)
                        st.session_state.props_df = snapshot_data['props_df']
                        st.session_state.slips = snapshot_data['slips']
                        st.session_state.snapshot_id = selected_snapshot
                        st.session_state.last_loaded_snapshot = selected_snapshot
                        st.session_state.last_snapshot_action = selected_snapshot
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading: {str(e)}")

        with col4:
            # Combined Export selector
            EXPORT_PROPS = "Export Props CSV"
            EXPORT_SLIPS = "Export Slips CSV"

            export_options = [EXPORT_PROPS, EXPORT_SLIPS]

            # Initialize session state to prevent immediate export on first render
            if 'export_initialized' not in st.session_state:
                st.session_state.last_export_action = EXPORT_PROPS
                st.session_state.export_initialized = True

            selected_export = st.selectbox(
                "Exports",
                options=export_options,
                key="export_selector"
            )

            # Handle export action when selection changes
            if selected_export == EXPORT_PROPS and selected_export != st.session_state.get('last_export_action'):
                if st.session_state.props_df is not None:
                    try:
                        export_path = f"./exports/props_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        export_props_csv(st.session_state.props_df, export_path)
                        st.toast("✓ Props exported", icon="✅")
                        st.session_state.last_export_action = selected_export

                        # Record experiment
                        record_experiment({
                            'event_type': EVENT_TYPES['EXPORT'],
                            'notes': f'Exported props to {export_path}'
                        })
                    except Exception as e:
                        st.toast(f"Error: {str(e)}", icon="❌")
                else:
                    st.toast("No props to export", icon="⚠️")

            elif selected_export == EXPORT_SLIPS and selected_export != st.session_state.get('last_export_action'):
                if st.session_state.slips:
                    try:
                        export_path = f"./exports/slips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        export_slips_csv(st.session_state.slips, export_path)
                        st.toast("✓ Slips exported", icon="✅")
                        st.session_state.last_export_action = selected_export

                        # Record experiment
                        record_experiment({
                            'event_type': EVENT_TYPES['EXPORT'],
                            'notes': f'Exported slips to {export_path}'
                        })
                    except Exception as e:
                        st.toast(f"Error: {str(e)}", icon="❌")
                else:
                    st.toast("No slips to export", icon="⚠️")

        # Row 2: Week, Season, and conditional Odds API settings
        if data_source == "Odds API (Real Props)":
            # Display note for NBA/MLB that Week/Season are not used
            if sport in ["NBA", "MLB"]:
                st.info(f"📅 {sport}: Fetching upcoming games (Week/Season fields below are not used)")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                week_label = "Week" if sport == "NFL" else "Week (unused)"
                week = st.number_input(week_label, min_value=1, max_value=18, value=1, key="top_week", disabled=(sport != "NFL"))
                st.session_state.current_week = week  # Store for snapshot
            with col2:
                season = st.number_input("Season", min_value=2020, max_value=2025, value=2025, key="top_season")
                st.session_state.current_season = season  # Store for snapshot
            with col3:
                max_games = st.number_input(
                    "Max Games",
                    min_value=1,
                    max_value=16,
                    value=5,
                    help="Limit games to conserve API quota",
                    key="top_max_games"
                )
            with col4:
                game_time_filter = st.selectbox(
                    "Game Time Filter",
                    options=["Upcoming Only", "Include Started Games", "All Games"],
                    index=0,
                    help="Filter games by start time to save API credits",
                    key="top_time_filter"
                )
        else:
            # Mock data mode - just Week and Season
            col1, col2 = st.columns([1, 1])
            with col1:
                week = st.number_input("Week", min_value=1, max_value=18, value=1, key="top_week")
                st.session_state.current_week = week  # Store for snapshot
            with col2:
                season = st.number_input("Season", min_value=2020, max_value=2025, value=2025, key="top_season")
                st.session_state.current_season = season  # Store for snapshot
            max_games = None
            game_time_filter = "All Games"

        # Row 2: Fetch Props button with custom green color
        if st.button("Fetch Props from API", type="primary", use_container_width=True, key="fetch_props_top"):
            with st.spinner("🔄 Fetching props from API..."):
                try:
                    # Get week and season from session state
                    week = st.session_state.get('current_week', 1)
                    season = st.session_state.get('current_season', 2025)

                    # Fetch props based on selected data source
                    if data_source == "Odds API (Real Props)":
                        # Fetch from Odds API
                        props_df = fetch_current_props_from_odds_api(
                            week=week,
                            season=season,
                            max_games=max_games,
                            game_time_filter=game_time_filter,
                            sport=sport
                        )
                    else:
                        # Fetch mock data
                        props_df = fetch_current_props(week=week, season=season, sport=sport)

                    if props_df is not None and len(props_df) > 0:
                        # Build features
                        props_df = build_features(props_df)

                        # Estimate probabilities
                        props_df = estimate_probabilities(props_df)

                        # Store in session state
                        st.session_state.props_df = props_df

                        # Record experiment
                        record_experiment({
                            'event_type': EVENT_TYPES['PROPS_FETCHED'],
                            'week': week,
                            'season': season,
                            'data_source': data_source,
                            'num_props': len(props_df)
                        })

                        st.success(f"✓ Fetched {len(props_df)} props for Week {week}, {season}!")
                        st.rerun()
                    else:
                        st.warning("No props available for this week/season")

                except Exception as e:
                    st.error(f"Error fetching props: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    # Slip Generation - How to build parlays
    with st.expander("Slip Generation", expanded=False):
        # Row 1: Strategy Settings
        col1, col2, col3 = st.columns(3)

        with col1:
            risk_mode_display = st.selectbox(
                "Risk Profile",
                options=["Conservative", "Balanced", "Aggressive"],
                index=1,  # Default to Balanced
                help="Controls Kelly fraction, min probability, max legs, and min edge",
                key="slip_risk"
            )
            risk_mode = risk_mode_display.lower()

        with col2:
            BANKROLL_PRESETS_MAIN = {
                "$50": 50.0,
                "$100": 100.0,
                "$250": 250.0,
                "$500": 500.0,
                "$1000": 1000.0,
                "$2500": 2500.0,
                "$5000": 5000.0,
                "Custom": None
            }

            bankroll_selection_main = st.selectbox(
                "Bankroll ($)",
                options=list(BANKROLL_PRESETS_MAIN.keys()),
                index=3,  # Default to $500
                help="Your total bankroll for bet sizing",
                key="slip_bankroll_select"
            )

            if BANKROLL_PRESETS_MAIN[bankroll_selection_main] is None:
                bankroll = st.number_input(
                    "Custom Amount ($)",
                    min_value=10.0,
                    max_value=100000.0,
                    value=st.session_state.config.ui.bankroll.default_amount,
                    step=10.0,
                    key="slip_bankroll_custom"
                )
            else:
                bankroll = BANKROLL_PRESETS_MAIN[bankroll_selection_main]

        with col3:
            n_slips = st.selectbox(
                "Number of Slips",
                options=[5, 10, 20, 30, 50],
                index=2,  # Default to 20
                help="How many optimized parlays to generate",
                key="slip_n_slips"
            )

        # Row 2: Parlay Constraints (Range Sliders)
        col1, col2 = st.columns(2)

        with col1:
            legs_range = st.slider(
                "Legs Range",
                min_value=2,
                max_value=10,
                value=(2, 5),
                help="Minimum and maximum number of props per parlay",
                key="slip_legs_range"
            )
            min_legs = legs_range[0]
            max_legs = legs_range[1]

        with col2:
            odds_range = st.slider(
                "Total Odds Range",
                min_value=0.0,
                max_value=100.0,
                value=(2.0, 50.0),
                step=0.5,
                help="Minimum and maximum total parlay odds (all legs multiplied)",
                key="slip_odds_range"
            )
            min_odds = odds_range[0]
            max_odds = odds_range[1]

        # Row 3: Filter sliders
        col1, col2, col3 = st.columns(3)

        with col1:
            max_ci_width = st.slider(
                "CI Width Filter",
                min_value=0.0,
                max_value=0.5,
                value=0.0,
                step=0.05,
                key="filter_ci_width",
                help="Max confidence interval width. 0 = disabled. Lower values = only high-confidence props. Recommended: 0.25 for real data."
            )
            enable_ci_filter = max_ci_width > 0

        with col2:
            min_edge = st.slider(
                "Minimum Edge (%)",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                key="filter_edge",
                help="Minimum EV edge required. 0 = disabled. Higher = more selective. Example: 3% = only props with 1.03x EV or higher."
            )

        with col3:
            diversity_target = st.slider(
                "Diversity Target",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Higher = more diverse slips with lower correlation. 0 = no diversity preference.",
                key="slip_diversity"
            )

        # Generate Optimized Slips button
        if st.session_state.props_df is not None:
            if st.button("Generate Optimized Slips", type="primary", use_container_width=True, key="generate_slips_top"):
                with st.spinner("🔄 Generating optimized slips..."):
                    try:
                        # Start with stored props
                        props_df = st.session_state.props_df.copy()

                        # Apply CI filter if enabled
                        if enable_ci_filter and 'ci_lower' in props_df.columns and 'ci_upper' in props_df.columns:
                            props_df = filter_by_ci_width(props_df, max_ci_width)

                        # Apply edge filter if enabled
                        if min_edge > 0:
                            # Calculate EV if not already present
                            if 'ev' not in props_df.columns and 'over_odds' in props_df.columns and 'prob_over' in props_df.columns:
                                props_df['ev'] = props_df.apply(
                                    lambda row: row['prob_over'] * (1 + abs(row['over_odds']) / 100) if row.get('over_odds', 0) < 0
                                    else row['prob_over'] * (1 + row.get('over_odds', 0) / 100),
                                    axis=1
                                )
                            if 'ev' in props_df.columns:
                                props_df = props_df[props_df['ev'] > 1 + min_edge / 100]

                        # Estimate correlations
                        corr_matrix = estimate_correlations(props_df)

                        # Optimize slips
                        slips = optimize_slips(
                            props_df,
                            corr_matrix,
                            bankroll=bankroll,
                            diversity_target=diversity_target,
                            n_slips=n_slips,
                            risk_mode=risk_mode,
                            min_legs=min_legs,
                            max_legs=max_legs,
                            min_odds=min_odds,
                            max_odds=max_odds
                        )

                        # Store in session state
                        st.session_state.slips = slips
                        st.session_state.corr_matrix = corr_matrix

                        # Record experiment
                        record_experiment({
                            'event_type': EVENT_TYPES['SLIP_GENERATED'],
                            'week': week,
                            'season': season,
                            'risk_mode': risk_mode,
                            'bankroll': bankroll,
                            'num_props': len(props_df),
                            'num_slips': len(slips)
                        })

                        st.success(f"✓ Slips generated! Created {len(slips)} optimized parlays from {len(props_df)} props.")

                    except Exception as e:
                        st.error(f"Error generating slips: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

    return {
        "week": week,
        "season": season,
        "data_source": data_source,
        "max_games": max_games,
        "game_time_filter": game_time_filter,
        "bankroll": bankroll,
        "risk_mode": risk_mode,
        "min_legs": min_legs,
        "max_legs": max_legs,
        "min_odds": min_odds,
        "max_odds": max_odds,
        "diversity_target": diversity_target,
        "enable_ci_filter": enable_ci_filter,
        "max_ci_width": max_ci_width,
        "min_edge": min_edge
    }


def main():
    """Main application."""
    initialize_session_state()

    # Apply clean light theme CSS
    apply_theme_css()

    # Main content area
    st.title("BetterBros Props")
    st.caption("Advanced probability analysis and slip optimization for player props")

    # Quick Actions Menu - wrapper div with custom class for CSS targeting
    st.markdown('<div class="quick-actions-wrapper">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Snapshot", use_container_width=True,
                    type="primary",
                    help="Save current analysis",
                    key="quick_snapshot"):
            if st.session_state.props_df is not None:
                try:
                    week = st.session_state.get('current_week', 1)
                    season = st.session_state.get('current_season', 2025)
                    snapshot_id = lock_snapshot(
                        props_df=st.session_state.props_df,
                        slips=st.session_state.slips,
                        config=st.session_state.config.model_dump() if hasattr(st.session_state.config, 'model_dump') else {},
                        week=week,
                        season=season
                    )
                    st.session_state.snapshot_id = snapshot_id
                    st.toast(f"Snapshot saved: {snapshot_id[:8]}...")
                except Exception as e:
                    st.toast(f"Error: {str(e)}")
            else:
                st.toast("No data to snapshot")

    with col2:
        if st.button("Export", use_container_width=True,
                    type="primary",
                    help="Export data",
                    key="quick_export"):
            if st.session_state.props_df is not None:
                try:
                    export_path = f"./exports/props_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    export_props_csv(st.session_state.props_df, export_path)
                    st.toast("Props exported")
                except Exception as e:
                    st.toast(f"Error: {str(e)}")
            else:
                st.toast("No props to export")

    with col3:
        if st.button("Shortcuts", use_container_width=True,
                    type="primary",
                    help="View keyboard shortcuts",
                    key="quick_shortcuts"):
            st.session_state.show_shortcuts_modal = not st.session_state.show_shortcuts_modal

    with col4:
        if st.button("Start Guide", use_container_width=True,
                    type="primary",
                    help="View getting started guide",
                    key="quick_guide"):
            st.session_state.show_guide_modal = not st.session_state.show_guide_modal

    st.markdown('</div>', unsafe_allow_html=True)

    # Keyboard Shortcuts Section
    if st.session_state.show_shortcuts_modal:
        with st.expander("Keyboard Shortcuts", expanded=True):
            st.markdown("""
            | Shortcut | Action |
            |----------|--------|
            | Cmd/Ctrl + K | Focus search |
            | Cmd/Ctrl + G | Generate slips |
            | Cmd/Ctrl + F | Fetch props |
            | Cmd/Ctrl + E | Export data |
            | Cmd/Ctrl + S | Save snapshot |
            | ? | Show this help |
            """)
            if st.button("Close", use_container_width=True, key="close_shortcuts"):
                st.session_state.show_shortcuts_modal = False
                st.rerun()

    # Quick Start Guide Section
    if st.session_state.show_guide_modal:
        with st.expander("Quick Start Guide", expanded=True):
            st.markdown("""
            **How to Use NFL Props Analyzer**

            1. Configure Settings: Use the Data Fetch and Slip Generation sections to set your week, bankroll, and risk profile
            2. Generate Analysis: Click the main button to fetch props and generate optimized slips
            3. Explore Props: Review individual prop cards with probabilities and EV
            4. Build Slips: Use optimized slips or build your own manually
            5. Analyze Correlations: View the correlation heatmap to understand prop relationships
            6. Run Backtests: Test your strategy across historical data
            7. Export & Share: Save your analysis as CSV or create shareable packages

            **Key Parameters Explained**

            **Bankroll**
            - What it affects: Only the Suggested Bet amount (via Kelly Criterion)
            - What it does NOT affect: Slip generation, min/max odds, which props are selected
            - How it works: Larger bankroll = larger suggested bets (clamped to $5-$50)
            - Recommendation: Set to your actual betting bankroll for accurate sizing

            **Risk Profile (Conservative / Balanced / Aggressive)**

            Controls multiple underlying parameters:
            - Conservative: Max 4 legs, min 65% prob per leg, min 8% edge, 25% Kelly
            - Balanced: Max 6 legs, min 55% prob per leg, min 5% edge, 50% Kelly
            - Aggressive: Max 8 legs, min 45% prob per leg, min 3% edge, 75% Kelly

            **Slip Constraints**

            - Min/Max Legs: Number of props per parlay
              - Fewer legs = safer, lower payout
              - More legs = riskier, higher payout

            - Min Total Odds: Minimum parlay payout multiplier
              - Set to 0 to allow any combination
              - 1.5-2.0 = Standard safe range

            - Diversity Target (0.0 - 1.0)
              - Controls prop variety across slips
              - Higher = more diverse, less correlated props
              - 0 = Allows highly correlated prop combinations
            """)
            if st.button("Close", use_container_width=True, key="close_guide"):
                st.session_state.show_guide_modal = False
                st.rerun()

    # Render top controls (replaces sidebar)
    settings = render_top_controls()

    # Calibration banner
    render_calibration_banner()

    # If we have data, show it in an analysis results container
    if st.session_state.props_df is not None:
        with st.expander("Analysis Results", expanded=True):
            # Tabs for different views
            tab0, tab1, tab2, tab3, tab4 = st.tabs([
                "Trend Chips",
                "Props Grid",
                "Slips & Builder",
                "Correlations",
                "Backtest"
            ])

            with tab0:
                # Generate and display trends
                try:
                    trends = generate_trend_chips(st.session_state.props_df)
                    render_trend_chips(trends)
                except Exception as e:
                    st.warning(f"Could not generate trend chips: {str(e)}")

            with tab1:

                # Search & Filter Bar
                col1, col2 = st.columns([3, 1])
                with col1:
                    search = st.text_input(
                        "Search players, teams, props...",
                        value=st.session_state.search_query,
                        key="global_search",
                        placeholder="e.g., Patrick Mahomes, passing yards, Chiefs"
                    )
                    st.session_state.search_query = search

                with col2:
                    if st.button("Clear Search", use_container_width=True, key="clear_search"):
                        st.session_state.search_query = ""
                        st.rerun()

                # Apply search filter to props_df
                filtered_df = st.session_state.props_df.copy()

                # Search filter
                if st.session_state.search_query:
                    search_lower = st.session_state.search_query.lower()
                    mask = (
                        filtered_df['player_name'].str.lower().str.contains(search_lower, case=False, na=False) |
                        filtered_df['prop_type'].str.lower().str.contains(search_lower, case=False, na=False)
                    )
                    if 'team' in filtered_df.columns:
                        mask = mask | filtered_df['team'].str.lower().str.contains(search_lower, case=False, na=False)
                    if 'home_team' in filtered_df.columns:
                        mask = mask | filtered_df['home_team'].str.lower().str.contains(search_lower, case=False, na=False)
                    if 'away_team' in filtered_df.columns:
                        mask = mask | filtered_df['away_team'].str.lower().str.contains(search_lower, case=False, na=False)
                    filtered_df = filtered_df[mask]

                # Show count
                st.caption(f"Showing {len(filtered_df)} of {len(st.session_state.props_df)} props")

                # Render filtered props
                render_prop_cards(filtered_df)

            with tab2:
                render_top_sets(st.session_state.slips)
                st.divider()
                render_slip_builder(
                    st.session_state.slips,
                    st.session_state.props_df,
                    settings['bankroll']
                )

            with tab3:
                render_correlation_heatmap(
                    st.session_state.props_df,
                    st.session_state.corr_matrix
                )

            with tab4:
                render_backtest_tab(settings)
    else:
        # Show quick start guide
        with st.expander("Quick Start Guide"):
            st.markdown("""
            **How to Use NFL Props Analyzer**

            1. Configure Settings: Use the Data Fetch and Slip Generation sections to set your week, bankroll, and risk profile
            2. Generate Analysis: Click the main button to fetch props and generate optimized slips
            3. Explore Props: Review individual prop cards with probabilities and EV
            4. Build Slips: Use optimized slips or build your own manually
            5. Analyze Correlations: View the correlation heatmap to understand prop relationships
            6. Run Backtests: Test your strategy across historical data
            7. Export & Share: Save your analysis as CSV or create shareable packages

            **Key Parameters Explained**

            **Bankroll**
            - What it affects: Only the Suggested Bet amount (via Kelly Criterion)
            - What it does NOT affect: Slip generation, min/max odds, which props are selected
            - How it works: Larger bankroll = larger suggested bets (clamped to $5-$50)
            - Recommendation: Set to your actual betting bankroll for accurate sizing

            **Risk Profile (Conservative / Balanced / Aggressive)**

            Controls multiple underlying parameters:
            - Conservative: Max 4 legs, min 65% prob per leg, min 8% edge, 25% Kelly
            - Balanced: Max 6 legs, min 55% prob per leg, min 5% edge, 50% Kelly
            - Aggressive: Max 8 legs, min 45% prob per leg, min 3% edge, 75% Kelly

            **Slip Constraints**

            - Min/Max Legs: Number of props per parlay
              - Fewer legs = safer, lower payout
              - More legs = riskier, higher payout

            - Min Total Odds: Minimum parlay payout multiplier
              - Set to 0 to allow any combination (including heavy favorites)
              - < 1.0 = Negative EV even on wins (not recommended)
              - 1.5-2.0 = Standard safe range
              - Higher values = Filter to only longer-odds parlays

            - Max Total Odds: Maximum parlay payout
              - Prevents extremely long-shot parlays
              - 20-50 = Reasonable range for 3-6 leg parlays

            - Diversity Target (0.0 - 1.0)
              - 0.0 = No preference (may stack same game/team)
              - 0.5 = Balanced (default)
              - 1.0 = Maximum diversity (different teams/games/positions)
              - Higher = Reduces correlation risk but may reduce EV

            **Advanced Filters**

            - CI Width Filter: Removes props with uncertain probabilities
              - Enable for real data to filter unstable estimates
              - Disable for mock data (mock has no CI data)

            - Minimum Edge Filter: Only include props with specified edge
              - 3-5% = Conservative (higher quality picks)
              - 0% = Include all positive EV props

            #### **Data Source**
            - **Odds API**: Real props from DraftKings/FanDuel/BetMGM (uses API credits)
            - **Mock Data**: Synthetic props for testing (free, no API usage)

            ---

            ### 💡 Common Scenarios

            **"I want safe 3-leg parlays"**
            - Risk Profile: Conservative
            - Min Legs: 3, Max Legs: 3
            - Min Total Odds: 1.5
            - Diversity Target: 0.7

            **"I want high-upside 5-6 leg parlays"**
            - Risk Profile: Aggressive
            - Min Legs: 5, Max Legs: 6
            - Min Total Odds: 5.0
            - Diversity Target: 0.5

            **"I want heavy favorite 3-leg parlays"**
            - Risk Profile: Balanced
            - Min Legs: 3, Max Legs: 3
            - Min Total Odds: 1.0 (or even 0.0)
            - Min Edge: 0%

            **"I'm getting 0 slips generated"**
            - Lower Min Total Odds (try 1.0 or 1.5)
            - Increase Max Legs
            - Reduce Min Edge filter
            - Check your props have decent odds/probabilities

            ---

            ### Features
            - **Trend Chips**: Automatic detection of market trends
            - **What-If Analysis**: Adjust probabilities to see impact on EV
            - **Calibration Monitoring**: Track model accuracy over time
            - **Correlation Analysis**: Identify and avoid correlated props
            - **Kelly Sizing**: Automatic bet sizing based on edge and bankroll
            """)

        # Show stats if we have experiment history
        try:
            recent = query_experiments(limit=5)
            if not recent.empty:
                with st.expander("Recent Activity", expanded=False):
                    st.dataframe(
                        recent[['timestamp', 'event_type', 'week', 'season']].head(),
                        use_container_width=True,
                        hide_index=True
                    )
        except:
            pass


if __name__ == "__main__":
    main()
