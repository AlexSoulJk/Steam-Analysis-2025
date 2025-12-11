from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.config import examples_statistics_images_path
from typing import Tuple, List, Any, Optional, Dict
from collections import Counter
import json
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from scipy import stats
import warnings


from steam_analysis.proccessors.schemas.games import (AbstractGameBy_, GamesClusteringData,
                                                      ClusteringResult, ClusterInfo,
                                                      CorrelationHeatmapData, TwoDHistogramData, GamesReleaseBySeason,
                                                      HistogramAnalysisResult, GroupedHistogramData, EnhancedHistogramData)


from collections import Counter


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


# def generate_heatmap(
#         data: AbstractGameBy_,
#         title_name: str,
#         path_to_save: str,
#         matrix_size: Tuple[int, int] = (10, 10),
#         xlabel_val: str = "X",
#         ylabel_val: str = "Y"
# ) -> None:
#     ticks, values = data_prep(data)
#     rows, cols = matrix_size
#
#     sorted_pairs = sorted(zip(values, ticks), reverse=True)
#     sorted_values = [p[0] for p in sorted_pairs]
#     sorted_ticks = [p[1] for p in sorted_pairs]
#
#     total = rows * cols
#     if len(sorted_values) < total:
#         sorted_values += [0] * (total - len(sorted_values))
#     else:
#         sorted_values = sorted_values[:total]
#         sorted_ticks = sorted_ticks[:total]
#
#     matrix = np.array(sorted_values).reshape(rows, cols)
#
#     if len(sorted_ticks) >= rows:
#         row_labels = sorted_ticks[:rows]
#     else:
#         row_labels = [f"Row {i+1}" for i in range(rows)]
#
#     col_labels = [f"Col {i+1}" for i in range(cols)]
#
#     fig, ax = plt.subplots(figsize=(12, 10))
#     im = ax.imshow(matrix, cmap='viridis', aspect='auto')
#
#     cbar = plt.colorbar(im, ax=ax)
#     cbar.ax.set_ylabel('Value', rotation=-90, va='bottom')
#
#     ax.set_xticks(np.arange(cols))
#     ax.set_yticks(np.arange(rows))
#     ax.set_xticklabels(col_labels)
#     ax.set_yticklabels(row_labels)
#
#     plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
#
#     vmin, vmax = matrix.min(), matrix.max()
#     mid = (vmin + vmax) / 2
#
#     for i in range(rows):
#         for j in range(cols):
#             val = matrix[i, j]
#             color = "white" if val < mid else "black"
#             ax.text(j, i, f"{val:,}", ha="center", va="center", fontsize=8, color=color)
#
#     ax.set_title(title_name, fontsize=16, fontweight='bold', pad=20)
#     ax.set_xlabel(xlabel_val)
#     ax.set_ylabel(ylabel_val)
#
#     plt.tight_layout()
#     plt.savefig(path_to_save, dpi=300)
#     plt.close(fig)



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


# def prepare_data_for_clustering(data: Any) -> Tuple[List[str], List[int]]:
#     """
#     Подготавливает данные для кластеризации из различных форматов.
#     Возвращает кортеж: (список меток, список значений)
#     """
#     print(f"Подготавливаю данные типа: {type(data)}")
#
#     # Если это строка (JSON)
#     if isinstance(data, str):
#         try:
#             data = json.loads(data)
#         except json.JSONDecodeError:
#             raise ValueError("Невалидный JSON")
#
#     # Если это словарь
#     if isinstance(data, dict):
#         if 'ticks' in data and 'values' in data:
#             ticks = data['ticks']
#             values_data = data['values']
#
#             # Обработка values в зависимости от типа
#             if isinstance(values_data, dict):
#                 values = []
#                 for tick in ticks:
#                     values.append(values_data.get(tick, 0))
#             elif isinstance(values_data, list):
#                 values = [int(v) for v in values_data]
#             else:
#                 raise TypeError(f"Неподдерживаемый тип values: {type(values_data)}")
#
#             print(f"Обработано из dict: {len(ticks)} тиков, {len(values)} значений")
#             return ticks, values
#
#     # Если это объект с атрибутами ticks и values
#     if hasattr(data, 'ticks') and hasattr(data, 'values'):
#         ticks = data.ticks
#         values_data = data.values
#
#         print(f"Тип values_data: {type(values_data)}")
#
#         if isinstance(values_data, dict):
#             values = []
#             for tick in ticks:
#                 if tick in values_data:
#                     values.append(int(values_data[tick]))
#                 else:
#                     values.append(0)
#             return ticks, values
#         elif isinstance(values_data, list):
#             # Преобразуем все значения в int
#             values = [int(v) for v in values_data]
#             return ticks, values
#
#     # Если это уже кортеж или список
#     if isinstance(data, (tuple, list)) and len(data) == 2:
#         ticks, values = data
#         if isinstance(ticks, list) and isinstance(values, list):
#             return ticks, values
#
#     raise ValueError(f"Неподдерживаемый формат данных: {type(data)}")
#
#
# def generate_scatter_clusters(data: Any, title_name: str,
#                               path_to_save: str, max_clusters: int = 10,
#                               max_points_per_cluster: int = 100) -> None:
#
#     ticks, values = prepare_data_for_clustering(data)
#
#     if len(ticks) < 2:
#         raise ValueError(f"Недостаточно данных для кластеризации: {len(ticks)} категорий")
#
#     print(f"Обработано категорий: {len(ticks)}")
#     print(f"Пример тиков: {ticks[:5]}...")
#     print(f"Пример значений: {values[:5]}...")
#
#     x_coords = []
#     y_coords = []
#     original_values = []
#
#     for i, (tick, value) in enumerate(zip(ticks, values)):
#         x = float(i)
#
#         y = np.log10(float(value) + 1) if value > 0 else 0.0
#
#         x_coords.append(x)
#         y_coords.append(y)
#         original_values.append(value)
#
#     X = np.column_stack([x_coords, y_coords])
#
#     if len(X) >= 3:
#         n_clusters = min(max_clusters, len(set(values)) or 3)
#         n_clusters = max(2, min(n_clusters, len(X) // 5 + 1))
#     else:
#         n_clusters = min(len(X), 2)
#
#     print(f"Использую {n_clusters} кластеров для {len(X)} точек")
#
#     kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
#     cluster_labels = kmeans.fit_predict(X)
#
#     fig, ax = plt.subplots(figsize=(14, 10))
#
#     colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))
#     markers = ['o', 's', '^', 'v', '<', '>', 'p', '*', 'h', 'D', 'X']
#
#     for cluster_id in range(n_clusters):
#         mask = cluster_labels == cluster_id
#         if not np.any(mask):
#             continue
#
#         cluster_indices = np.where(mask)[0]
#         cluster_x = [x_coords[i] for i in cluster_indices]
#         cluster_y = [y_coords[i] for i in cluster_indices]
#         cluster_ticks = [ticks[i] for i in cluster_indices]
#         cluster_vals = [original_values[i] for i in cluster_indices]
#
#         if max(original_values) > 0:
#             sizes = [50 + 200 * (v / max(original_values)) for v in cluster_vals]
#         else:
#             sizes = [100] * len(cluster_vals)
#
#         marker_idx = cluster_id % len(markers)
#
#         ax.scatter(cluster_x, cluster_y,
#                    s=sizes,
#                    c=[colors[cluster_id]],
#                    marker=markers[marker_idx],
#                    alpha=0.7,
#                    edgecolors='black',
#                    linewidth=1,
#                    label=f'Кластер {cluster_id + 1} (n={len(cluster_x)})')
#
#     ax.set_title(f"{title_name}\nКластеризация по {len(ticks)} категориям",
#                  fontsize=16, fontweight='bold', pad=20)
#     ax.set_xlabel("Категории (индекс)", fontsize=12)
#     ax.set_ylabel("log10(Количество + 1)", fontsize=12)
#
#     if len(ticks) <= 20:
#         ax.set_xticks(range(len(ticks)))
#         ax.set_xticklabels(ticks, rotation=45, ha='right', fontsize=9)
#     else:
#         step = max(1, len(ticks) // 10)
#         indices = list(range(0, len(ticks), step))
#         ax.set_xticks(indices)
#         ax.set_xticklabels([ticks[i] for i in indices], rotation=45, ha='right', fontsize=8)
#
#     ax.legend(title=f"Кластеры (всего: {n_clusters})", loc='upper right', fontsize=9)
#
#     ax.grid(True, alpha=0.3, linestyle='--', axis='y')
#
#     cluster_counts = Counter(cluster_labels)
#     cluster_info = "\n".join([f"Кластер {k + 1}: {v} категорий"
#                               for k, v in sorted(cluster_counts.items())])
#
#     total_sum = sum(values)
#     max_val = max(values)
#     max_tick = ticks[values.index(max_val)]
#
#     info_text = f"""Статистика:
# {cluster_info}
#
# Общая статистика:
# Всего элементов: {total_sum:,}
# Категорий: {len(ticks)}
# Максимум: {max_tick} ({max_val:,})
# Среднее: {np.mean(values):.1f}
# Медиана: {np.median(values):.1f}"""
#
#     ax.text(0.02, 0.98, info_text,
#             transform=ax.transAxes,
#             verticalalignment='top',
#             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
#             fontsize=9)
#
#     plt.tight_layout()
#     plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
#     plt.close(fig)
#
#     print(f"✅ График сохранен: {path_to_save}")
#
#     print("\n--- СТАТИСТИКА КЛАСТЕРИЗАЦИИ ---")
#     for cluster_id in range(n_clusters):
#         mask = cluster_labels == cluster_id
#         cluster_values = [original_values[i] for i in np.where(mask)[0]]
#         cluster_ticks_list = [ticks[i] for i in np.where(mask)[0]]
#
#         if cluster_values:
#             print(f"\nКластер {cluster_id + 1}:")
#             print(f"  Количество категорий: {len(cluster_values)}")
#             print(f"  Сумма значений: {sum(cluster_values):,}")
#             print(f"  Среднее: {np.mean(cluster_values):.1f}")
#             print(f"  Топ-3 категории: {sorted(zip(cluster_values, cluster_ticks_list), reverse=True)[:3]}")


def perform_games_clustering(
        data: GamesClusteringData,
        title_name: str,
        path_to_save: str,
        method: str = "kmeans",
        n_clusters: int = 5,
        features_to_show: Optional[List[str]] = None
) -> ClusteringResult:
    """
    Выполняет кластеризацию игр и создает визуализацию.

    Args:
        data: Данные для кластеризации
        title_name: Заголовок
        path_to_save: Путь для сохранения
        method: Метод кластеризации ('kmeans', 'dbscan')
        n_clusters: Количество кластеров (для kmeans)
        features_to_show: Признаки для отображения в визуализации

    Returns:
        ClusteringResult с информацией о кластерах
    """
    print(f"Кластеризация {len(data.games)} игр по {len(data.feature_names)} признакам")

    if not data.feature_matrix:
        raise ValueError("Нет матрицы признаков для кластеризации")

    X = np.array(data.feature_matrix)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if method.lower() == "kmeans":
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    elif method.lower() == "dbscan":
        clusterer = DBSCAN(eps=0.5, min_samples=5)
    else:
        raise ValueError(f"Неизвестный метод кластеризации: {method}")

    cluster_labels = clusterer.fit_predict(X_scaled)

    n_noise = np.sum(cluster_labels == -1) if hasattr(clusterer, 'labels_') else 0
    if n_noise > 0:
        print(f"DBSCAN обнаружил {n_noise} шумных точек (кластер -1)")
        max_cluster = cluster_labels.max()
        cluster_labels[cluster_labels == -1] = max_cluster + 1

    print("Выполняю уменьшение размерности для визуализации...")

    pca = PCA(n_components=2)
    X_reduced = pca.fit_transform(X_scaled)

    clusters_info = []
    unique_clusters = sorted(np.unique(cluster_labels))

    for cluster_id in unique_clusters:
        mask = cluster_labels == cluster_id
        cluster_points = X_scaled[mask]

        feature_stats = {}
        for i, feature_name in enumerate(data.feature_names):
            feature_values = X[mask, i]
            if len(feature_values) > 0:
                feature_stats[feature_name] = {
                    'mean': float(np.mean(feature_values)),
                    'std': float(np.std(feature_values)),
                    'min': float(np.min(feature_values)),
                    'max': float(np.max(feature_values)),
                    'median': float(np.median(feature_values))
                }

        top_games = []
        if method == "kmeans" and hasattr(clusterer, 'cluster_centers_'):
            centroid = clusterer.cluster_centers_[cluster_id]
            distances = np.linalg.norm(cluster_points - centroid, axis=1)
            closest_indices = np.argsort(distances)[:5]

            for idx in closest_indices:
                game_idx = np.where(mask)[0][idx]
                game = data.games[game_idx]
                top_games.append({
                    'app_id': game.app_id,
                    'name': game.name,
                    'distance_to_center': float(distances[idx])
                })

        clusters_info.append(ClusterInfo(
            cluster_id=int(cluster_id),
            size=int(np.sum(mask)),
            centroid=clusterer.cluster_centers_[cluster_id].tolist() if hasattr(clusterer, 'cluster_centers_') else [],
            feature_stats=feature_stats,
            top_games=top_games,
            description=None
        ))

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    axes = axes.flatten()

    ax1 = axes[0]
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_clusters)))

    for cluster_id, color in zip(unique_clusters, colors):
        mask = cluster_labels == cluster_id
        ax1.scatter(X_reduced[mask, 0], X_reduced[mask, 1],
                    c=[color],
                    s=30,
                    alpha=0.6,
                    edgecolors='black',
                    linewidth=0.5,
                    label=f'Кластер {cluster_id}')

    ax1.set_title(f"Кластеризация игр\nВсего: {len(data.games)} игр, {len(unique_clusters)} кластеров",
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel(f"Компонента 1 ({pca.explained_variance_ratio_[0]:.1%} дисперсии)")
    ax1.set_ylabel(f"Компонента 2 ({pca.explained_variance_ratio_[1]:.1%} дисперсии)")
    ax1.legend(title="Кластеры", fontsize=9)
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    cluster_sizes = [info.size for info in clusters_info]
    cluster_ids = [info.cluster_id for info in clusters_info]

    bars = ax2.bar(range(len(cluster_sizes)), cluster_sizes, color=colors, edgecolor='black')
    ax2.set_title("Размеры кластеров", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Номер кластера")
    ax2.set_ylabel("Количество игр")
    ax2.set_xticks(range(len(cluster_sizes)))
    ax2.set_xticklabels([f"Кластер {cid}" for cid in cluster_ids])

    for bar, size in zip(bars, cluster_sizes):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{size}',
                 ha='center', va='bottom', fontsize=9)

    ax3 = axes[2]

    if features_to_show:
        key_features = [f for f in features_to_show if f in data.feature_names][:6]
    else:
        feature_stds = np.std(X, axis=0)
        top_feature_indices = np.argsort(feature_stds)[-6:][::-1]
        key_features = [data.feature_names[i] for i in top_feature_indices]

    heatmap_data = []
    for cluster_info in clusters_info:
        row = []
        for feature in key_features:
            if feature in cluster_info.feature_stats:
                row.append(cluster_info.feature_stats[feature]['mean'])
            else:
                row.append(0)
        heatmap_data.append(row)

    im = ax3.imshow(heatmap_data, cmap='viridis', aspect='auto')

    ax3.set_title("Средние значения признаков по кластерам", fontsize=14, fontweight='bold')
    ax3.set_xlabel("Признаки")
    ax3.set_ylabel("Кластеры")

    ax3.set_xticks(range(len(key_features)))
    ax3.set_xticklabels(key_features, rotation=45, ha='right', fontsize=8)

    ax3.set_yticks(range(len(clusters_info)))
    ax3.set_yticklabels([f"Кластер {info.cluster_id}" for info in clusters_info])

    plt.colorbar(im, ax=ax3, fraction=0.046, pad=0.04)

    ax4 = axes[3]
    ax4.axis('off')

    description_text = "ОПИСАНИЕ КЛАСТЕРОВ:\n\n"
    for cluster_info in clusters_info:
        desc = f"Кластер {cluster_info.cluster_id} ({cluster_info.size} игр):\n"

        if cluster_info.feature_stats:
            top_features = sorted(
                cluster_info.feature_stats.items(),
                key=lambda x: abs(x[1]['mean']),
                reverse=True
            )[:3]

            for feat_name, stats in top_features:
                desc += f"  • {feat_name}: {stats['mean']:.2f}\n"

        if cluster_info.top_games:
            desc += "  Примеры игр:\n"
            for game in cluster_info.top_games[:2]:
                desc += f"    - {game['name'][:30]}...\n"

        description_text += desc + "\n"

    ax4.text(0.02, 0.98, description_text,
             transform=ax4.transAxes,
             verticalalignment='top',
             fontsize=9,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    plt.suptitle(title_name, fontsize=18, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Кластеризация завершена. График сохранен: {path_to_save}")

    game_assignments = {
        game.app_id: int(cluster_labels[i])
        for i, game in enumerate(data.games)
    }

    result = ClusteringResult(
        clusters=clusters_info,
        game_assignments=game_assignments,
        n_clusters=len(unique_clusters),
        method=method,
        reduced_2d=X_reduced.tolist(),
        values={"total_games": len(data.games), "n_clusters": len(unique_clusters)},
        ticks=[f"Cluster_{cid}" for cid in unique_clusters]
    )

    return result


import pandas as pd
from matplotlib.colors import LinearSegmentedColormap




def generate_correlation_heatmap(
        data: CorrelationHeatmapData,
        title_name: str,
        path_to_save: str,
        cmap: str = "RdBu_r",
        annotate: bool = True,
        figsize: Tuple[int, int] = (12, 10)
) -> None:
    """
    Генерирует heatmap матрицы корреляций между признаками.

    Args:
        data: Данные с матрицей корреляций
        title_name: Заголовок графика
        path_to_save: Путь для сохранения
        cmap: Цветовая карта
        annotate: Добавлять ли числовые значения в ячейки
        figsize: Размер фигуры
    """
    corr_matrix = np.array(data.correlation_matrix)
    feature_names = data.feature_names if hasattr(data, 'feature_names') else data.ticks

    if len(feature_names) != corr_matrix.shape[0]:
        raise ValueError(f"Количество названий признаков ({len(feature_names)}) "
                         f"не совпадает с размером матрицы ({corr_matrix.shape[0]})")

    fig, ax = plt.subplots(figsize=figsize)

    im = ax.imshow(corr_matrix, cmap=cmap, aspect='auto',
                   vmin=-1, vmax=1)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Коэффициент корреляции', rotation=-90, va='bottom')

    ax.set_xticks(np.arange(len(feature_names)))
    ax.set_yticks(np.arange(len(feature_names)))
    ax.set_xticklabels(feature_names, rotation=45, ha='right', fontsize=10)
    ax.set_yticklabels(feature_names, fontsize=10)

    if annotate:
        for i in range(len(feature_names)):
            for j in range(len(feature_names)):
                value = corr_matrix[i, j]
                color = "white" if abs(value) > 0.5 else "black"
                text = f"{value:.2f}" if not np.isnan(value) else "NaN"
                ax.text(j, i, text,
                        ha="center", va="center",
                        color=color, fontsize=8, fontweight='bold')

    threshold = 0.7
    strong_corr_indices = np.where(np.abs(corr_matrix) > threshold)

    for i, j in zip(*strong_corr_indices):
        if i != j:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                 fill=False, edgecolor='red',
                                 linewidth=2, linestyle='--')
            ax.add_patch(rect)

    ax.set_title(f"{title_name}\n"
                 f"Размер матрицы: {corr_matrix.shape[0]}×{corr_matrix.shape[1]}",
                 fontsize=14, fontweight='bold', pad=20)

    n_strong = len(strong_corr_indices[0]) - len(feature_names)
    info_text = f"Сильных корреляций (|r| > {threshold}): {n_strong}"

    ax.text(0.02, -0.1, info_text,
            transform=ax.transAxes,
            fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Heatmap корреляций сохранена: {path_to_save}")


def generate_2d_density_heatmap(
        data: TwoDHistogramData,
        title_name: str,
        path_to_save: str,
        cmap: str = "viridis",
        log_scale: bool = False,
        figsize: Tuple[int, int] = (12, 10)
) -> None:
    """
    Генерирует 2D heatmap/гистограмму распределения точек.

    Args:
        data: Данные с x и y значениями
        title_name: Заголовок графика
        path_to_save: Путь для сохранения
        cmap: Цветовая карта
        log_scale: Использовать логарифмическую шкалу для цвета
        figsize: Размер фигуры
    """
    x_values = np.array(data.x_values)
    y_values = np.array(data.y_values)

    if len(x_values) != len(y_values):
        raise ValueError(f"Количество X значений ({len(x_values)}) "
                         f"не совпадает с количеством Y значений ({len(y_values)})")

    mask = ~np.isnan(x_values) & ~np.isnan(y_values)
    x_values = x_values[mask]
    y_values = y_values[mask]

    if len(x_values) == 0:
        raise ValueError("Нет валидных данных для построения heatmap")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize,
                                   gridspec_kw={'width_ratios': [3, 1]})

    # 1. 2D Histogram (heatmap)
    h, xedges, yedges, im = ax1.hist2d(x_values, y_values,
                                       bins=(data.x_bins, data.y_bins),
                                       cmap=cmap)

    # Логарифмическая шкала цвета
    if log_scale and np.any(h > 0):
        h_log = np.log10(h + 1)
        im.set_array(h_log.T)
        cbar_label = 'log10(Количество + 1)'
    else:
        cbar_label = 'Количество'

    cbar = fig.colorbar(im, ax=ax1, shrink=0.8)
    cbar.set_label(cbar_label, rotation=-90, va='bottom')

    x_label = getattr(data, 'x_label', 'X')
    y_label = getattr(data, 'y_label', 'Y')

    ax1.set_xlabel(x_label, fontsize=12)
    ax1.set_ylabel(y_label, fontsize=12)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # 2. Маргинальные распределения (гистограммы по краям)
    # Гистограмма по X
    ax2_histx = ax2.inset_axes([0, 0.7, 1, 0.25])
    ax2_histx.hist(x_values, bins=data.x_bins, color='skyblue', edgecolor='black')
    ax2_histx.set_title(f"Распределение по {x_label}", fontsize=10)
    ax2_histx.set_ylabel("Частота")
    ax2_histx.grid(True, alpha=0.3)

    # Гистограмма по Y
    ax2_histy = ax2.inset_axes([0, 0.0, 1, 0.25])
    ax2_histy.hist(y_values, bins=data.y_bins, color='lightgreen',
                   edgecolor='black', orientation='horizontal')
    ax2_histy.set_title(f"Распределение по {y_label}", fontsize=10)
    ax2_histy.set_xlabel("Частота")
    ax2_histy.grid(True, alpha=0.3)

    info_ax = ax2.inset_axes([0, 0.35, 1, 0.3])
    info_ax.axis('off')

    stats_text = f"""Статистика:
Всего точек: {len(x_values):,}

X ({x_label}):
  Среднее: {np.mean(x_values):.2f}
  Медиана: {np.median(x_values):.2f}
  Min: {np.min(x_values):.2f}
  Max: {np.max(x_values):.2f}

Y ({y_label}):
  Среднее: {np.mean(y_values):.2f}
  Медиана: {np.median(y_values):.2f}
  Min: {np.min(y_values):.2f}
  Max: {np.max(y_values):.2f}

Корреляция: {np.corrcoef(x_values, y_values)[0, 1]:.3f}"""

    info_ax.text(0, 1, stats_text,
                 transform=info_ax.transAxes,
                 verticalalignment='top',
                 fontsize=9,
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax1.set_title(f"{title_name}\n"
                  f"Количество точек: {len(x_values):,}",
                  fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ 2D density heatmap сохранена: {path_to_save}")


def generate_time_series_heatmap(
        data: AbstractGameBy_,
        title_name: str,
        path_to_save: str,
        time_period: str = "month",  # "year", "quarter", "month", "week"
        value_type: str = "count",  # "count", "sum", "average"
        cmap: str = "YlOrRd",
        figsize: Tuple[int, int] = (14, 8)
) -> None:
    """
    Генерирует heatmap временных рядов (например, релизы по годам и месяцам).

    Args:
        data: Данные с временными метками и значениями
        title_name: Заголовок графика
        path_to_save: Путь для сохранения
        time_period: Период времени для агрегации
        value_type: Тип агрегации значений
        cmap: Цветовая карта
        figsize: Размер фигуры
    """
    ticks, values = data_prep(data)

    if len(ticks) == 0 or len(values) == 0:
        raise ValueError("Нет данных для построения heatmap")

    try:
        dates = pd.to_datetime(ticks, errors='coerce')
        valid_mask = ~dates.isna()

        if not valid_mask.any():
            raise ValueError("Тики не содержат валидных дат")

        dates = dates[valid_mask]
        values_filtered = np.array(values)[valid_mask]

    except Exception as e:
        print(f"Не удалось преобразовать тики в даты: {e}")
        dates = pd.RangeIndex(start=0, stop=len(ticks))
        values_filtered = np.array(values)

    df = pd.DataFrame({
        'date': dates,
        'value': values_filtered
    })

    if hasattr(df['date'].iloc[0], 'year'):
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['week'] = df['date'].dt.isocalendar().week
    else:
        df['year'] = df.index // 12
        df['month'] = df.index % 12 + 1

    if time_period == "year-month":
        pivot_data = df.pivot_table(
            index='year',
            columns='month',
            values='value',
            aggfunc=value_type,
            fill_value=0
        )
        xlabel = "Месяц"
        ylabel = "Год"
    elif time_period == "year-quarter":
        pivot_data = df.pivot_table(
            index='year',
            columns='quarter',
            values='value',
            aggfunc=value_type,
            fill_value=0
        )
        xlabel = "Квартал"
        ylabel = "Год"
    elif time_period == "month":
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(range(len(values)), values, marker='o', linestyle='-')
        ax.set_xlabel("Время", fontsize=12)
        ax.set_ylabel("Значение", fontsize=12)
        ax.set_title(title_name, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"✅ Временной ряд сохранен: {path_to_save}")
        return
    else:
        raise ValueError(f"Неподдерживаемый time_period: {time_period}")

    # Создаем heatmap
    fig, ax = plt.subplots(figsize=figsize)

    # Нормализуем для лучшей визуализации
    data_matrix = pivot_data.values

    if np.any(data_matrix > 0):
        # Используем логарифмическую шкалу, если значения сильно различаются
        if np.max(data_matrix) / np.min(data_matrix[np.nonzero(data_matrix)]) > 100:
            data_matrix_vis = np.log10(data_matrix + 1)
            cbar_label = 'log10(Значение + 1)'
            annot_format = lambda x: f"{x:.1f}"
        else:
            data_matrix_vis = data_matrix
            cbar_label = 'Значение'
            annot_format = lambda x: f"{int(x)}" if x == int(x) else f"{x:.1f}"
    else:
        data_matrix_vis = data_matrix
        cbar_label = 'Значение'
        annot_format = lambda x: f"{int(x)}"

    im = ax.imshow(data_matrix_vis, cmap=cmap, aspect='auto')

    # Цветовая шкала
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label(cbar_label, rotation=-90, va='bottom')

    # Настраиваем оси
    ax.set_xticks(np.arange(pivot_data.shape[1]))
    ax.set_yticks(np.arange(pivot_data.shape[0]))

    ax.set_xticklabels(pivot_data.columns, fontsize=10)
    ax.set_yticklabels(pivot_data.index, fontsize=10)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    # Поворачиваем подписи
    plt.setp(ax.get_xticklabels(), rotation=0)

    # Добавляем числовые значения
    for i in range(pivot_data.shape[0]):
        for j in range(pivot_data.shape[1]):
            value = data_matrix[i, j]
            if value > 0:  # Показываем только ненулевые значения
                color = "white" if data_matrix_vis[i, j] > np.median(data_matrix_vis[data_matrix_vis > 0]) else "black"
                ax.text(j, i, annot_format(value),
                        ha="center", va="center",
                        color=color, fontsize=8, fontweight='bold')

    # Статистика
    total_value = np.sum(data_matrix)
    max_value = np.max(data_matrix)
    max_idx = np.unravel_index(np.argmax(data_matrix), data_matrix.shape)
    max_year = pivot_data.index[max_idx[0]]
    max_period = pivot_data.columns[max_idx[1]]

    stats_text = f"""Статистика:
Всего: {total_value:,.0f}
Максимум: {max_value:,.0f} ({max_year}, {max_period})
Среднее: {np.mean(data_matrix[data_matrix > 0]):,.0f}
Ненулевых ячеек: {np.sum(data_matrix > 0)}/{data_matrix.size}"""

    ax.text(0.02, -0.1, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    ax.set_title(f"{title_name}\n"
                 f"Агрегация: {value_type}",
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Heatmap временного ряда сохранена: {path_to_save}")


def generate_heatmap(
        data: AbstractGameBy_,
        title_name: str,
        path_to_save: str,
        heatmap_type: str = "auto",  # "auto", "correlation", "2d_density", "time_series"
        **kwargs
) -> None:
    """
    Умная функция для генерации heatmap, которая определяет тип данных.

    Args:
        data: Данные для визуализации
        title_name: Заголовок
        path_to_save: Путь для сохранения
        heatmap_type: Тип heatmap ("auto", "correlation", "2d_density", "time_series")
        **kwargs: Дополнительные параметры для конкретного типа heatmap
    """
    if heatmap_type == "auto":
        if hasattr(data, 'correlation_matrix'):
            heatmap_type = "correlation"
        elif hasattr(data, 'x_values') and hasattr(data, 'y_values'):
            heatmap_type = "2d_density"
        elif hasattr(data, 'values') and isinstance(data.values, dict):
            ticks = data.ticks if hasattr(data, 'ticks') else []
            if ticks and any('/' in str(t) or '-' in str(t) for t in ticks[:5]):
                heatmap_type = "time_series"
            else:
                heatmap_type = "2d_density"
        else:
            heatmap_type = "2d_density"

    if heatmap_type == "correlation":
        generate_correlation_heatmap(data, title_name, path_to_save, **kwargs)
    elif heatmap_type == "2d_density":
        generate_2d_density_heatmap(data, title_name, path_to_save, **kwargs)
    elif heatmap_type == "time_series":
        generate_time_series_heatmap(data, title_name, path_to_save, **kwargs)
    else:
        raise ValueError(f"Неизвестный тип heatmap: {heatmap_type}")


# def generate_bubble_chart(data: AbstractGameBy_, title_name: str,
#                           path_to_save: str, size_factor: float = 1000) -> None:
#
#     ticks, values = data_prep(data)
#
#     if len(ticks) != len(values):
#         raise ValueError(f"Количество тиков ({len(ticks)}) не совпадает с количеством значений ({len(values)})")
#
#     sorted_pairs = sorted(zip(values, ticks), reverse=True)
#     values_sorted = [v for v, _ in sorted_pairs]
#     ticks_sorted = [t for _, t in sorted_pairs]
#
#     fig, ax = plt.subplots(figsize=(14, 8))
#
#     max_val = max(values_sorted)
#     sizes = [(v / max_val) * size_factor for v in values_sorted]
#
#     norm = plt.Normalize(min(values_sorted), max(values_sorted))
#     colors = plt.cm.viridis(norm(values_sorted))
#
#     scatter = ax.scatter(range(len(ticks_sorted)),
#                          [1] * len(ticks_sorted),
#                          s=sizes,
#                          c=colors,
#                          alpha=0.7,
#                          edgecolors='black',
#                          linewidth=1.5)
#
#     for i, (tick, value, size) in enumerate(zip(ticks_sorted, values_sorted, sizes)):
#         ax.annotate(f'{tick}\n{value:,}',
#                     xy=(i, 1),
#                     xytext=(0, 10 + size / 100),
#                     textcoords='offset points',
#                     ha='center',
#                     va='bottom',
#                     fontsize=9,
#                     bbox=dict(boxstyle="round,pad=0.3",
#                               facecolor="lightyellow",
#                               alpha=0.8))
#
#     ax.set_title(title_name, fontsize=16, fontweight='bold', pad=20)
#     ax.set_xlabel("Категории", fontsize=12)
#     ax.set_ylabel("")
#
#     ax.set_yticks([])
#     ax.set_xticks([])
#     ax.set_ylim(0.5, 1.8)
#
#     total = sum(values_sorted)
#     info_text = f"""Статистика:
# Всего элементов: {total:,}
# Категорий: {len(ticks_sorted)}
# Крупнейшая: {ticks_sorted[0]} ({values_sorted[0]:,})
# Мелчайшая: {ticks_sorted[-1]} ({values_sorted[-1]:,})
# Соотношение: {values_sorted[0] / values_sorted[-1]:.0f}:1"""
#
#     ax.text(0.02, 0.98, info_text,
#             transform=ax.transAxes,
#             verticalalignment='top',
#             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
#             fontsize=10)
#
#     plt.tight_layout()
#     plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
#     plt.close(fig)
#
#     print(f"✅ Пузырьковая диаграмма сохранена: {path_to_save}")


# import squarify
#
#
# def generate_treemap(data: AbstractGameBy_, title_name: str,
#                      path_to_save: str) -> None:
#     ticks, values = data_prep(data)
#
#     data_pairs = list(zip(ticks, values))
#     data_pairs.sort(key=lambda x: x[1], reverse=True)
#
#     labels = [f"{label}\n{value:,}" for label, value in data_pairs]
#     sizes = [value for _, value in data_pairs]
#     colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
#
#     fig, ax = plt.subplots(figsize=(14, 10))
#
#     squarify.plot(sizes=sizes,
#                   label=labels,
#                   color=colors,
#                   alpha=0.8,
#                   edgecolor='black',
#                   linewidth=1.5,
#                   text_kwargs={'fontsize': 9})
#
#     ax.set_title(title_name, fontsize=18, fontweight='bold', pad=20)
#     ax.axis('off')
#
#     patches = [Patch(facecolor=color, edgecolor='black', label=label.split('\n')[0])
#                for color, label in zip(colors, labels)]
#     ax.legend(handles=patches, title="Категории",
#               bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
#
#     plt.tight_layout()
#     plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
#     plt.close(fig)

# def generate_friend_graph(data: AbstractGameBy_, title_name: str,
#                           path_to_save: str, max_nodes: int = 50,
#                           min_cluster_size: int = 5) -> None:
#     """
#     Граф друзей с кластерами
#
#     Args:
#         data: входные данные (ожидается информация о друзьях и кластерах)
#         title_name: заголовок графика
#         path_to_save: путь для сохранения
#         max_nodes: максимальное количество узлов для отображения
#         min_cluster_size: минимальный размер кластера для отображения
#     """
#     try:
#         # Парсим данные (предполагаем структуру с друзьями и кластерами)
#         ticks, values = data_prep(data)
#
#         # Создаем искусственные данные для демонстрации
#         # В реальном использовании data должна содержать информацию о связях
#
#         # Создаем кластеры друзей
#         n_clusters = min(10, len(ticks) // min_cluster_size + 1)
#
#         if n_clusters < 2:
#             n_clusters = 3
#
#         # Создаем граф
#         G = nx.Graph()
#
#         # Создаем узлы-кластеры
#         cluster_nodes = []
#         cluster_sizes = []
#
#         for i in range(n_clusters):
#             cluster_size = np.random.randint(min_cluster_size, min_cluster_size * 3)
#             cluster_sizes.append(cluster_size)
#
#             # Создаем узел кластера
#             cluster_node_id = f"Cluster_{i}"
#             G.add_node(cluster_node_id,
#                        size=cluster_size * 10,  # Размер узла пропорционален размеру кластера
#                        color=i,
#                        type='cluster')
#
#             cluster_nodes.append(cluster_node_id)
#
#         # Добавляем связи между кластерами (более вероятно между большими кластерами)
#         for i in range(n_clusters):
#             for j in range(i + 1, n_clusters):
#                 # Вероятность связи зависит от размеров кластеров
#                 connection_prob = 0.3 * (cluster_sizes[i] + cluster_sizes[j]) / (2 * min_cluster_size)
#                 if np.random.random() < connection_prob:
#                     weight = np.random.randint(1, 10)
#                     G.add_edge(cluster_nodes[i], cluster_nodes[j], weight=weight)
#
#         # Позиционирование узлов
#         pos = nx.spring_layout(G, k=2, iterations=50)
#
#         fig, ax = plt.subplots(figsize=(14, 10))
#
#         # Получаем атрибуты узлов
#         node_sizes = [G.nodes[n]['size'] for n in G.nodes()]
#         node_colors = [G.nodes[n]['color'] for n in G.nodes()]
#
#         # Рисуем граф
#         nx.draw_networkx_nodes(G, pos,
#                                node_size=node_sizes,
#                                node_color=node_colors,
#                                cmap=plt.cm.tab20,
#                                alpha=0.8,
#                                ax=ax)
#
#         # Рисуем ребра
#         edges = G.edges()
#         weights = [G[u][v]['weight'] for u, v in edges]
#
#         nx.draw_networkx_edges(G, pos,
#                                edgelist=edges,
#                                width=[w * 0.5 for w in weights],
#                                alpha=0.5,
#                                edge_color='gray',
#                                ax=ax)
#
#         # Подписи узлов
#         labels = {node: node.replace('_', '\n') for node in G.nodes()}
#         nx.draw_networkx_labels(G, pos,
#                                 labels=labels,
#                                 font_size=9,
#                                 font_weight='bold',
#                                 ax=ax)
#
#         # Информация о кластерах
#         cluster_info = "\n".join([f"{cluster_nodes[i]}: {cluster_sizes[i]} чел."
#                                   for i in range(n_clusters)])
#
#         ax.text(0.02, 0.98, f"Кластеры друзей:\n{cluster_info}",
#                 transform=ax.transAxes,
#                 verticalalignment='top',
#                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
#                 fontsize=9)
#
#         ax.set_title(title_name, fontsize=16, fontweight='bold', pad=20)
#         ax.axis('off')
#
#         # Добавляем легенду для размеров
#         from matplotlib.patches import Circle
#         legend_elements = [
#             Circle((0, 0), radius=5, color='gray', alpha=0.6,
#                    label=f'Маленький кластер (~{min_cluster_size} чел.)'),
#             Circle((0, 0), radius=10, color='gray', alpha=0.6,
#                    label=f'Средний кластер (~{min_cluster_size * 2} чел.)'),
#             Circle((0, 0), radius=15, color='gray', alpha=0.6,
#                    label=f'Большой кластер (~{min_cluster_size * 3} чел.)')
#         ]
#
#         ax.legend(handles=legend_elements, loc='lower right', fontsize=8)
#
#         plt.tight_layout()
#         plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
#         plt.close(fig)
#
#     except Exception as e:
#         print(f"Ошибка при создании графа друзей: {e}")
#         # Резервный вариант - простой график
#         plt.figure(figsize=(10, 6))
#         plt.title(f"Граф: {title_name}")
#         plt.text(0.5, 0.5, "Данные графа недоступны\nили произошла ошибка",
#                  ha='center', va='center', transform=plt.gca().transAxes)
#         plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
#         plt.close()
#
#
#
# def generate_detailed_pie_by_feature(data: AbstractGameBy_, title_name: str,    # ХУЕТА
#                                      path_to_save: str,
#                                      sections_num: int,
#                                      inner_sections: int) -> None:
#
#     values_dict = data.values
#     all_ticks = data.ticks
#
#     main_sizes = {}
#     main_labels = []
#
#     tick_sizes = []
#     for tick in all_ticks:
#         if tick in values_dict:
#             total = sum(values_dict[tick].values())
#             tick_sizes.append((tick, total))
#         else:
#             tick_sizes.append((tick, 0))
#
#     tick_sizes.sort(key=lambda x: x[1], reverse=True)
#
#     # Берем только sections_num самых крупных
#     top_ticks = [tick for tick, size in tick_sizes[:sections_num]]
#
#     # Рассчитываем размеры для выбранных тиков
#     for tick in top_ticks:
#         if tick in values_dict:
#             main_sizes[tick] = sum(values_dict[tick].values())
#             main_labels.append(f"Section {tick}")
#         else:
#             main_sizes[tick] = 0
#             main_labels.append(f"Section {tick}")
#
#     # Добавляем секцию "others" если есть остальные тики
#     others_sum = 0
#     others_ticks = []
#     for tick, size in tick_sizes[sections_num:]:
#         if size > 0:
#             others_sum += size
#             others_ticks.append(tick)
#
#     if others_sum > 0:
#         main_sizes["others"] = others_sum
#         main_labels.append("Others")
#         all_main_ticks = list(top_ticks) + ["others"]
#     else:
#         all_main_ticks = list(top_ticks)
#
#     # 2. Подготавливаем данные для внутренних секций
#     inner_data = {}
#
#     # Для каждого основного тика (кроме others)
#     for tick in all_main_ticks:
#         if tick == "others":
#             continue
#
#         if tick in values_dict:
#             # Получаем все подсекции для этого тика
#             subsections = values_dict[tick]
#
#             # Сортируем подсекции по убыванию количества
#             sorted_subsections = sorted(
#                 subsections.items(),
#                 key=lambda x: x[1],
#                 reverse=True
#             )
#
#             # Отбираем top inner_sections
#             if len(sorted_subsections) > inner_sections:
#                 top_subsections = sorted_subsections[:inner_sections]
#                 others_sum_inner = sum(count for _, count in sorted_subsections[inner_sections:])
#                 if others_sum_inner > 0:
#                     top_subsections.append(("others", others_sum_inner))
#                 inner_data[tick] = top_subsections
#             else:
#                 inner_data[tick] = sorted_subsections
#
#     # 3. Если есть секция "others", готовим ее подсекции
#     if "others" in main_sizes and others_ticks:
#         all_other_subsections = {}
#         for tick in others_ticks:
#             if tick in values_dict:
#                 for key, value in values_dict[tick].items():
#                     prefixed_key = f"Sec{tick}:{key}"
#                     all_other_subsections[prefixed_key] = all_other_subsections.get(prefixed_key, 0) + value
#
#         # Сортируем и ограничиваем количество
#         sorted_other_subsections = sorted(
#             all_other_subsections.items(),
#             key=lambda x: x[1],
#             reverse=True
#         )
#
#         if len(sorted_other_subsections) > inner_sections:
#             top_other_subsections = sorted_other_subsections[:inner_sections]
#             others_sum_inner = sum(count for _, count in sorted_other_subsections[inner_sections:])
#             if others_sum_inner > 0:
#                 top_other_subsections.append(("others", others_sum_inner))
#             inner_data["others"] = top_other_subsections
#         else:
#             inner_data["others"] = sorted_other_subsections
#
#     # 4. Собираем все данные для круговой диаграммы
#     all_sizes = []
#     all_labels = []
#     all_colors = []
#
#     # Цвета для топ-3 внутренних секций
#     top_colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Синий, оранжевый, зеленый
#
#     # Для хранения границ основных секций
#     main_section_boundaries = []
#
#     # Проходим по всем основным секциям и их подсекциям
#     start_idx = 0
#     for tick in all_main_ticks:
#         if tick not in inner_data:
#             continue
#
#         subsections = inner_data[tick]
#         if not subsections:
#             continue
#
#         # Запоминаем начальный индекс для этой основной секции
#         main_section_boundaries.append(start_idx)
#
#         # Для каждой подсекции в этой основной секции
#         for j, (name, size) in enumerate(subsections):
#             if size == 0:
#                 continue
#
#             # Добавляем данные для этой подсекции
#             all_sizes.append(size)
#
#             # Формируем метку (только номер основной секции для подсекций)
#             if tick == "others":
#                 label = "Others"
#             else:
#                 label = f"Sec {tick}"
#
#             all_labels.append(label)
#
#             # Определяем цвет: топ-3 подсекции в каждой основной секции окрашиваются
#             if j < 3 and j < len(top_colors):
#                 color = top_colors[j]
#             else:
#                 color = 'none'  # Бесцветные
#
#             all_colors.append(color)
#
#         # Запоминаем конечный индекс для этой основной секции
#         start_idx += len(subsections)
#
#     # Добавляем последнюю границу
#     main_section_boundaries.append(len(all_sizes))
#
#     # 5. Создаем и настраиваем график
#     fig, ax = plt.subplots(figsize=(16, 14))
#
#     # Рисуем круговую диаграмму
#     wedges, texts = ax.pie(
#         all_sizes,
#         labels=all_labels,
#         colors=all_colors,
#         startangle=90,
#         wedgeprops={
#             'edgecolor': 'lightgray',
#             'linewidth': 0.5,
#             'linestyle': '-'
#         },
#         textprops={
#             'fontsize': 9,
#             'fontweight': 'bold'
#         },
#         radius=1.0
#     )
#
#     # 6. Настраиваем внешний вид каждого клина отдельно
#     for i, wedge in enumerate(wedges):
#         # Устанавливаем прозрачность для бесцветных секций
#         if all_colors[i] == 'none':
#             wedge.set_alpha(0.3)
#
#     # 7. Добавляем жирные границы для основных секций
#     # Проходим по всем границам основных секций
#     for i in range(len(main_section_boundaries) - 1):
#         start_idx = main_section_boundaries[i]
#         end_idx = main_section_boundaries[i + 1] - 1
#
#         if start_idx < len(wedges):
#             # Начало основной секции
#             wedges[start_idx].set_edgecolor('black')
#             wedges[start_idx].set_linewidth(3)
#
#         if end_idx >= 0 and end_idx < len(wedges):
#             # Конец основной секции
#             wedges[end_idx].set_edgecolor('black')
#             wedges[end_idx].set_linewidth(3)
#
#     # 8. Выводим информацию о подсекциях в консоль
#     print("\n" + "=" * 70)
#     print(f"DETAILED SUBSECTION ANALYSIS FOR '{title_name}'")
#     print("=" * 70)
#
#     total_games = sum(main_sizes.values())
#     print(f"\nTotal games in chart: {total_games:,}")
#     print(f"Main sections shown: {len(all_main_ticks)}")
#     print(f"Total sub-sections shown: {len(all_sizes)}")
#     print("=" * 70)
#
#     # Индекс для отслеживания позиции в all_sizes
#     current_idx = 0
#
#     for tick_idx, tick in enumerate(all_main_ticks):
#         if tick not in inner_data:
#             continue
#
#         subsections = inner_data[tick]
#         if not subsections:
#             continue
#
#         total_main_size = main_sizes[tick]
#
#         print(f"\n{'=' * 40}")
#         if tick == "others":
#             print(f"SECTION: OTHERS (Total: {total_main_size:,} games, {total_main_size / total_games * 100:.1f}%)")
#         else:
#             print(f"SECTION {tick} (Total: {total_main_size:,} games, {total_main_size / total_games * 100:.1f}%)")
#         print('=' * 40)
#
#         # Выводим все подсекции
#         for j, (name, size) in enumerate(subsections):
#             percentage_in_section = (size / total_main_size) * 100 if total_main_size > 0 else 0
#             percentage_total = (size / total_games) * 100 if total_games > 0 else 0
#
#             if name == "others":
#                 print(
#                     f"  Other subsections: {size:,} games ({percentage_in_section:.1f}% of section, {percentage_total:.1f}% total)")
#             elif tick == "others":
#                 # Обрезаем префикс для вывода
#                 if name.startswith("Sec"):
#                     display_name = name.split(":", 1)[-1]
#                     if len(display_name) > 45:
#                         display_name = display_name[:42] + "..."
#                 else:
#                     display_name = name
#                 print(
#                     f"  {display_name}: {size:,} games ({percentage_in_section:.1f}% of section, {percentage_total:.1f}% total)")
#             else:
#                 # Обрезаем длинные названия
#                 if len(name) > 50:
#                     display_name = name[:47] + "..."
#                 else:
#                     display_name = name
#
#                 marker = "★" if j < 3 else "○"
#                 print(
#                     f"  {marker} {display_name:50} {size:6,} games ({percentage_in_section:5.1f}% in sec, {percentage_total:5.1f}% total)")
#
#             current_idx += 1
#
#     # 9. Выводим статистику по топ-3 в каждой секции
#     print("\n" + "=" * 70)
#     print("TOP 3 SUBSECTIONS IN EACH MAIN SECTION (colored):")
#     print("=" * 70)
#
#     for tick in all_main_ticks:
#         if tick not in inner_data:
#             continue
#
#         subsections = inner_data[tick]
#         if not subsections:
#             continue
#
#         total_main_size = main_sizes[tick]
#
#         print(f"\nSection {tick if tick != 'others' else 'Others'}:")
#         top_n = min(3, len(subsections))
#         for j in range(top_n):
#             name, size = subsections[j]
#             if name == "others":
#                 continue
#
#             percentage_in_section = (size / total_main_size) * 100 if total_main_size > 0 else 0
#             percentage_total = (size / total_games) * 100 if total_games > 0 else 0
#
#             if tick == "others" and name.startswith("Sec"):
#                 display_name = name.split(":", 1)[-1]
#             else:
#                 display_name = name
#
#             if len(display_name) > 40:
#                 display_name = display_name[:37] + "..."
#
#             print(
#                 f"  {j + 1}. {display_name:40} {size:6,} games ({percentage_in_section:5.1f}% in sec, {percentage_total:5.1f}% total)")
#
#     # 10. Добавляем легенду и настраиваем график
#     from matplotlib.patches import Patch
#
#     # Создаем элементы для легенды
#     legend_elements = [
#         Patch(facecolor=top_colors[0], label='Top 1 inner section', alpha=0.7, edgecolor='gray'),
#         Patch(facecolor=top_colors[1], label='Top 2 inner section', alpha=0.7, edgecolor='gray'),
#         Patch(facecolor=top_colors[2], label='Top 3 inner section', alpha=0.7, edgecolor='gray'),
#         Patch(facecolor='none', edgecolor='lightgray', label='Other inner sections', alpha=0.3),
#         Patch(facecolor='none', edgecolor='black', linewidth=3, label='Main section border')
#     ]
#
#     # Добавляем легенду
#     ax.legend(handles=legend_elements, loc='center left',
#               bbox_to_anchor=(1.05, 0.5), fontsize=10, framealpha=0.9)
#
#     # Устанавливаем заголовок
#     ax.set_title(f"{title_name}\nMain sections: {sections_num}, Inner sections per main: {inner_sections}",
#                  fontsize=16, fontweight='bold', pad=20)
#
#     # Устанавливаем равные оси для круговой диаграммы
#     ax.set_aspect('equal')
#
#     # Сохраняем график
#     plt.tight_layout()
#     plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
#     plt.close(fig)
#
#     print(f"\n{'=' * 70}")
#     print(f"Chart saved to: {path_to_save}")
#     print('=' * 70)


def analyze_distribution(values: np.ndarray) -> HistogramAnalysisResult:
    """Анализирует распределение данных"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        mean = np.mean(values)
        median = np.median(values)
        std = np.std(values)
        skew = stats.skew(values)
        kurt = stats.kurtosis(values)

        # Процентили
        percentiles = {
            '1%': np.percentile(values, 1),
            '5%': np.percentile(values, 5),
            '25%': np.percentile(values, 25),
            '50%': np.percentile(values, 50),
            '75%': np.percentile(values, 75),
            '95%': np.percentile(values, 95),
            '99%': np.percentile(values, 99)
        }

        # Межквартильный размах
        iqr = percentiles['75%'] - percentiles['25%']

        # Выбросы (по правилу 1.5*IQR)
        lower_bound = percentiles['25%'] - 1.5 * iqr
        upper_bound = percentiles['75%'] + 1.5 * iqr
        outliers = values[(values < lower_bound) | (values > upper_bound)]

        # Тест на нормальность (Shapiro-Wilk, ограничение по размеру выборки)
        if len(values) <= 5000:
            _, normality_p = stats.shapiro(values)
        else:
            # Для больших выборок используем Anderson-Darling
            result = stats.anderson(values, dist='norm')
            normality_p = result.significance_level[result.statistic < result.critical_values][0]

        # Определяем тип распределения
        distribution_type = "unknown"

        if normality_p > 0.05:
            distribution_type = "normal"
        elif skew > 1:
            distribution_type = "right_skewed"
        elif skew < -1:
            distribution_type = "left_skewed"
        elif abs(kurt) > 1:
            distribution_type = "heavy_tailed" if kurt > 0 else "light_tailed"

        # Проверяем на бимодальность (используем kernel density estimation)
        try:
            kde = stats.gaussian_kde(values)
            x = np.linspace(values.min(), values.max(), 1000)
            density = kde(x)
            peaks = np.where((density[1:-1] > density[:-2]) & (density[1:-1] > density[2:]))[0] + 1
            modality = len(peaks)
        except:
            modality = 1

        if modality > 1:
            distribution_type = f"multimodal_{modality}"

        return HistogramAnalysisResult(
            distribution_type=distribution_type,
            skewness=float(skew),
            kurtosis=float(kurt),
            is_normal=normality_p > 0.05,
            normality_p_value=float(normality_p),
            mean=float(mean),
            median=float(median),
            std=float(std),
            iqr=float(iqr),
            outliers_count=int(len(outliers)),
            percentiles=percentiles,
            modality=int(modality)
        )


def generate_enhanced_histogram(
        data: EnhancedHistogramData,
        title_name: str,
        path_to_save: str,
        figsize: Tuple[int, int] = (14, 10)
) -> HistogramAnalysisResult:
    """
    Генерирует улучшенную гистограмму с анализом распределения.

    Args:
        data: Данные для гистограммы
        title_name: Заголовок
        path_to_save: Путь для сохранения
        figsize: Размер фигуры

    Returns:
        Результат анализа распределения
    """
    values = np.array(data.values)
    values = values[~np.isnan(values)]  # Удаляем NaN

    if len(values) == 0:
        raise ValueError("Нет валидных числовых данных")

    # Анализируем распределение
    analysis = analyze_distribution(values)

    # Создаем фигуру с несколькими панелями
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 2, height_ratios=[2, 1], width_ratios=[3, 1])

    # Основная гистограмма
    ax_main = fig.add_subplot(gs[0, 0])

    # Выбираем метод определения бинов
    bins_methods = {
        'auto': 'auto',
        'sturges': int(np.ceil(np.log2(len(values))) + 1),
        'fd': 'fd',
        'doane': 'doane',
        'scott': 'scott',
        'rice': int(np.ceil(2 * len(values) ** (1 / 3))),
        'sqrt': int(np.ceil(np.sqrt(len(values))))
    }

    bins = bins_methods.get(data.bins_method, 'auto')

    # Гистограмма
    n, bins, patches = ax_main.hist(
        values,
        bins=bins,
        density=data.show_density,
        alpha=0.7,
        color='skyblue',
        edgecolor='black',
        linewidth=1,
        label='Распределение данных'
    )

    # Выделяем выбросы
    if data.show_outliers and analysis.outliers_count > 0:
        lower_bound = analysis.percentiles['25%'] - 1.5 * analysis.iqr
        upper_bound = analysis.percentiles['75%'] + 1.5 * analysis.iqr

        for i, (bin_start, bin_end) in enumerate(zip(bins[:-1], bins[1:])):
            if bin_end < lower_bound or bin_start > upper_bound:
                patches[i].set_facecolor('red')
                patches[i].set_alpha(0.8)
                patches[i].set_edgecolor('darkred')

    # Kernel Density Estimation (KDE)
    if data.show_density:
        try:
            kde = stats.gaussian_kde(values)
            x_kde = np.linspace(values.min(), values.max(), 1000)
            y_kde = kde(x_kde)
            ax_main.plot(x_kde, y_kde, 'r-', linewidth=2, label='KDE (оценка плотности)')
        except:
            pass

    # Нормальное распределение для сравнения
    if data.compare_with_normal and analysis.is_normal:
        x_norm = np.linspace(values.min(), values.max(), 1000)
        y_norm = stats.norm.pdf(x_norm, analysis.mean, analysis.std)
        ax_main.plot(x_norm, y_norm, 'g--', linewidth=2,
                     label=f'Нормальное распределение (μ={analysis.mean:.1f}, σ={analysis.std:.1f})')

    # Линии статистик
    ax_main.axvline(analysis.mean, color='red', linestyle='-',
                    linewidth=2, alpha=0.7, label=f'Среднее: {analysis.mean:.1f}')
    ax_main.axvline(analysis.median, color='green', linestyle='--',
                    linewidth=2, alpha=0.7, label=f'Медиана: {analysis.median:.1f}')

    # Заполнение ±1σ
    ax_main.axvspan(analysis.mean - analysis.std, analysis.mean + analysis.std,
                    alpha=0.2, color='gray', label=f'±1σ ({analysis.std:.1f})')

    # Настройки
    value_label = f"{data.value_name} ({data.unit})" if data.unit else data.value_name
    ax_main.set_xlabel(value_label, fontsize=12)
    ax_main.set_ylabel('Плотность вероятности' if data.show_density else 'Частота', fontsize=12)
    ax_main.set_title(f"Распределение {data.value_name.lower()}\n"
                      f"n={len(values):,}", fontsize=14, fontweight='bold')
    ax_main.legend(fontsize=9, loc='upper right')
    ax_main.grid(True, alpha=0.3, linestyle='--')

    # Box plot для визуализации статистик
    ax_box = fig.add_subplot(gs[0, 1])
    bp = ax_box.boxplot(values, vert=True, patch_artist=True,
                        boxprops=dict(facecolor='lightblue', alpha=0.7),
                        medianprops=dict(color='green', linewidth=2),
                        whiskerprops=dict(color='black', linestyle='--'),
                        capprops=dict(color='black'),
                        flierprops=dict(marker='o', color='red', alpha=0.5, markersize=4))

    ax_box.set_ylabel(value_label, fontsize=10)
    ax_box.set_title('Box Plot', fontsize=12, fontweight='bold')
    ax_box.grid(True, alpha=0.3, axis='y')
    ax_box.set_xticks([])

    # QQ-plot (тест на нормальность)
    ax_qq = fig.add_subplot(gs[1, 0])

    if len(values) > 1:
        stats.probplot(values, dist="norm", plot=ax_qq)
        ax_qq.get_lines()[0].set_marker('o')
        ax_qq.get_lines()[0].set_markersize(4)
        ax_qq.get_lines()[0].set_alpha(0.6)
        ax_qq.get_lines()[1].set_color('red')
        ax_qq.get_lines()[1].set_linewidth(2)

        normality_text = f"Тест на нормальность: "
        if analysis.is_normal:
            normality_text += f"НОРМАЛЬНОЕ (p={analysis.normality_p_value:.3f})"
        else:
            normality_text += f"НЕ НОРМАЛЬНОЕ (p={analysis.normality_p_value:.3f})"

        ax_qq.set_title(f"Q-Q Plot\n{normality_text}", fontsize=12)
        ax_qq.grid(True, alpha=0.3)
    else:
        ax_qq.text(0.5, 0.5, "Недостаточно данных\nдля Q-Q plot",
                   ha='center', va='center', transform=ax_qq.transAxes)
        ax_qq.axis('off')

    # Панель с детальной статистикой
    ax_stats = fig.add_subplot(gs[1, 1])
    ax_stats.axis('off')

    # Формируем текст статистики
    stats_text = f"""СТАТИСТИЧЕСКИЙ АНАЛИЗ:

Распределение: {analysis.distribution_type.upper()}
Модальность: {analysis.modality} пик(а)

Меры центра:
  Среднее: {analysis.mean:.2f}
  Медиана: {analysis.median:.2f}
  Мода(ы): {stats.mode(values, keepdims=True)[0][0]:.2f}

Меры разброса:
  Ст. отклонение: {analysis.std:.2f}
  Дисперсия: {analysis.std ** 2:.2f}
  IQR: {analysis.iqr:.2f}
  Размах: {values.max() - values.min():.2f}

Форма распределения:
  Асимметрия: {analysis.skewness:.2f}
  Эксцесс: {analysis.kurtosis:.2f}

Процентили:
  1%: {analysis.percentiles['1%']:.1f}
  25%: {analysis.percentiles['25%']:.1f}
  50%: {analysis.percentiles['50%']:.1f}
  75%: {analysis.percentiles['75%']:.1f}
  99%: {analysis.percentiles['99%']:.1f}

Выбросы: {analysis.outliers_count} ({analysis.outliers_count / len(values) * 100:.1f}%)

Тест на нормальность:
  p-value: {analysis.normality_p_value:.3f}
  Нормальное: {'ДА' if analysis.is_normal else 'НЕТ'}"""

    ax_stats.text(0, 1, stats_text,
                  transform=ax_stats.transAxes,
                  verticalalignment='top',
                  fontsize=9,
                  bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    # Общий заголовок
    fig.suptitle(title_name, fontsize=16, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Улучшенная гистограмма сохранена: {path_to_save}")
    print(f"   Анализ: {analysis.distribution_type}, n={len(values)}")

    return analysis


def generate_grouped_histogram(
        data: GroupedHistogramData,
        title_name: str,
        path_to_save: str,
        figsize: Tuple[int, int] = (16, 12)
) -> None:
    """
    Генерирует группированную гистограмму для сравнения распределений.

    Args:
        data: Данные с группами
        title_name: Заголовок
        path_to_save: Путь для сохранения
        figsize: Размер фигуры
    """
    groups = data.groups
    group_names = data.group_names if data.group_names else list(groups.keys())

    # Проверяем данные и преобразуем в numpy массивы
    valid_groups = {}
    for name in group_names:
        if name in groups:
            values = groups[name]
            if isinstance(values, list):
                values = np.array(values)
                values = values[~np.isnan(values)]
                if len(values) > 0:
                    valid_groups[name] = values

    if not valid_groups:
        raise ValueError("Нет валидных данных в группах")

    n_groups = len(valid_groups)

    # Создаем фигуру
    if data.show_violin:
        # Violin plot
        fig, (ax_violin, ax_box) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1] * 0.8),
                                                gridspec_kw={'height_ratios': [3, 1]})

        # Violin plot
        violin_parts = ax_violin.violinplot(
            [valid_groups[name] for name in group_names if name in valid_groups],
            showmeans=True,
            showmedians=True,
            showextrema=True
        )

        # Настраиваем цвета
        cmap = plt.cm.Set3
        for i, pc in enumerate(violin_parts['bodies']):
            pc.set_facecolor(cmap(i / max(1, n_groups - 1)))
            pc.set_alpha(0.7)
            pc.set_edgecolor('black')

        ax_violin.set_xticks(range(1, n_groups + 1))
        ax_violin.set_xticklabels([name for name in group_names if name in valid_groups],
                                  rotation=45, ha='right')
        ax_violin.set_ylabel(data.value_name, fontsize=12)
        ax_violin.set_title(f"Violin Plot: {title_name}", fontsize=14, fontweight='bold')
        ax_violin.grid(True, alpha=0.3, axis='y')

        # Box plot под violin plot
        ax_box.boxplot([valid_groups[name] for name in group_names if name in valid_groups],
                       vert=True)
        ax_box.set_xticks(range(1, n_groups + 1))
        ax_box.set_xticklabels([])
        ax_box.set_ylabel(data.value_name, fontsize=10)
        ax_box.grid(True, alpha=0.3, axis='y')

    else:
        # Группированные гистограммы
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.flatten()

        # 1. Наложенные гистограммы
        ax1 = axes[0]
        colors = plt.cm.tab10(np.linspace(0, 1, n_groups))

        # Определяем общие бины для всех групп для сравнения
        all_values = np.concatenate(list(valid_groups.values()))
        bin_edges = np.histogram_bin_edges(all_values, bins='auto')

        for i, (name, values) in enumerate(valid_groups.items()):
            if data.normalize:
                # Для нормализованных данных используем density=True вместо weights
                density = True
                weights = None
            else:
                density = False
                weights = None

            ax1.hist(values, bins=bin_edges, alpha=0.6,
                     color=colors[i], edgecolor='black',
                     label=name, density=density,
                     weights=weights)

        ax1.set_xlabel(data.value_name, fontsize=12)
        ax1.set_ylabel('Плотность' if data.normalize else 'Частота', fontsize=12)
        ax1.set_title('Наложенные распределения', fontsize=13, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)

        # 2. KDE для каждой группы
        ax2 = axes[1]

        for i, (name, values) in enumerate(valid_groups.items()):
            try:
                kde = stats.gaussian_kde(values)
                x_kde = np.linspace(values.min(), values.max(), 1000)
                y_kde = kde(x_kde)
                ax2.plot(x_kde, y_kde, color=colors[i], linewidth=2, label=name)
            except Exception as e:
                print(f"Ошибка KDE для группы {name}: {e}")
                # Если KDE не работает, рисуем гистограмму с плотностью
                ax2.hist(values, bins=bin_edges, alpha=0.3,
                         color=colors[i], density=True,
                         label=name + " (hist)")

        ax2.set_xlabel(data.value_name, fontsize=12)
        ax2.set_ylabel('Плотность вероятности', fontsize=12)
        ax2.set_title('KDE (оценка плотности)', fontsize=13, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)

        # 3. Box plot сравнение
        ax3 = axes[2]

        box_data = [valid_groups[name] for name in group_names if name in valid_groups]
        bp = ax3.boxplot(box_data, patch_artist=True,
                         labels=[name for name in group_names if name in valid_groups])

        # Раскрашиваем box plots
        for i, box in enumerate(bp['boxes']):
            box.set_facecolor(colors[i])
            box.set_alpha(0.7)

        ax3.set_ylabel(data.value_name, fontsize=12)
        ax3.set_title('Сравнение групп (Box Plot)', fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.tick_params(axis='x', rotation=45)

        # 4. Статистика сравнения
        ax4 = axes[3]
        ax4.axis('off')

        # Сравниваем статистики
        stats_comparison = []
        for name in group_names:
            if name in valid_groups:
                values = valid_groups[name]
                stats_comparison.append({
                    'Группа': name,
                    'n': len(values),
                    'Среднее': np.mean(values),
                    'Медиана': np.median(values),
                    'Ст. отклонение': np.std(values),
                    'IQR': np.percentile(values, 75) - np.percentile(values, 25)
                })

        # Создаем таблицу
        if stats_comparison:
            df_stats = pd.DataFrame(stats_comparison)
            table_text = "СРАВНЕНИЕ СТАТИСТИК:\n\n"

            for _, row in df_stats.iterrows():
                table_text += f"{row['Группа']} (n={row['n']}):\n"
                table_text += f"  Среднее: {row['Среднее']:.2f}\n"
                table_text += f"  Медиана: {row['Медиана']:.2f}\n"
                table_text += f"  Ст. откл.: {row['Ст. отклонение']:.2f}\n"
                table_text += f"  IQR: {row['IQR']:.2f}\n\n"

            ax4.text(0, 1, table_text,
                     transform=ax4.transAxes,
                     verticalalignment='top',
                     fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

        # Тест ANOVA (если группы > 1)
        if n_groups >= 2:
            try:
                anova_result = stats.f_oneway(*[valid_groups[name] for name in valid_groups.keys()])
                anova_text = f"\n\nANOVA тест:\nF={anova_result.statistic:.3f}\np={anova_result.pvalue:.3f}"

                if anova_result.pvalue < 0.05:
                    anova_text += "\nЕсть статистически значимые различия между группами"
                else:
                    anova_text += "\nНет значимых различий между группами"

                ax4.text(0, -0.1, anova_text,
                         transform=ax4.transAxes,
                         fontsize=9,
                         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
            except Exception as e:
                print(f"Ошибка ANOVA теста: {e}")

    fig.suptitle(title_name, fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Группированная гистограмма сохранена: {path_to_save}")
    print(f"   Группы: {list(valid_groups.keys())}")


def generate_histogram(
        data: AbstractGameBy_,
        title_name: str,
        path_to_save: str,
        histogram_type: str = "auto",
        **kwargs
) -> Any:
    """
    Умная функция для генерации гистограммы.
    Определяет тип данных и выбирает подходящую визуализацию.

    Args:
        data: Данные для визуализации
        title_name: Заголовок
        path_to_save: Путь для сохранения
        histogram_type: "auto", "enhanced", "grouped"
        **kwargs: Дополнительные параметры

    Returns:
        Результат анализа (для enhanced гистограммы)
    """
    if histogram_type == "auto":
        # Автоматическое определение типа
        if hasattr(data, 'groups'):
            histogram_type = "grouped"
        elif hasattr(data, 'values'):
            if isinstance(data.values, dict):
                # Проверяем, являются ли значения списками
                first_value = next(iter(data.values.values())) if data.values else None
                if isinstance(first_value, list):
                    histogram_type = "grouped"
                else:
                    histogram_type = "enhanced"
            elif isinstance(data.values, list):
                histogram_type = "enhanced"
            else:
                histogram_type = "enhanced"
        else:
            histogram_type = "enhanced"

    if histogram_type == "enhanced":
        # Проверяем и преобразуем данные
        if hasattr(data, 'values'):
            if isinstance(data.values, list):
                values = data.values
            elif isinstance(data.values, dict):
                # Берем значения из словаря
                values = list(data.values.values())
            else:
                values = []
        else:
            # Пытаемся извлечь значения через data_prep
            try:
                _, values_list = data_prep(data)
                values = values_list
            except:
                values = []

        # Фильтруем NaN значения
        values = [v for v in values if not np.isnan(v)]

        if len(values) == 0:
            raise ValueError("Нет числовых данных для построения гистограммы")

        # Создаем объект EnhancedHistogramData
        enhanced_data = EnhancedHistogramData(
            values=values,
            value_name=kwargs.get('value_name', title_name),
            unit=kwargs.get('unit', ''),
            bins_method=kwargs.get('bins_method', 'auto'),
            show_density=kwargs.get('show_density', True),
            show_stats=kwargs.get('show_stats', True),
            show_outliers=kwargs.get('show_outliers', True),
            compare_with_normal=kwargs.get('compare_with_normal', True),
            log_scale=kwargs.get('log_scale', False),
            ticks=[]
        )

        return generate_enhanced_histogram(enhanced_data, title_name, path_to_save, **kwargs)

    elif histogram_type == "grouped":
        # Создаем объект GroupedHistogramData из данных
        if hasattr(data, 'groups'):
            # Если уже есть groups, используем как есть
            grouped_data = data
        elif hasattr(data, 'values') and isinstance(data.values, dict):
            # Преобразуем dict в GroupedHistogramData
            groups = {}
            for key, value in data.values.items():
                if isinstance(value, list):
                    groups[key] = value
                elif isinstance(value, (int, float)):
                    groups[key] = [value]  # Преобразуем единичное значение в список
                else:
                    groups[key] = []

            grouped_data = GroupedHistogramData(
                groups=groups,
                group_names=data.ticks if hasattr(data, 'ticks') else list(groups.keys()),
                value_name=kwargs.get('value_name', 'Значение'),
                show_kde=kwargs.get('show_kde', True),
                show_violin=kwargs.get('show_violin', False),
                normalize=kwargs.get('normalize', False)
            )
        else:
            raise ValueError("Невозможно создать grouped гистограмму из данных")

        return generate_grouped_histogram(grouped_data, title_name, path_to_save, **kwargs)

    else:
        raise ValueError(f"Неизвестный тип гистограммы: {histogram_type}")


def main():
    pdp = ProcessedDataProvider()
    distribution = pdp.get_games_by_types()

    # print(distribution)
    # distribution = pdp.get_games_by_genres()
    # distribution = pdp.get_games_by_categories()
    # distribution = pdp.get_games_by_categories_count()

    # generate_distribution_by_feature(distribution, "title_name", "res/test.png", 20)
    # generate_pie_by_feature(distribution, "title_name", "res/pie_test.png", 15, 3)
    # generate_detailed_pie_by_feature(distribution, "title_name", "res/pie_detail_test.png", sections_num=8, inner_sections=2)

    # generate_line_plot(distribution, "title_name", "res/line_plot_test.png")

    # generate_heatmap(distribution, "title_name", "res/heatmap_test.png")

    # generate_histogram(distribution, "title_name", "res/hist_test.png")

    # generate_scatter_clusters(
    #     data=distribution,
    #     title_name="title_name",
    #     path_to_save="res/cluster_test.png",
    #     max_clusters=10
    # )

    # generate_treemap(
    #     data=distribution,
    #     title_name="title_name",
    #     path_to_save="res/bubble_test.png"
    # )

def main_clust():
    # Пример 1: Heatmap корреляций между признаками игр
    # (после кластеризации или анализа)
    correlation_data = CorrelationHeatmapData(
        correlation_matrix=[[1.0, 0.3, -0.1, 0.7],
                            [0.3, 1.0, 0.5, 0.2],
                            [-0.1, 0.5, 1.0, 0.4],
                            [0.7, 0.2, 0.4, 1.0]],
        feature_names=["Цена", "Рейтинг", "Время игры", "Количество отзывов"],
        values={}, ticks=[]
    )

    generate_heatmap(
        data=correlation_data,
        title_name="Корреляции между признаками игр",
        path_to_save="res/correlations.png",
        heatmap_type="correlation"
    )

    # Пример 2: 2D плотность (цена vs рейтинг)
    density_data = TwoDHistogramData(
        x_values=[10, 20, 30, 40, 50, 15, 25, 35, 45],  # Цены
        y_values=[0.7, 0.8, 0.9, 0.6, 0.85, 0.75, 0.95, 0.65, 0.88],  # Рейтинги
        x_bins=5,
        y_bins=5,
        x_label="Цена ($)",
        y_label="Рейтинг",
        values={}, ticks=[]
    )

    generate_heatmap(
        data=density_data,
        title_name="Распределение игр по цене и рейтингу",
        path_to_save="res/price_vs_rating.png",
        heatmap_type="2d_density"
    )

    # Пример 3: Временной ряд (релизы по годам и месяцам)
    # Предполагая, что у вас есть схема GamesReleaseBySeason
    release_data = GamesReleaseBySeason(
        values={"2020-Q1": 150, "2020-Q2": 200, "2020-Q3": 180, "2020-Q4": 220,
                "2021-Q1": 170, "2021-Q2": 210, "2021-Q3": 190, "2021-Q4": 230},
        ticks=["2020-Q1", "2020-Q2", "2020-Q3", "2020-Q4",
               "2021-Q1", "2021-Q2", "2021-Q3", "2021-Q4"]
    )

    generate_heatmap(
        data=release_data,
        title_name="Релизы игр по кварталам",
        path_to_save="res/releases_heatmap.png",
        heatmap_type="time_series",
        time_period="year-quarter"
    )

def main_hist():
    # Тест 1: Enhanced гистограмма с простыми данными
    print("\n1. Тест enhanced гистограммы:")

    simple_data = EnhancedHistogramData(
        values=[10, 20, 15, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],
        value_name="Время игры",
        unit="часы"
    )

    try:
        result = generate_histogram(
            data=simple_data,
            title_name="Тест: Распределение времени игры",
            path_to_save="res/test_enhanced_hist.png",
            histogram_type="enhanced"
        )
        print(f"✓ Enhanced гистограмма создана")
        print(f"  Тип распределения: {result.distribution_type}")
        print(f"  Среднее: {result.mean:.2f}")
    except Exception as e:
        print(f"✗ Ошибка: {e}")

    # Тест 2: Grouped гистограмма
    print("\n2. Тест grouped гистограммы:")

    grouped_data = GroupedHistogramData(
        groups={
            "Action": [10, 20, 15, 25, 30, 35, 40],
            "RPG": [50, 60, 55, 65, 70, 75, 80],
            "Strategy": [25, 30, 35, 40, 45, 50, 55],
            "Simulation": [15, 20, 25, 30, 35, 40, 45]
        },
        group_names=["Action", "RPG", "Strategy", "Simulation"],
        value_name="Среднее время игры (часы)",
        normalize=True
    )

    try:
        generate_histogram(
            data=grouped_data,
            title_name="Тест: Сравнение времени игры по жанрам",
            path_to_save="res/test_grouped_hist.png",
            histogram_type="grouped"
        )
        print(f"✓ Grouped гистограмма создана")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Тест 3: Автоматическое определение типа
    print("\n3. Тест автоматического определения типа:")

    # Данные в формате AbstractGameBy_ (словарь значений)
    abstract_data = type('TestData', (), {
        'values': {
            'Action': [10, 20, 15, 25, 30],
            'RPG': [50, 60, 55, 65, 70],
            'Strategy': [25, 30, 35, 40, 45]
        },
        'ticks': ['Action', 'RPG', 'Strategy']
    })()

    try:
        generate_histogram(
            data=abstract_data,
            title_name="Тест: Автоматическое определение",
            path_to_save="res/test_auto_hist.png"
        )
        print(f"✓ Автоматическое определение сработало")
    except Exception as e:
        print(f"✗ Ошибка: {e}")


# main()
# main_clust()
main_hist()




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
