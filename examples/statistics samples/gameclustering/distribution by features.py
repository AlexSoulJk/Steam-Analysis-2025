from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.config import examples_statistics_images_path
from pathlib import Path

from steam_analysis.proccessors.schemas.games import GamesByTypes, AbstractGameBy_
from matplotlib.patches import Patch

from steam_analysis.proccessors.schemas.games import AbstractGameBy_
import matplotlib.pyplot as plt
import numpy as np

from typing import Tuple, List


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
        top_ticks = [t[0] for t in combined[:columns_num - 1]]
        top_values = [t[1] for t in combined[:columns_num - 1]]
        others_sum = sum(t[1] for t in combined[columns_num - 1:])
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
                            path_to_save: str, columns_num=10) -> None:
    ticks, values = create_data_columns(data, columns_num)

    fig, ax = plt.subplots(figsize=(10, 8))

    sorted_data = sorted(zip(values, ticks), reverse=True)

    top_three_values = [v for v, _ in sorted_data[:3]]
    top_three_labels = [l for _, l in sorted_data[:3]]

    red_shades = ['#FF0000', '#CC0000', '#990000']

    colors = []
    colors_blank = ['none' for _ in values]

    for i, (val, label) in enumerate(zip(values, ticks)):
        if label in top_three_labels:
            idx = top_three_labels.index(label)
            colors.append(red_shades[idx])
        else:
            colors.append('none')

    wedges, texts, autotexts = ax.pie(
        values,
        labels=ticks,
        colors=colors_blank,
        autopct=lambda pct: f'{pct:.1f}%)',
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

    legend_elements = []
    for i, (label, color) in enumerate(zip(top_three_labels, red_shades)):
        if i < len(top_three_labels):
            legend_elements.append(
                Patch(facecolor=color, edgecolor='black',
                      linewidth=1.5, label=f'Топ-{i + 1}: {label}')
            )

    legend_elements.append(
        Patch(facecolor='none', edgecolor='black',
              linewidth=1.5, label='Остальные категории')
    )

    ax.legend(
        handles=legend_elements,
        loc='center left',
        bbox_to_anchor=(1, 1),
        fontsize=10,
        title="Категории",
        title_fontsize=11
    )

    ax.set_title(title_name, fontsize=14, fontweight='bold')
    ax.axis('equal')

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    pass

def main():
    pdp = ProcessedDataProvider()
    # distribution = pdp.get_games_by_types()
    distribution = pdp.get_games_by_categories()

    generate_distribution_by_feature(distribution, "title_name", "res/test.png", 20)
    generate_pie_by_feature(distribution, "title_name", "res/pie_test.png", 10)


main()

# def main():
#     dir_to_save = fr"{examples_statistics_images_path}/gameclustering"
#     pdp = ProcessedDataProvider()
#
#     distribution, genres_name = pdp.get_games_by_genres()
#     generate_distribution_by_feature(data=distribution,
#                                      features_name=genres_name,
#                                      title_name="жанрам",
#                                      path_to_save=fr"{dir_to_save}/distribution_by_genres.png")
#
#     distribution, categories_name = pdp.get_games_by_categories()
#     generate_distribution_by_feature(data=distribution,
#                                      features_name=categories_name,
#                                      title_name="категориям",
#                                      path_to_save=fr"{dir_to_save}/distribution_by_categories.png")
#     pass
