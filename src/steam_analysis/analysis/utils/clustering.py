from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from scipy.ndimage import gaussian_filter1d


from steam_analysis.proccessors.schemas.games import (AbstractGameBy_, GamesClusteringData,
                                                      TwoDHistogramData, GamesReleaseBySeason,
                                                      EnhancedHistogramData,
                                                      GameFeatureVector)
from steam_analysis.analysis.response_schemas.clustering import ClusteringResult, ClusterInfo
from steam_analysis.analysis.response_schemas.graphics import CorrelationHeatmapData, GroupedHistogramData, HistogramAnalysisResult




class KMeansParamAnalyzer:
    """Класс для анализа параметров KMeans"""

    @staticmethod
    def calculate_metrics(X_scaled: np.ndarray, n_clusters: int) -> Dict[str, Any]:
        """Вычисляет метрики качества для KMeans с заданным количеством кластеров"""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        results = {
            'wcss': kmeans.inertia_,
            'labels': labels,
            'n_unique_clusters': len(np.unique(labels))
        }

        # Вычисляем дополнительные метрики только если есть более одного кластера
        if results['n_unique_clusters'] > 1:
            results['silhouette'] = silhouette_score(X_scaled, labels)
            results['davies_bouldin'] = davies_bouldin_score(X_scaled, labels)
            results['calinski_harabasz'] = calinski_harabasz_score(X_scaled, labels)
        else:
            results['silhouette'] = 0
            results['davies_bouldin'] = float('inf')
            results['calinski_harabasz'] = 0

        return results

    @staticmethod
    def analyze_optimal_clusters(
            wcss: List[float],
            silhouette_scores: List[float],
            db_scores: List[float],
            ch_scores: List[float],
            cluster_range: range
    ) -> Dict[str, Any]:
        """Анализирует метрики и определяет оптимальное количество кластеров"""
        # Метод локтя (Elbow Method)
        wcss_np = np.array(wcss)
        if len(wcss_np) > 2:
            second_deriv = np.diff(np.diff(wcss_np))
            elbow_idx = np.argmax(np.abs(second_deriv)) + 2 if len(second_deriv) > 0 else 2
        else:
            elbow_idx = 2

        # Силуэтный анализ (максимум)
        silhouette_idx = np.argmax(silhouette_scores) if len(silhouette_scores) > 0 else 0

        # Davies-Bouldin (минимум)
        db_idx = np.argmin(db_scores) if len(db_scores) > 0 else 0

        # Calinski-Harabasz (максимум)
        ch_idx = np.argmax(ch_scores) if len(ch_scores) > 0 else 0

        # Собираем кандидатов
        candidates = [
            cluster_range[elbow_idx - 2] if elbow_idx - 2 < len(cluster_range) else 3,
            cluster_range[silhouette_idx],
            cluster_range[db_idx],
            cluster_range[ch_idx]
        ]

        # Вычисляем оптимальное значение как медиану
        optimal_n = int(np.median(candidates))
        optimal_n = max(2, min(optimal_n, cluster_range[-1]))

        return {
            'elbow': cluster_range[elbow_idx - 2] if elbow_idx - 2 < len(cluster_range) else 3,
            'silhouette': cluster_range[silhouette_idx],
            'davies_bouldin': cluster_range[db_idx],
            'calinski_harabasz': cluster_range[ch_idx],
            'optimal': optimal_n,
            'candidates': candidates
        }


class DBSCANParamAnalyzer:
    """Класс для анализа параметров DBSCAN"""

    @staticmethod
    def _ensure_int_range(min_samples_range: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Преобразует диапазон min_samples в целые числа"""
        return (int(min_samples_range[0]), int(min_samples_range[1]), int(min_samples_range[2]))

    @staticmethod
    def _calculate_k_distance(X_scaled: np.ndarray, min_samples: int) -> Tuple[np.ndarray, float]:
        """Рассчитывает k-distance и рекомендованное eps"""
        nbrs = NearestNeighbors(n_neighbors=min_samples).fit(X_scaled)
        distances, _ = nbrs.kneighbors(X_scaled)
        k_distances = np.sort(distances[:, min_samples - 1])

        # Рекомендация eps через анализ второй производной
        y = k_distances
        y_smooth = gaussian_filter1d(y, sigma=3)
        first_deriv = np.gradient(y_smooth)
        second_deriv = np.gradient(first_deriv)

        if len(second_deriv) > 10:
            knee_idx = np.argmax(second_deriv[10:-10]) + 10
            eps_from_knee = y_smooth[knee_idx]
        else:
            eps_from_knee = np.percentile(k_distances, 90)

        return k_distances, eps_from_knee

    @staticmethod
    def _evaluate_dbscan_params(X_scaled: np.ndarray, eps: float, min_samples: int) -> Dict[str, Any]:
        """Оценивает параметры DBSCAN для одной комбинации"""
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(X_scaled)
        n_clusters = len(np.unique(labels[labels != -1]))
        noise_ratio = np.sum(labels == -1) / len(labels) if len(labels) > 0 else 1.0

        silhouette = -1
        if n_clusters > 1 and n_clusters < len(labels) // 2:
            try:
                non_noise_mask = labels != -1
                if np.sum(non_noise_mask) > 10:
                    silhouette = silhouette_score(X_scaled[non_noise_mask], labels[non_noise_mask])
            except:
                silhouette = -1

        return {
            'eps': eps,
            'min_samples': int(min_samples),
            'n_clusters': n_clusters,
            'noise_ratio': noise_ratio,
            'silhouette': silhouette
        }


def find_optimal_clusters_kmeans(
        X_scaled: np.ndarray,
        max_clusters: int = 15
) -> int:
    """Находит оптимальное количество кластеров для KMeans"""

    print("  Вычисление метрик для диапазона кластеров...")
    print(f"  Перебираем K от 2 до {max_clusters}")

    cluster_range = range(2, max_clusters + 1)
    wcss = []
    silhouette_scores = []
    db_scores = []
    ch_scores = []

    for idx, n in enumerate(cluster_range, 1):
        print(f"    [{idx}/{len(cluster_range)}] Обработка K={n}...", end="", flush=True)

        # Вычисляем метрики для текущего количества кластеров
        metrics = KMeansParamAnalyzer.calculate_metrics(X_scaled, n)

        wcss.append(metrics['wcss'])
        silhouette_scores.append(metrics['silhouette'])
        db_scores.append(metrics['davies_bouldin'])
        ch_scores.append(metrics['calinski_harabasz'])

        print(f" OK - WCSS={metrics['wcss']:.1f}, Silhouette={metrics['silhouette']:.3f}, "
              f"DB={metrics['davies_bouldin']:.3f}, CH={metrics['calinski_harabasz']:.0f}")

    print("\n  Анализ результатов...")

    # Анализируем метрики для определения оптимального количества кластеров
    analysis = KMeansParamAnalyzer.analyze_optimal_clusters(
        wcss, silhouette_scores, db_scores, ch_scores, cluster_range
    )

    print(f"\n  Результаты подбора:")
    print(f"    Метод локтя: K={analysis['elbow']}")
    print(f"    Силуэтный анализ: K={analysis['silhouette']}")
    print(f"    Davies-Bouldin: K={analysis['davies_bouldin']}")
    print(f"    Calinski-Harabasz: K={analysis['calinski_harabasz']}")
    print(f"  Рекомендуемое количество кластеров: {analysis['optimal']} (медиана всех методов)")

    return analysis['optimal']


def plot_cluster_selection_metrics(
        X_scaled: np.ndarray,
        max_clusters: int = 15,
        ax: Optional[plt.Axes] = None,
        save_path: Optional[str] = None
) -> plt.Axes:
    """Строит график метрик для выбора количества кластеров"""

    print("  Построение графика выбора количества кластеров...")

    # Создаем фигуру, если ax не предоставлен
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure if hasattr(ax, 'figure') else plt.gcf()

    # Вычисляем метрики для диапазона кластеров
    cluster_range = range(2, max_clusters + 1)
    wcss = []
    silhouette_scores = []
    db_scores = []
    ch_scores = []

    for idx, n in enumerate(cluster_range, 1):
        print(f"    [{idx}/{len(cluster_range)}] Подсчет метрик для K={n}...", end="", flush=True)

        metrics = KMeansParamAnalyzer.calculate_metrics(X_scaled, n)

        wcss.append(metrics['wcss'])
        silhouette_scores.append(metrics['silhouette'])
        db_scores.append(metrics['davies_bouldin'])
        ch_scores.append(metrics['calinski_harabasz'])

        print(" OK")

    # Нормализуем Davies-Bouldin для лучшего отображения (инвертируем, т.к. меньше=лучше)
    db_scores_norm = 1 / (np.array(db_scores) + 1e-10)

    # Построение графиков
    line1 = ax.plot(cluster_range, wcss, 'bo-', linewidth=2, markersize=8, label='WCSS')
    ax.set_xlabel('Количество кластеров', fontsize=12)
    ax.set_ylabel('WCSS (Within-Cluster Sum of Squares)', color='b', fontsize=12)
    ax.tick_params(axis='y', labelcolor='b')
    ax.grid(True, alpha=0.3)

    # Вторная ось Y для силуэтного коэффициента
    ax2 = ax.twinx()
    line2 = ax2.plot(cluster_range, silhouette_scores, 'ro--', linewidth=2,
                     markersize=8, label='Силуэтный коэффициент')
    ax2.set_ylabel('Силуэтный коэффициент', color='r', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='r')

    # Третья ось Y для нормализованного Davies-Bouldin
    ax3 = ax.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    line3 = ax3.plot(cluster_range, db_scores_norm, 'g^:', linewidth=2,
                     markersize=8, label='Davies-Bouldin (норм.)')
    ax3.set_ylabel('Davies-Bouldin (норм.)', color='g', fontsize=12)
    ax3.tick_params(axis='y', labelcolor='g')

    # Находим оптимальные точки по разным метрикам
    analysis = KMeansParamAnalyzer.analyze_optimal_clusters(
        wcss, silhouette_scores, db_scores, ch_scores, cluster_range
    )

    # Добавляем вертикальные линии для оптимальных значений
    ax.axvline(x=analysis['elbow'], color='b', linestyle='--', alpha=0.5,
               label=f'Метод локтя: K={analysis["elbow"]}')
    ax2.axvline(x=analysis['silhouette'], color='r', linestyle='--', alpha=0.5,
                label=f'Силуэт: K={analysis["silhouette"]}')

    # Для Davies-Bouldin находим минимум в оригинальных значениях
    db_min_idx = np.argmin(db_scores)
    ax3.axvline(x=cluster_range[db_min_idx], color='g', linestyle='--', alpha=0.5,
                label=f'DB: K={cluster_range[db_min_idx]}')

    # Настройка заголовка и легенды
    ax.set_title('Выбор оптимального количества кластеров', fontsize=14, fontweight='bold')

    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='upper right', fontsize=9)

    # Сохранение графика
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  График сохранен: {save_path}")
        plt.close(fig)

    return ax


def find_optimal_dbscan_params(
        X_scaled: np.ndarray,
        eps_range: Tuple[float, float, float] = (0.1, 2.0, 0.5),
        min_samples_range: Tuple[float, float, float] = (5, 50, 15)
) -> Tuple[float, int]:
    """Находит оптимальные параметры для DBSCAN"""

    print("  Поиск оптимальных параметров DBSCAN...")
    print(f"  Диапазон eps: от {eps_range[0]} до {eps_range[1]} с шагом {eps_range[2]}")
    print(f"  Диапазон min_samples: от {min_samples_range[0]} до {min_samples_range[1]} с шагом {min_samples_range[2]}")

    # Преобразование диапазонов
    min_samples_range_int = DBSCANParamAnalyzer._ensure_int_range(min_samples_range)
    eps_values = np.arange(eps_range[0], eps_range[1], eps_range[2])
    min_samples_values = range(min_samples_range_int[0], min_samples_range_int[1], min_samples_range_int[2])

    # Анализ k-distance графика
    median_min_samples = int(np.median(min_samples_range_int))
    print(f"  Анализ k-distance графика с min_samples={median_min_samples}...")

    k_distances, eps_from_knee = DBSCANParamAnalyzer._calculate_k_distance(X_scaled, median_min_samples)
    print(f"  Рекомендуемое eps из k-distance: {eps_from_knee:.2f}")

    # Перебор комбинаций параметров
    results = []
    total_combinations = len(eps_values) * len(min_samples_values)
    current_combination = 0

    print(f"  Перебор {total_combinations} комбинаций параметров...")

    for eps in eps_values:
        for min_samples in min_samples_values:
            current_combination += 1
            print(f"    [{current_combination}/{total_combinations}] eps={eps:.2f}, min_samples={min_samples}...",
                  end="", flush=True)

            result = DBSCANParamAnalyzer._evaluate_dbscan_params(X_scaled, eps, min_samples)
            results.append(result)

            print(f" кластеров={result['n_clusters']}, шум={result['noise_ratio']:.1%}, "
                  f"силуэт={result['silhouette']:.3f}")

    # Анализ результатов
    df_results = pd.DataFrame(results)
    df_filtered = df_results[
        (df_results['n_clusters'] >= 2) &
        (df_results['n_clusters'] <= 10) &
        (df_results['noise_ratio'] < 0.3)
        ]

    if len(df_filtered) > 0:
        best_row = df_filtered.loc[df_filtered['silhouette'].idxmax()]
        optimal_eps = float(best_row['eps'])
        optimal_min_samples = int(best_row['min_samples'])

        print(f"  Найдено {len(df_filtered)} хороших комбинаций параметров")
        print(f"  Лучшие: eps={optimal_eps:.2f}, min_samples={optimal_min_samples}")
        print(f"  -> Кластеров: {best_row['n_clusters']}, "
              f"Шум: {best_row['noise_ratio']:.1%}, "
              f"Силуэт: {best_row['silhouette']:.3f}")
    else:
        optimal_eps = float(eps_from_knee)
        optimal_min_samples = median_min_samples
        print(f"  Не найдено идеальных параметров, используем eps={optimal_eps:.2f} из k-distance")

    return optimal_eps, optimal_min_samples


def plot_dbscan_param_analysis(
        X_scaled: np.ndarray,
        ax: Optional[plt.Axes] = None,
        eps_range: Tuple[float, float, float] = (0.1, 2.0, 0.5),
        min_samples_range: Tuple[float, float, float] = (5, 50, 15),
        save_path: Optional[str] = None
) -> plt.Axes:
    """Строит графики анализа параметров DBSCAN"""

    print("  Построение графиков анализа параметров DBSCAN...")

    # Создание фигуры
    if ax is None:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        ax = axes
    else:
        fig = ax[0].figure if hasattr(ax, 'figure') else plt.gcf()

    # Преобразование диапазона min_samples
    min_samples_range_int = DBSCANParamAnalyzer._ensure_int_range(min_samples_range)
    median_min_samples = int(np.median(min_samples_range_int))

    # График 1: K-distance
    k_distances, eps_from_knee = DBSCANParamAnalyzer._calculate_k_distance(X_scaled, median_min_samples)
    eps_recommended = np.percentile(k_distances, 95)

    ax[0].plot(k_distances, linewidth=2)
    ax[0].set_xlabel('Точки (отсортированные)', fontsize=12)
    ax[0].set_ylabel(f'Расстояние до {median_min_samples}-го соседа', fontsize=12)
    ax[0].set_title('График k-distance для выбора eps', fontsize=13, fontweight='bold')
    ax[0].grid(True, alpha=0.3)
    ax[0].axhline(y=eps_recommended, color='r', linestyle='--',
                  label=f'Рекомендуемое eps: {eps_recommended:.2f}')
    ax[0].legend()

    # График 2: Влияние eps
    eps_values = np.arange(eps_range[0], eps_range[1], eps_range[2])
    n_clusters_list = []
    noise_ratios = []

    print(f"  Анализ влияния eps (min_samples={median_min_samples})...")

    for idx, eps in enumerate(eps_values, 1):
        print(f"    [{idx}/{len(eps_values)}] eps={eps:.2f}...", end="", flush=True)

        result = DBSCANParamAnalyzer._evaluate_dbscan_params(X_scaled, eps, median_min_samples)
        n_clusters_list.append(result['n_clusters'])
        noise_ratios.append(result['noise_ratio'])

        print(f" кластеров={result['n_clusters']}, шум={result['noise_ratio']:.1%}")

    ax2 = ax[1].twinx()
    line1 = ax[1].plot(eps_values, n_clusters_list, 'bo-', linewidth=2,
                       markersize=6, label='Количество кластеров')
    ax[1].set_xlabel('Параметр eps', fontsize=12)
    ax[1].set_ylabel('Количество кластеров', color='b', fontsize=12)
    ax[1].tick_params(axis='y', labelcolor='b')

    line2 = ax2.plot(eps_values, noise_ratios, 'ro--', linewidth=2,
                     markersize=6, label='Процент шума')
    ax2.set_ylabel('Процент шума', color='r', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.set_ylim([0, 1])

    ax[1].set_title(f'Влияние eps при min_samples={median_min_samples}',
                    fontsize=13, fontweight='bold')
    ax[1].grid(True, alpha=0.3)

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax[1].legend(lines, labels, loc='upper right')

    # Сохранение графика
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  График сохранен: {save_path}")
        plt.close(fig)

    return ax


def perform_games_clustering(
        data: GamesClusteringData,
        title_name: str,
        path_to_save: str,
        method: str = "kmeans",
        n_clusters: int = 5,
        features_to_show: Optional[List[str]] = None,
        auto_select_params: bool = False,
        max_clusters: int = 15,
        eps_range: Tuple[float, float, float] = (0.1, 2.0, 0.5),
        min_samples_range: Tuple[float, float, float] = (5, 50, 15),
        eps: float = 1.0,
        min_samples: int = 45,
) -> ClusteringResult:
    """Основная функция кластеризации игр"""

    print("=" * 80)
    print(f"🚀 ЗАПУСК КЛАСТЕРИЗАЦИИ: {title_name}")
    print(f"   Метод: {method}")
    print(f"   Игр: {len(data.games)}")
    print(f"   Признаков: {len(data.feature_names)}")
    print("=" * 80)

    # Проверка данных
    if not data.feature_matrix:
        raise ValueError("Нет матрицы признаков для кластеризации")

    X = np.array(data.feature_matrix)

    # Масштабирование
    print("📊 Масштабирование данных...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("   ✓ Данные масштабированы")

    # Автоматический подбор параметров
    clusterer = None
    cluster_labels = None

    if auto_select_params:
        clusterer, cluster_labels, n_clusters = _auto_select_clustering_params(
            X_scaled, method, max_clusters, eps_range, min_samples_range, path_to_save
        )
    else:
        print(f"\n🎯 ПРИМЕНЕНИЕ КЛАСТЕРИЗАЦИИ...")
        print(f"   Количество кластеров: {n_clusters}")

        clusterer, cluster_labels = _apply_clustering(
            X_scaled, method, n_clusters, eps, min_samples
        )

    # Обработка шумовых точек (для DBSCAN)
    cluster_labels = _handle_noise_points(cluster_labels)

    # Снижение размерности
    print("\n📉 СНИЖЕНИЕ РАЗМЕРНОСТИ (PCA)...")
    X_reduced = _apply_pca(X_scaled)

    # Анализ кластеров
    print(f"\n📊 АНАЛИЗ КЛАСТЕРОВ...")
    clusters_info = _analyze_clusters(
        X, X_scaled, cluster_labels, data, clusterer, method
    )

    # Построение графиков
    print("\n🎨 ПОСТРОЕНИЕ ГРАФИКОВ...")
    _create_clustering_visualization(
        X_reduced, cluster_labels, clusters_info, data,
        features_to_show, title_name, path_to_save
    )

    print(f"\n💾 ГРАФИК СОХРАНЕН: {path_to_save}")
    print("=" * 80)
    print("✅ КЛАСТЕРИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print("=" * 80)

    # Создание результата
    result = _create_clustering_result(
        data, cluster_labels, clusters_info, method, X_reduced
    )

    return result


# Вспомогательные функции для perform_games_clustering
def _auto_select_clustering_params(
        X_scaled: np.ndarray,
        method: str,
        max_clusters: int,
        eps_range: Tuple[float, float, float],
        min_samples_range: Tuple[float, float, float],
        path_to_save: str
) -> Tuple[Any, np.ndarray, int]:
    """Автоматический подбор параметров кластеризации"""

    print("\n🔍 АВТОМАТИЧЕСКИЙ ПОДБОР ПАРАМЕТРОВ КЛАСТЕРИЗАЦИИ...")

    if method.lower() == "kmeans":
        print("   Метод: KMeans")
        plot_save_path = path_to_save.replace('.png', '_kmeans_selection.png')
        plot_cluster_selection_metrics(X_scaled, max_clusters=max_clusters,
                                       save_path=plot_save_path)

        optimal_n = find_optimal_clusters_kmeans(X_scaled, max_clusters=max_clusters)
        n_clusters = optimal_n
        print(f"   ✅ Оптимальное количество кластеров (KMeans): {n_clusters}")

        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = clusterer.fit_predict(X_scaled)

    elif method.lower() == "dbscan":
        print("   Метод: DBSCAN")
        plot_save_path = path_to_save.replace('.png', '_dbscan_analysis.png')
        plot_dbscan_param_analysis(X_scaled, eps_range=eps_range,
                                   min_samples_range=min_samples_range,
                                   save_path=plot_save_path)

        optimal_eps, optimal_min_samples = find_optimal_dbscan_params(
            X_scaled, eps_range, min_samples_range
        )
        print(f"   ✅ Оптимальные параметры DBSCAN: eps={optimal_eps:.2f}, "
              f"min_samples={optimal_min_samples}")

        clusterer = DBSCAN(eps=optimal_eps, min_samples=optimal_min_samples)
        cluster_labels = clusterer.fit_predict(X_scaled)
        n_clusters = len(np.unique(cluster_labels[cluster_labels != -1]))

    else:
        raise ValueError(f"Неизвестный метод кластеризации: {method}")

    return clusterer, cluster_labels, n_clusters


def _apply_clustering(
        X_scaled: np.ndarray,
        method: str,
        n_clusters: int,
        eps: float,
        min_samples: int
) -> Tuple[Any, np.ndarray]:
    """Применяет выбранный метод кластеризации"""

    if method.lower() == "kmeans":
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        print("   Алгоритм: KMeans")
    elif method.lower() == "dbscan":
        clusterer = DBSCAN(eps=eps, min_samples=min_samples)
        print("   Алгоритм: DBSCAN (параметры по умолчанию)")
    else:
        raise ValueError(f"Неизвестный метод кластеризации: {method}")

    print("   Обучение модели...", end="", flush=True)
    cluster_labels = clusterer.fit_predict(X_scaled)
    print(" ✓")

    return clusterer, cluster_labels


def _handle_noise_points(cluster_labels: np.ndarray) -> np.ndarray:
    """Обрабатывает шумовые точки в DBSCAN"""
    n_noise = np.sum(cluster_labels == -1)
    if n_noise > 0:
        print(f"   DBSCAN обнаружил {n_noise} шумных точек (кластер -1)")
        max_cluster = cluster_labels.max()
        cluster_labels[cluster_labels == -1] = max_cluster + 1

    return cluster_labels


def _apply_pca(X_scaled: np.ndarray) -> np.ndarray:
    """Применяет PCA для снижения размерности"""
    pca = PCA(n_components=2)
    X_reduced = pca.fit_transform(X_scaled)

    explained_var = pca.explained_variance_ratio_
    print(f"   Объясненная дисперсия: {explained_var[0]:.1%} + {explained_var[1]:.1%} = "
          f"{(explained_var[0] + explained_var[1]):.1%}")

    return X_reduced


def _analyze_clusters(
        X: np.ndarray,
        X_scaled: np.ndarray,
        cluster_labels: np.ndarray,
        data: GamesClusteringData,
        clusterer: Any,
        method: str
) -> List[ClusterInfo]:
    """Анализирует полученные кластеры"""

    clusters_info = []
    unique_clusters = sorted(np.unique(cluster_labels))

    print(f"   Найдено кластеров: {len(unique_clusters)}")

    for cluster_id in unique_clusters:
        print(f"    Кластер {cluster_id}: ", end="", flush=True)
        mask = cluster_labels == cluster_id
        cluster_points = X_scaled[mask]

        # Статистика по признакам
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

        # Топ игр (только для KMeans)
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

        print(f"{np.sum(mask)} игр")

    return clusters_info


def _create_clustering_visualization(
        X_reduced: np.ndarray,
        cluster_labels: np.ndarray,
        clusters_info: List[ClusterInfo],
        data: GamesClusteringData,
        features_to_show: Optional[List[str]],
        title_name: str,
        path_to_save: str
) -> None:
    """Создает визуализацию результатов кластеризации"""

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    axes = axes.flatten()

    # График 1: Визуализация кластеров в 2D
    _plot_clusters_2d(axes[0], X_reduced, cluster_labels, clusters_info, data)

    # График 2: Размеры кластеров
    _plot_cluster_sizes(axes[1], clusters_info)

    # График 3: Heatmap признаков
    _plot_feature_heatmap(axes[2], clusters_info, data, features_to_show)

    # График 4: Описание кластеров
    _plot_cluster_descriptions(axes[3], clusters_info)

    plt.suptitle(title_name, fontsize=18, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)


def _plot_clusters_2d(ax, X_reduced, cluster_labels, clusters_info, data):
    """Строит 2D визуализацию кластеров"""
    unique_clusters = sorted(np.unique(cluster_labels))
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))

    for cluster_id, color in zip(unique_clusters, colors):
        mask = cluster_labels == cluster_id
        ax.scatter(X_reduced[mask, 0], X_reduced[mask, 1],
                   c=[color], s=30, alpha=0.6,
                   edgecolors='black', linewidth=0.5,
                   label=f'Кластер {cluster_id}')

    ax.set_title(f"Кластеризация игр\nВсего: {len(data.games)} игр, {len(unique_clusters)} кластеров",
                 fontsize=14, fontweight='bold')
    ax.set_xlabel(f"Компонента 1", fontsize=14)
    ax.set_ylabel(f"Компонента 2", fontsize=14)
    ax.legend(title="Кластеры", fontsize=10)
    ax.grid(True, alpha=0.3)


def _plot_cluster_sizes(ax, clusters_info):
    """Строит график размеров кластеров"""
    cluster_sizes = [info.size for info in clusters_info]
    cluster_ids = [info.cluster_id for info in clusters_info]
    colors = plt.cm.Set3(np.linspace(0, 1, len(clusters_info)))

    bars = ax.bar(range(len(cluster_sizes)), cluster_sizes, color=colors, edgecolor='black')
    ax.set_title("Размеры кластеров", fontsize=14, fontweight='bold')
    ax.set_xlabel("Номер кластера")
    ax.set_ylabel("Количество игр")
    ax.set_xticks(range(len(cluster_sizes)))
    ax.set_xticklabels([f"Кластер {cid}" for cid in cluster_ids])

    for bar, size in zip(bars, cluster_sizes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'{size}', ha='center', va='bottom', fontsize=12)


def _plot_feature_heatmap(ax, clusters_info, data, features_to_show):
    """Строит heatmap признаков по кластерам"""
    # Выбор ключевых признаков
    if features_to_show:
        key_features = [f for f in features_to_show if f in data.feature_names]
    else:
        X = np.array(data.feature_matrix)
        feature_stds = np.std(X, axis=0)
        top_feature_indices = np.argsort(feature_stds)[-6:][::-1]
        key_features = [data.feature_names[i] for i in top_feature_indices]

    print(f"   Ключевые признаки для heatmap: {', '.join(key_features)}")

    # Подготовка данных для heatmap
    heatmap_data = []
    for cluster_info in clusters_info:
        row = []
        for feature in key_features:
            if feature in cluster_info.feature_stats:
                value = cluster_info.feature_stats[feature].get(
                    'median', cluster_info.feature_stats[feature]['mean']
                )
                row.append(value)
            else:
                row.append(0)
        heatmap_data.append(row)

    heatmap_array = np.array(heatmap_data)
    heatmap_normalized_by_features = np.zeros_like(heatmap_array)

    for i in range(heatmap_array.shape[1]):
        col = heatmap_array[:, i]
        if np.ptp(col) > 0:
            heatmap_normalized_by_features[:, i] = (col - np.min(col)) / np.ptp(col)
        else:
            heatmap_normalized_by_features[:, i] = 0.5

    # Построение heatmap
    im = ax.imshow(heatmap_normalized_by_features, cmap='PiYG', aspect='auto')
    ax.set_title("Средние значения признаков по кластерам", fontsize=14, fontweight='bold')
    ax.set_xlabel("Признаки")
    ax.set_ylabel("Кластеры")
    ax.set_xticks(range(len(key_features)))
    ax.set_xticklabels(key_features, rotation=45, ha='right', fontsize=14)
    ax.set_yticks(range(len(clusters_info)))
    ax.set_yticklabels([f"Кластер {info.cluster_id}" for info in clusters_info])
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def _plot_cluster_descriptions(ax, clusters_info):
    """Добавляет текстовое описание кластеров"""
    ax.axis('off')

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
                desc += f"    - {game['name']}\n"

        description_text += desc + "\n"

    ax.text(0.02, 0.98, description_text,
            transform=ax.transAxes,
            verticalalignment='top',
            fontsize=9,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))


def _create_clustering_result(
        data: GamesClusteringData,
        cluster_labels: np.ndarray,
        clusters_info: List[ClusterInfo],
        method: str,
        X_reduced: np.ndarray
) -> ClusteringResult:
    """Создает объект результата кластеризации"""

    unique_clusters = sorted(np.unique(cluster_labels))
    game_assignments = {
        game.app_id: int(cluster_labels[i])
        for i, game in enumerate(data.games)
    }

    return ClusteringResult(
        clusters=clusters_info,
        game_assignments=game_assignments,
        n_clusters=len(unique_clusters),
        method=method,
        reduced_2d=X_reduced.tolist(),
        values={"total_games": len(data.games), "n_clusters": len(unique_clusters)},
        ticks=[f"Cluster_{cid}" for cid in unique_clusters]
    )