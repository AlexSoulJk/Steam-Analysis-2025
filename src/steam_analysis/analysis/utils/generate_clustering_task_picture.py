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


def generate_line_plot(data: AbstractGameBy_, title_name: str,
                       path_to_save: str, columns_num: int = None,
                       xlabel_val: str = "X", ylabel_val: str = "Y") -> None:
    ticks, values = data_prep(data)

    if not columns_num: columns_num = len(ticks)

    if len(ticks) > columns_num:
        step = len(ticks) // columns_num
        indices = list(range(0, len(ticks), step))[:columns_num]
        ticks_display = [ticks[i] for i in indices]
        values_display = [values[i] for i in indices]
        if len(ticks) - 1 not in indices:
            ticks_display.append(ticks[-1])
            values_display.append(values[-1])
    else:
        ticks_display = ticks
        values_display = values

    x_positions = np.arange(len(ticks_display))

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(x_positions, values_display,
            color='blue', marker='o',
            markersize=3, markerfacecolor="crimson")

    ax.set_title(title_name, fontsize=14)
    ax.set_xlabel(xlabel_val, fontsize=12)
    ax.set_ylabel(ylabel_val, fontsize=12)

    if len(ticks_display) <= 30:
        ax.set_xticks(x_positions)
        ax.set_xticklabels(ticks_display, rotation=45, ha='right', fontsize=10)

    ax.grid(True, alpha=0.3, linestyle='--')

    max_idx = np.argmax(values_display)
    min_idx = np.argmin(values_display)

    if values_display:
        ax.annotate(f'Max: {values_display[max_idx]:,}',
                    xy=(x_positions[max_idx], values_display[max_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=9, color='red')

        if max_idx != min_idx:
            ax.annotate(f'Min: {values_display[min_idx]:,}',
                        xy=(x_positions[min_idx], values_display[min_idx]),
                        xytext=(10, -20), textcoords='offset points',
                        arrowprops=dict(arrowstyle='->', color='green'),
                        fontsize=9, color='green')

    plt.tight_layout()
    plt.savefig(path_to_save)
    plt.close(fig)


def generate_heatmap(data: AbstractGameBy_, title_name: str,
                     path_to_save: str, matrix_size: Tuple[int, int] = (10, 10),
                    xlabel_val: str = "X", ylabel_val: str = "Y") -> None:
    ticks, values = data_prep(data)
    rows, cols = matrix_size
    if len(values) < rows * cols:
        values_extended = values + [0] * (rows * cols - len(values))
    else:
        values_extended = values[:rows * cols]

    matrix = np.array(values_extended).reshape(rows, cols)

    if len(ticks) >= rows:
        row_labels = ticks[:rows]
    else:
        row_labels = [f"Row {i + 1}" for i in range(rows)]

    col_labels = [f"Col {i + 1}" for i in range(cols)]

    fig, ax = plt.subplots(figsize=(12, 10))

    im = ax.imshow(matrix, cmap='viridis', aspect='auto')

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Значение', rotation=-90, va="bottom")

    ax.set_xticks(np.arange(cols))
    ax.set_yticks(np.arange(rows))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(rows):
        for j in range(cols):
            text = ax.text(j, i, f'{matrix[i, j]:,}',
                           ha="center", va="center",
                           color="w" if matrix[i, j] > matrix.max() / 2 else "black",
                           fontsize=8)

    ax.set_title(title_name, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel_val)
    ax.set_ylabel(ylabel_val)

    plt.tight_layout()
    plt.savefig(path_to_save)
    plt.close(fig)


def generate_histogram(data: AbstractGameBy_, title_name: str,
                       path_to_save: str, bins_num: int = 20,
                       color: str = 'skyblue', density: bool = False,
                       xlabel_val: str ="X") -> None:

    ticks, values = data_prep(data)

    numeric_values = []
    for v in values:
        try:
            numeric_values.append(float(v))
        except:
            numeric_values.append(0)

    fig, ax = plt.subplots(figsize=(12, 6))

    n, bins, patches = ax.hist(numeric_values, bins=bins_num,
                               color=color, edgecolor='black',
                               alpha=0.7, density=density)

    max_bin_idx = np.argmax(n)
    patches[max_bin_idx].set_facecolor('crimson')
    patches[max_bin_idx].set_edgecolor('black')

    ax.set_title(title_name, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel_val, fontsize=12)
    ax.set_ylabel("Плотность" if density else "Частота", fontsize=12)

    mean_val = np.mean(numeric_values)
    median_val = np.median(numeric_values)
    std_val = np.std(numeric_values)

    ax.axvline(mean_val, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Mean: {mean_val:.2f}')
    ax.axvline(median_val, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Median: {median_val:.2f}')

    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)