from typing import Tuple, List

from steam_analysis.proccessors.schemas.games import AbstractGameBy_
import matplotlib.pyplot as plt
import numpy as np

import matplotlib.cm as cm



def generate_colormap_colors(num_colors, colormap_name='tab20'):
    cmap = cm.get_cmap(colormap_name)
    colors = [cmap(i / max(num_colors - 1, 1)) for i in range(num_colors)]

    hex_colors = []
    for r, g, b, _ in colors:
        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)

        hex_color = f"#{r_int:02x}{g_int:02x}{b_int:02x}"
        hex_colors.append(hex_color)

    return hex_colors


def data_prep(data: AbstractGameBy_) -> Tuple[List[str], List[str]]:
    ticks = data.ticks
    values_data = data.values

    if isinstance(values_data, dict):
        values = []
        for tick in ticks:
            if tick in values_data:
                values.append(int(values_data[tick]))
            else:
                values.append(0)
        print(f"Преобразованные values из dict: {values}")
    elif isinstance(values_data, list):
        values = [int(v) for v in values_data]
    else:
        raise TypeError(f"Неподдерживаемый тип values: {type(values_data)}")

    if not ticks:
        raise ValueError("Список ticks пустой")
    if not values:
        raise ValueError("Список values пустой")

    print(f"---> ticks: {ticks}")
    print(f"---> values: {values}")

    return ticks, values


def create_data_columns(data: AbstractGameBy_, columns_num: int) -> Tuple[List[str], List[str]]:
    ticks, values = data_prep(data)
    if len(ticks) > columns_num:
        combined = list(zip(ticks, values))
        combined.sort(key=lambda x: x[1], reverse=True)
        top_ticks = [t[0] for t in combined[:columns_num-1]]
        top_values = [t[1] for t in combined[:columns_num-1]]
        others_sum = sum(t[1] for t in combined[columns_num-1:])
        ticks = top_ticks + ["Others"]
        values = top_values + [others_sum]
    else:
        return ticks, values
    return ticks, values


def generate_distribution_by_feature(data: AbstractGameBy_, title_name: str,
                                     path_to_save: str, columns_num: int) -> None:

    ticks, values = create_data_columns(data, columns_num)
    x_positions = np.arange(len(ticks))

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(x_positions, values, color='skyblue', edgecolor='black', alpha=0.7)

    for i in range(min(3, len(bars))):
        bars[i].set_color('crimson')
        bars[i].set_edgecolor('black')

    ax.set_title(title_name, fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(ticks, rotation=45, ha='right', fontsize=10)

    max_value = max(values)
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + max_value * 0.01,
            f'{value:,}',
            ha='center',
            va='bottom',
            fontsize=9
        )

    plt.tight_layout()

    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)



def generate_pie_by_feature(data: AbstractGameBy_, title_name: str,
                            path_to_save: str, sections_num: int, max_to_color: int) -> None:
    ticks, values = create_data_columns(data, sections_num)

    fig, ax = plt.subplots(figsize=(10, 8))

    sorted_data = sorted(zip(values, ticks), reverse=True)

    top_value = [v for v, _ in sorted_data[:max_to_color]]
    top_label = [l for _, l in sorted_data[:max_to_color]]

    print(top_value)
    print(top_label)

    colors = []
    # colors_ = generate_colormap_colors(max_to_color, 'Blues')
    colors_ = generate_colormap_colors(max_to_color, 'Dark2')


    for i, (val, label) in enumerate(zip(values, ticks)):
        if label in top_label:
            idx = top_label.index(label)
            colors.append(colors_[idx])
        else:
            colors.append('none')

    print(colors)

    wedges, texts, autotexts = ax.pie(
        values,
        labels=ticks,
        colors=colors,
        autopct=lambda pct: f'{pct:.1f}%',
        pctdistance=0.75,
        labeldistance=1.1,
        startangle=90,
        wedgeprops={
            'edgecolor': 'black',
            'linewidth': 1.5,
            'linestyle': '-',
            'alpha': 0.8
        }
    )

    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontweight('bold')

    ax.set_title(title_name, fontsize=14, fontweight='bold')
    ax.axis('equal')

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

