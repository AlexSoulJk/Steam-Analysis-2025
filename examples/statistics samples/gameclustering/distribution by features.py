from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.config import examples_statistics_images_path

from steam_analysis.proccessors.schemas.games import GamesByTypes, AbstractGameBy_
from matplotlib.patches import Patch, Wedge

from steam_analysis.proccessors.schemas.games import AbstractGameBy_
import matplotlib.pyplot as plt
import numpy as np

from typing import Tuple, List
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


def generate_detailed_pie_by_feature(data: AbstractGameBy_, title_name: str,
                              path_to_save: str,
                              sections_num: int,
                              inner_sections: int) -> None:

    ticks = data.ticks
    values_data = data.values


    outer_items = []
    for tick in ticks:
        tick_data = values_data.get(str(tick), values_data.get(tick, {}))
        total = sum(tick_data.values())

        if total > 0:
            sorted_inner = sorted(tick_data.items(),
                                  key=lambda x: x[1],
                                  reverse=True)
            outer_items.append((str(tick), total, sorted_inner))

    if len(outer_items) > sections_num:
        outer_items.sort(key=lambda x: x[1], reverse=True)

        top_items = outer_items[:sections_num - 1]
        others_items = outer_items[sections_num - 1:]

        others_total = sum(item[1] for item in others_items)

        combined_inner = {}
        for _, _, inner in others_items:
            for label, value in inner:
                combined_inner[label] = combined_inner.get(label, 0) + value

        sorted_combined = sorted(combined_inner.items(),
                                 key=lambda x: x[1],
                                 reverse=True)

        outer_items = top_items + [("Others", others_total, sorted_combined)]

    fig, ax = plt.subplots(figsize=(14, 10))

    outer_values = [item[1] for item in outer_items]
    outer_labels = [f"{item[0]} кат." for item in outer_items]

    wedges_outer, texts_outer, autotexts_outer = ax.pie(
        outer_values,
        labels=outer_labels,
        autopct=lambda pct: f'{pct:.1f}%',
        startangle=90,
        radius=1.0,
        wedgeprops=dict(width=0.35, edgecolor='black', linewidth=1.5)
    )

    colors_outer = plt.cm.Set3(np.arange(len(outer_items)))
    for wedge, color in zip(wedges_outer, colors_outer):
        pass

    for i, (wedge, outer_item) in enumerate(zip(wedges_outer, outer_items)):
        outer_label, outer_total, inner_items = outer_item

        theta1 = wedge.theta1
        theta2 = wedge.theta2
        wedge_width = theta2 - theta1

        top_inner = inner_items[:inner_sections]
        if len(top_inner) < inner_sections:
            other_sum = outer_total - sum(v for _, v in top_inner)
            if other_sum > 0:
                top_inner.append(("Остальные", other_sum))

        inner_values = [v for _, v in top_inner]
        inner_labels = [l for l, _ in top_inner]

        inner_angles = [v / outer_total * wedge_width for v in inner_values]

        if i % 3 == 0:
            cmap = plt.cm.Reds
        elif i % 3 == 1:
            cmap = plt.cm.Blues
        else:
            cmap = plt.cm.Greens

        inner_colors = cmap(np.linspace(0.3, 0.8, len(top_inner)))

        current_angle = theta1

        for j, (inner_angle, color) in enumerate(zip(inner_angles, inner_colors)):
            inner_wedge = Wedge(
                (0, 0), 0.65,
                current_angle, current_angle + inner_angle,
                facecolor=color,
                edgecolor='black',
                linewidth=1,
                alpha=0.8
            )
            ax.add_patch(inner_wedge)

            if inner_values[j] / outer_total > 0.15:  # >15%
                mid_angle = current_angle + inner_angle / 2
                angle_rad = np.deg2rad(mid_angle)

                x = 0.5 * np.cos(angle_rad)
                y = 0.5 * np.sin(angle_rad)

                label = inner_labels[j]
                if len(label) > 15:
                    label = label[:12] + "..."

                percentage = inner_values[j] / outer_total * 100

                ax.text(x, y, f"{label}\n{percentage:.0f}%",
                        ha='center', va='center',
                        fontsize=6, fontweight='bold',
                        rotation=mid_angle,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

            current_angle += inner_angle

    centre_circle = plt.Circle((0, 0), 0.3,
                               facecolor='white',
                               edgecolor='black',
                               linewidth=2)
    ax.add_artist(centre_circle)

    total = sum(outer_values)
    ax.text(0, 0, f"Всего:\n{total:,}",
            ha='center', va='center',
            fontsize=10, fontweight='bold')

    ax.set_title(f"{title_name}\nВнешний: {sections_num} групп, Внутренний: {inner_sections} подгрупп",
                 fontsize=12, fontweight='bold', pad=20)
    ax.axis('equal')

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)



def main():
    pdp = ProcessedDataProvider()
    # distribution = pdp.get_games_by_types()
    # distribution = pdp.get_games_by_categories()
    distribution = pdp.get_games_by_categories_count()


    # generate_distribution_by_feature(distribution, "title_name", "res/test.png", 20)
    # generate_pie_by_feature(distribution, "title_name", "res/pie_test.png", 15, 3)
    generate_detailed_pie_by_feature(distribution, "title_name", "res/pie_detail_test.png", sections_num=8, inner_sections=2)


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
