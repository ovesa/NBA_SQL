# Centralized plotting style for analysis scripts.
# Import and call set_plot_style() before generating figures.

import matplotlib.pyplot as plt


def set_plot_style():

    plt.style.use("default")

    plt.rcParams.update(
        {
            # Figure settings
            "figure.figsize": (8, 5),
            "figure.dpi": 120,
            "figure.facecolor": "white",
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            # Font sizes
            "axes.titlesize": 17,
            "axes.labelsize": 16,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "legend.fontsize": 16,
            "legend.title_fontsize": 16,
            # Line settings
            "lines.linewidth": 2,
            "lines.markersize": 3,
            # Tick settings
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            "xtick.major.size": 6,
            "ytick.major.size": 6,
            "xtick.minor.size": 3,
            "ytick.minor.size": 3,
            "axes.spines.top": True,
            "axes.spines.right": True,
            # Axes appearance
            "axes.linewidth": 1.0,
            "axes.grid": False,
            # Legend
            "legend.frameon": True,
            "legend.framealpha": 1.0,
            "legend.fancybox": True,
            "legend.shadow": True,
            "legend.facecolor": "white",
            "legend.edgecolor": "#cccccc",
            "legend.loc": "best",
            "legend.markerscale": 1.0,
            # Histogram styling
            "patch.edgecolor": "black",
            "patch.linewidth": 0.8,
            # Fonts
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans"],
            # Grid
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )
