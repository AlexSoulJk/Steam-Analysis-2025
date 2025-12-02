from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.config import examples_statistics_images_path
from pathlib import Path

from steam_analysis.proccessors.schemas.games import GamesByTypes, AbstractGameBy_

from steam_analysis.proccessors.schemas.games import AbstractGameBy_
import matplotlib.pyplot as plt
import numpy as np


def generate_distribution_by_feature(data: AbstractGameBy_, title_name: str,
                                     path_to_save: str) -> None:
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

    fig, ax = plt.subplots(figsize=(12, 6))

    if len(ticks) > 10:
        combined = list(zip(ticks, values))
        combined.sort(key=lambda x: x[1], reverse=True)
        top_ticks = [t[0] for t in combined[:9]]
        top_values = [t[1] for t in combined[:9]]
        others_sum = sum(t[1] for t in combined[9:])
        ticks = top_ticks + ["others"]
        values = top_values + [others_sum]

    x_positions = np.arange(len(ticks))

    bars = ax.bar(x_positions, values, color='skyblue', edgecolor='black', alpha=0.7)

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


def main():
    pdp = ProcessedDataProvider()
    # distribution = pdp.get_games_by_types()
    distribution = pdp.get_games_by_categories()

    generate_distribution_by_feature(distribution, "title_name", "res/test.png")


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
