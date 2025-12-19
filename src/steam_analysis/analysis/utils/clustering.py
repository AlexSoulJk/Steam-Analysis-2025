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

plt.rcParams['font.family'] = 'Microsoft YaHei'

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


def plot_wcss_elbow(
        X_scaled: np.ndarray,
        max_clusters: int = 15,
        ax: Optional[plt.Axes] = None,
        save_path: Optional[str] = None,
        title: str = "Метод локтя (Elbow Method)",
        figsize: tuple = (10, 6),
        color: str = 'blue',
        marker: str = 'o',
        linewidth: int = 2,
        markersize: int = 8
) -> plt.Axes:
    """
    Строит график WCSS (Within-Cluster Sum of Squares) для метода локтя.

    Параметры:
    ----------
    X_scaled : np.ndarray
        Масштабированные данные для кластеризации
    max_clusters : int
        Максимальное количество кластеров для анализа (по умолчанию 15)
    ax : Optional[plt.Axes]
        Ось Matplotlib для отрисовки (если None, создается новая фигура)
    save_path : Optional[str]
        Путь для сохранения графика (если None, не сохраняется)
    title : str
        Заголовок графика
    figsize : tuple
        Размер фигуры (ширина, высота)
    color : str
        Цвет линии и точек
    marker : str
        Стиль маркера точек
    linewidth : int
        Толщина линии
    markersize : int
        Размер маркеров

    Возвращает:
    -----------
    plt.Axes
        Ось с построенным графиком
    """

    print(f"📊 Построение графика WCSS...")
    print(f"   Перебираем K от 2 до {max_clusters}")

    # Создаем фигуру, если ax не предоставлен
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure if hasattr(ax, 'figure') else plt.gcf()

    # Вычисляем WCSS для разных значений k
    cluster_range = range(2, max_clusters + 1)
    wcss_values = []

    for idx, n in enumerate(cluster_range, 1):
        print(f"    [{idx}/{len(cluster_range)}] K={n}...", end="", flush=True)

        # Используем существующую функцию из вашего кода
        metrics = KMeansParamAnalyzer.calculate_metrics(X_scaled, n)
        wcss_values.append(metrics['wcss'])

        print(f" WCSS={metrics['wcss']:.1f}")

    # Преобразуем в numpy массив для вычислений
    wcss_np = np.array(wcss_values)

    # Метод локтя: находим точку излома (используя вторую производную)
    if len(wcss_np) > 2:
        # Первая производная (скорость изменения)
        first_deriv = np.diff(wcss_np)

        # Вторая производная (ускорение изменения)
        second_deriv = np.diff(first_deriv)

        # Находим точку максимального изгиба (максимальное ускорение)
        if len(second_deriv) > 0:
            elbow_idx = np.argmax(np.abs(second_deriv)) + 2  # +2 из-за двойного дифференцирования
            elbow_idx = min(elbow_idx, len(cluster_range) - 1)
            elbow_k = cluster_range[elbow_idx]
            elbow_wcss = wcss_np[elbow_idx]
        else:
            elbow_idx = 2
            elbow_k = cluster_range[elbow_idx]
            elbow_wcss = wcss_np[elbow_idx]
    else:
        elbow_k = cluster_range[0]
        elbow_wcss = wcss_np[0]

    # Построение основного графика
    line = ax.plot(cluster_range, wcss_values,
                   marker=marker,
                   color=color,
                   linewidth=linewidth,
                   markersize=markersize,
                   label='WCSS')

    # Добавляем точки для лучшей видимости
    ax.scatter(cluster_range, wcss_values,
               color=color,
               s=markersize * 30,
               zorder=5,
               alpha=0.6)

    # Подсветка точки локтя
    ax.scatter(elbow_k, elbow_wcss,
               color='red',
               s=200,
               zorder=10,
               edgecolor='black',
               linewidth=2,
               label=f'Точка локтя (K={elbow_k})')

    # Добавляем аннотацию для точки локтя
    ax.annotate(f'K={elbow_k}\nWCSS={elbow_wcss:.0f}',
                xy=(elbow_k, elbow_wcss),
                xytext=(elbow_k + 1, elbow_wcss * 1.05),
                fontsize=10,
                fontweight='bold',
                color='red',
                arrowprops=dict(arrowstyle='->',
                                color='red',
                                lw=1.5,
                                connectionstyle="arc3,rad=.2"))

    # Добавляем линии сетки
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)  # Сетка под графиком

    # Настройка осей
    ax.set_xlabel('Количество кластеров (K)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Within-Cluster Sum of Squares (WCSS)',
                  fontsize=12,
                  fontweight='bold',
                  color=color)

    # Устанавливаем целочисленные значения на оси X
    ax.set_xticks(list(cluster_range))
    ax.set_xticklabels([str(k) for k in cluster_range])

    # Добавляем второй график с процентным изменением WCSS
    if len(wcss_np) > 1:
        # Вычисляем процентное изменение WCSS
        wcss_percentage_change = np.diff(wcss_np) / wcss_np[:-1] * 100

        # Создаем вторую ось для процентного изменения
        ax2 = ax.twinx()
        ax2.plot(cluster_range[1:], wcss_percentage_change,
                 color='green',
                 linestyle='--',
                 marker='s',
                 markersize=6,
                 linewidth=1.5,
                 alpha=0.7,
                 label='% изменение WCSS')

        ax2.set_ylabel('Процентное изменение WCSS (%)',
                       fontsize=11,
                       color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        ax2.grid(False)

    # Заголовок
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Легенда
    handles, labels = ax.get_legend_handles_labels()
    if len(wcss_np) > 1:
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(handles + handles2, labels + labels2,
                  loc='upper right',
                  fontsize=10,
                  framealpha=0.9)
    else:
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

    # Автоматическая настройка пределов осей
    ax.set_xlim([min(cluster_range) - 0.5, max(cluster_range) + 0.5])

    # Вывод статистики в консоль
    print(f"\n📈 Анализ графика локтя:")
    print(f"   Точка локтя (рекомендуемое K): {elbow_k}")
    print(f"   WCSS в точке локтя: {elbow_wcss:.0f}")

    if len(wcss_np) > 1:
        print(f"   Процент изменения WCSS от K={elbow_k - 1} к K={elbow_k}: "
              f"{wcss_percentage_change[elbow_idx - 2]:.1f}%")

    # Сохранение графика
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   График сохранен: {save_path}")

    return ax


def plot_detailed_wcss_analysis(
        X_scaled: np.ndarray,
        max_clusters: int = 15,
        save_path: Optional[str] = None,
        figsize: tuple = (14, 10)
) -> None:
    """
    Строит детальный анализ WCSS с несколькими графиками.

    Параметры:
    ----------
    X_scaled : np.ndarray
        Масштабированные данные
    max_clusters : int
        Максимальное количество кластеров
    save_path : Optional[str]
        Путь для сохранения
    figsize : tuple
        Размер фигуры
    """

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # 1. Основной график WCSS
    plot_wcss_elbow(
        X_scaled,
        max_clusters=max_clusters,
        ax=axes[0, 0],
        title="Основной график метода локтя",
        color='royalblue'
    )

    # 2. WCSS в логарифмической шкале
    plot_wcss_elbow(
        X_scaled,
        max_clusters=max_clusters,
        ax=axes[0, 1]
    )
    axes[0, 1].set_yscale('log')
    axes[0, 1].set_title('WCSS в логарифмической шкале', fontsize=14, fontweight='bold')

    # 3. WCSS с производными
    cluster_range = range(2, max_clusters + 1)
    wcss_values = []

    for n in cluster_range:
        metrics = KMeansParamAnalyzer.calculate_metrics(X_scaled, n)
        wcss_values.append(metrics['wcss'])

    wcss_np = np.array(wcss_values)

    # Первая производная
    if len(wcss_np) > 1:
        first_deriv = np.diff(wcss_np)
        axes[1, 0].plot(cluster_range[1:], first_deriv,
                        marker='o',
                        color='darkorange',
                        linewidth=2)
        axes[1, 0].set_xlabel('Количество кластеров (K)', fontsize=12)
        axes[1, 0].set_ylabel('ΔWCSS (Первая производная)',
                              fontsize=12,
                              color='darkorange')
        axes[1, 0].set_title('Первая производная WCSS',
                             fontsize=14,
                             fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_xticks(list(cluster_range[1:]))

        # Вторая производная
        if len(first_deriv) > 1:
            second_deriv = np.diff(first_deriv)
            axes[1, 1].plot(cluster_range[2:], second_deriv,
                            marker='s',
                            color='purple',
                            linewidth=2)
            axes[1, 1].set_xlabel('Количество кластеров (K)', fontsize=12)
            axes[1, 1].set_ylabel('Δ²WCSS (Вторая производная)',
                                  fontsize=12,
                                  color='purple')
            axes[1, 1].set_title('Вторая производная WCSS (точка локтя)',
                                 fontsize=14,
                                 fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].set_xticks(list(cluster_range[2:]))

            # Находим точку локтя по второй производной
            elbow_idx = np.argmax(np.abs(second_deriv))
            elbow_k = cluster_range[2:][elbow_idx]
            axes[1, 1].axvline(x=elbow_k, color='red', linestyle='--', alpha=0.7,
                               label=f'Точка локтя K={elbow_k}')
            axes[1, 1].legend()

    plt.suptitle('Детальный анализ метода локтя для выбора количества кластеров',
                 fontsize=16,
                 fontweight='bold',
                 y=1.02)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   Детальный анализ сохранен: {save_path}")

    plt.show()


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
        eps_range: Tuple[float, float, float] = (0.1, 2.0, 0.2),
        min_samples_range: Tuple[float, float, float] = (20, 50, 10)
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


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import Optional, Tuple, List
from sklearn.decomposition import PCA


def plot_3d_clusters(
        X_scaled: np.ndarray,
        cluster_labels: np.ndarray,
        feature_names: List[str],
        title: str = "3D Визуализация кластеров",
        save_path: Optional[str] = None,
        figsize: Tuple[int, int] = (14, 10),
        elev: int = 20,
        azim: int = 45,
        alpha: float = 0.6,
        marker_size: int = 30
) -> None:
    """
    Строит 3D график кластеров.

    Параметры:
    ----------
    X_scaled : np.ndarray
        Масштабированные данные (>=3 признаков)
    cluster_labels : np.ndarray
        Метки кластеров
    feature_names : List[str]
        Названия признаков
    title : str
        Заголовок графика
    save_path : Optional[str]
        Путь для сохранения графика
    figsize : Tuple[int, int]
        Размер фигуры
    elev : int
        Угол возвышения камеры
    azim : int
        Азимутальный угол камеры
    alpha : float
        Прозрачность точек
    marker_size : int
        Размер маркеров
    """

    print(f"🎨 Построение 3D графика кластеров...")

    if X_scaled.shape[1] < 3:
        print(f"   ⚠️  Для 3D визуализации нужно минимум 3 признака, а у вас {X_scaled.shape[1]}")
        print(f"   ✅ Применяем PCA для получения 3 компонент...")
        pca_3d = PCA(n_components=3)
        X_3d = pca_3d.fit_transform(X_scaled)

        explained_var = pca_3d.explained_variance_ratio_
        feature_names_3d = [
            f"PCA 1 ({explained_var[0]:.1%})",
            f"PCA 2 ({explained_var[1]:.1%})",
            f"PCA 3 ({explained_var[2]:.1%})"
        ]

        print(f"   Объясненная дисперсия: {explained_var[0]:.1%} + "
              f"{explained_var[1]:.1%} + {explained_var[2]:.1%} = "
              f"{(explained_var[0] + explained_var[1] + explained_var[2]):.1%}")

    else:
        # Используем первые 3 признака
        X_3d = X_scaled[:, :3]
        feature_names_3d = feature_names[:3]
        print(f"   ✅ Используем первые 3 признака: {', '.join(feature_names_3d)}")

    # Создаем 3D график
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')

    # Получаем уникальные кластеры и цвета
    unique_clusters = sorted(np.unique(cluster_labels))
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))

    # Рисуем каждый кластер
    for cluster_id, color in zip(unique_clusters, colors):
        mask = cluster_labels == cluster_id
        ax.scatter(
            X_3d[mask, 0], X_3d[mask, 1], X_3d[mask, 2],
            c=[color],
            s=marker_size,
            alpha=alpha,
            edgecolors='black',
            linewidth=0.5,
            label=f'Кластер {cluster_id}'
        )

    # Настройка осей
    ax.set_xlabel(feature_names_3d[0], fontsize=12, labelpad=10)
    ax.set_ylabel(feature_names_3d[1], fontsize=12, labelpad=10)
    ax.set_zlabel(feature_names_3d[2], fontsize=12, labelpad=10)

    # Настройка заголовка
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    # Добавляем легенду
    ax.legend(loc='upper left', bbox_to_anchor=(0, 0.85), fontsize=10)

    # Настраиваем угол обзора
    ax.view_init(elev=elev, azim=azim)

    # Добавляем сетку
    ax.grid(True, alpha=0.3)

    # Добавляем дополнительную информацию
    info_text = f"Всего точек: {len(X_3d)}\n"
    info_text += f"Кластеров: {len(unique_clusters)}\n"

    # Если использовался PCA, добавляем информацию
    if X_scaled.shape[1] < 3:
        info_text += f"PCA проекция на 3D\n"
        info_text += f"Объяснено: {(explained_var[0] + explained_var[1] + explained_var[2]):.1%} дисперсии"

    # Размещаем текст в правом верхнем углу
    ax.text2D(0.95, 0.95, info_text,
              transform=ax.transAxes,
              fontsize=9,
              verticalalignment='top',
              horizontalalignment='right',
              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Сохраняем график
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   💾 3D график сохранен: {save_path}")

    plt.show()
    return fig, ax


def plot_interactive_3d_clusters(
        X_scaled: np.ndarray,
        cluster_labels: np.ndarray,
        feature_names: List[str],
        game_names: Optional[List[str]] = None,
        title: str = "Интерактивная 3D визуализация",
        save_path: Optional[str] = None
) -> None:
    """
    Создает интерактивный 3D график с возможностью вращения.
    """
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        print(f"🎨 Построение интерактивного 3D графика...")

        if X_scaled.shape[1] < 3:
            pca_3d = PCA(n_components=3)
            X_3d = pca_3d.fit_transform(X_scaled)
            explained_var = pca_3d.explained_variance_ratio_
            axis_labels = [
                f"PCA 1 ({explained_var[0]:.1%} дисперсии)",
                f"PCA 2 ({explained_var[1]:.1%} дисперсии)",
                f"PCA 3 ({explained_var[2]:.1%} дисперсии)"
            ]
        else:
            X_3d = X_scaled[:, :3]
            axis_labels = feature_names[:3]

        # Создаем фигуру
        fig = go.Figure()

        # Получаем уникальные кластеры
        unique_clusters = sorted(np.unique(cluster_labels))

        # Добавляем каждый кластер
        for cluster_id in unique_clusters:
            mask = cluster_labels == cluster_id

            # Подготовка подсказок
            hover_text = []
            for i in range(np.sum(mask)):
                text = f"Кластер: {cluster_id}<br>"
                if game_names is not None and i < len(game_names):
                    text += f"Игра: {game_names[i]}<br>"
                text += f"{axis_labels[0]}: {X_3d[mask, 0][i]:.2f}<br>"
                text += f"{axis_labels[1]}: {X_3d[mask, 1][i]:.2f}<br>"
                text += f"{axis_labels[2]}: {X_3d[mask, 2][i]:.2f}"
                hover_text.append(text)

            # Добавляем слой с кластером
            fig.add_trace(go.Scatter3d(
                x=X_3d[mask, 0],
                y=X_3d[mask, 1],
                z=X_3d[mask, 2],
                mode='markers',
                marker=dict(
                    size=5,
                    opacity=0.7,
                    line=dict(width=0.5, color='black')
                ),
                name=f'Кластер {cluster_id}',
                text=hover_text,
                hoverinfo='text'
            ))

        # Настраиваем вид
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=20)
            ),
            scene=dict(
                xaxis_title=axis_labels[0],
                yaxis_title=axis_labels[1],
                zaxis_title=axis_labels[2],
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=1000,
            height=800,
            showlegend=True
        )

        # Сохраняем или показываем
        if save_path:
            pio.write_html(fig, save_path)
            print(f"   💾 Интерактивный график сохранен: {save_path}")

        # Показываем график
        fig.show()

    except ImportError:
        print("   ⚠️  Для интерактивного графика установите plotly: pip install plotly")
        # Возвращаемся к обычному 3D
        plot_3d_clusters(X_scaled, cluster_labels, feature_names, title, save_path)


def create_3d_visualization(
        X_scaled: np.ndarray,
        cluster_labels: np.ndarray,
        clusters_info: List[ClusterInfo],
        data: GamesClusteringData,
        title_name: str,
        path_to_save: str,
        create_interactive: bool = False
) -> None:
    """
    Создает комплексную 3D визуализацию результатов кластеризации.
    """

    print(f"\n🎨 СОЗДАНИЕ 3D ВИЗУАЛИЗАЦИИ...")

    # Используем plot_3d_clusters напрямую, а не переменную с таким же именем
    try:
        # Основной 3D график
        plot_3d_clusters(
            X_scaled=X_scaled,
            cluster_labels=cluster_labels,
            feature_names=data.feature_names,
            title=f"{title_name} - 3D визуализация",
            save_path=path_to_save.replace('.png', '_3d.png'),
            figsize=(16, 12),
            elev=25,
            azim=45
        )

        print(f"   ✅ Основной 3D график создан")

        # Создаем дополнительные 3D графики с разных ракурсов
        angles = [
            (20, 45, "Основной вид"),
            (30, 60, "Вид сверху"),
            (10, 30, "Вид сбоку"),
            (40, 120, "Диагональный вид")
        ]

        for elev, azim, view_name in angles:
            try:
                plot_3d_clusters(
                    X_scaled=X_scaled,
                    cluster_labels=cluster_labels,
                    feature_names=data.feature_names,
                    title=f"{title_name} - {view_name}",
                    save_path=path_to_save.replace('.png', f'_3d_{view_name.lower().replace(" ", "_")}.png'),
                    figsize=(12, 8),
                    elev=elev,
                    azim=azim
                )
                print(f"   ✅ 3D график '{view_name}' создан")
            except Exception as e:
                print(f"   ⚠️  Ошибка при создании 3D графика '{view_name}': {e}")

        # 3D график с центрами кластеров
        plot_3d_with_centroids(X_scaled, cluster_labels, clusters_info, data, title_name, path_to_save)
        print(f"   ✅ 3D график с центрами кластеров создан")

        # Интерактивный график (опционально)
        if create_interactive:
            try:
                game_names = [game.name for game in data.games]
                plot_interactive_3d_clusters(
                    X_scaled=X_scaled,
                    cluster_labels=cluster_labels,
                    feature_names=data.feature_names,
                    game_names=game_names,
                    title=f"{title_name} - Интерактивная 3D визуализация",
                    save_path=path_to_save.replace('.png', '_3d_interactive.html')
                )
                print(f"   ✅ Интерактивный 3D график создан")
            except Exception as e:
                print(f"   ⚠️  Ошибка при создании интерактивного 3D графика: {e}")

        print(f"✅ 3D визуализация создана успешно!")

    except Exception as e:
        print(f"❌ Критическая ошибка при создании 3D визуализации: {e}")
        import traceback
        traceback.print_exc()


def plot_3d_with_centroids(
        X_scaled: np.ndarray,
        cluster_labels: np.ndarray,
        clusters_info: List[ClusterInfo],
        data: GamesClusteringData,
        title_name: str,
        path_to_save: str
) -> None:
    """
    Строит 3D график с выделенными центрами кластеров.
    """

    print(f"   📊 Построение 3D графика с центрами кластеров...")

    if X_scaled.shape[1] < 3:
        pca_3d = PCA(n_components=3)
        X_3d = pca_3d.fit_transform(X_scaled)
    else:
        X_3d = X_scaled[:, :3]

    # Создаем 3D график
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')

    unique_clusters = sorted(np.unique(cluster_labels))
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))

    # Рисуем точки кластеров
    for cluster_id, color in zip(unique_clusters, colors):
        mask = cluster_labels == cluster_id
        ax.scatter(
            X_3d[mask, 0], X_3d[mask, 1], X_3d[mask, 2],
            c=[color],
            s=30,
            alpha=0.4,
            edgecolors='black',
            linewidth=0.3,
            label=f'Кластер {cluster_id}'
        )

        # Находим и рисуем центр кластера
        if len(X_3d[mask]) > 0:
            centroid = np.mean(X_3d[mask], axis=0)
            ax.scatter(
                centroid[0], centroid[1], centroid[2],
                c='red',
                s=200,
                marker='X',
                edgecolors='black',
                linewidth=2,
                label=f'Центр {cluster_id}' if cluster_id == unique_clusters[0] else ""
            )

            # Подписываем центр
            ax.text(
                centroid[0], centroid[1], centroid[2],
                f'C{cluster_id}',
                fontsize=12,
                fontweight='bold',
                color='darkred'
            )

    # Настраиваем график
    ax.set_xlabel(data.feature_names[0] if len(data.feature_names) > 0 else "Признак 1",
                  fontsize=12, labelpad=10)
    ax.set_ylabel(data.feature_names[1] if len(data.feature_names) > 1 else "Признак 2",
                  fontsize=12, labelpad=10)
    ax.set_zlabel(data.feature_names[2] if len(data.feature_names) > 2 else "Признак 3",
                  fontsize=12, labelpad=10)

    ax.set_title(f"{title_name}\n3D с центрами кластеров", fontsize=16, fontweight='bold', pad=20)

    # Добавляем информацию о кластерах
    info_text = "ЦЕНТРЫ КЛАСТЕРОВ:\n"
    for cluster_info in clusters_info:
        info_text += f"Кластер {cluster_info.cluster_id}: {cluster_info.size} игр\n"

    ax.text2D(0.02, 0.98, info_text,
              transform=ax.transAxes,
              fontsize=9,
              verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    ax.legend(loc='upper left', bbox_to_anchor=(0, 0.85), fontsize=10)
    ax.view_init(elev=25, azim=45)
    ax.grid(True, alpha=0.3)

    # Сохраняем
    save_path = path_to_save.replace('.png', '_3d_centroids.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   💾 График с центрами сохранен: {save_path}")


def perform_games_clustering(
        data: GamesClusteringData,
        title_name: str,
        path_to_save: str,
        method: str = "kmeans",
        n_clusters: int = 5,
        features_to_show: Optional[List[str]] = None,
        auto_select_params: bool = False,
        max_clusters: int = 8,
        eps_range: Tuple[float, float, float] = (0.1, 2.0, 0.5),
        min_samples_range: Tuple[float, float, float] = (5, 50, 15),
        eps: float = 1.0,
        min_samples: int = 45,
        make_3d_viz: bool = True,  # Переименованный параметр для 3D
        make_interactive_3d: bool = False  # Переименованный параметр для интерактивной 3D
) -> ClusteringResult:
    """Основная функция кластеризации игр"""

    print("=" * 80)
    print(f"🚀 ЗАПУСК КЛАСТЕРИЗАЦИИ: {title_name}")
    print(f"   Метод: {method}")
    print(f"   Игр: {len(data.games)}")
    print(f"   Признаков: {len(data.feature_names)}")
    print(f"   Признаки: {', '.join(data.feature_names)}")
    print(f"   3D визуализация: {'Включена' if make_3d_viz else 'Отключена'}")
    if make_3d_viz:
        print(f"   Интерактивная 3D: {'Включена' if make_interactive_3d else 'Отключена'}")
    print("=" * 80)

    # Проверка данных
    if not data.feature_matrix:
        raise ValueError("❌ Нет матрицы признаков для кластеризации")

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

    # Подготовка данных для визуализации с учетом количества признаков
    print("\n📊 ПОДГОТОВКА ДАННЫХ ДЛЯ ВИЗУАЛИЗАЦИИ...")
    if len(data.feature_names) == 2:
        print(f"   ✓ Используем исходные признаки для визуализации:")
        print(f"      X: {data.feature_names[0]}")
        print(f"      Y: {data.feature_names[1]}")
        X_for_plot = X_scaled
        pca_info = None
    else:
        print(f"   ⚠️  {len(data.feature_names)} признака, применяем PCA...")
        X_for_plot, pca_info = _apply_pca_with_info(X_scaled, data.feature_names)

    # Анализ кластеров
    print(f"\n📊 АНАЛИЗ КЛАСТЕРОВ...")
    clusters_info = _analyze_clusters(
        X, X_scaled, cluster_labels, data, clusterer, method
    )

    # Детальный вывод в консоль
    print_detailed_cluster_analysis(clusters_info, data)

    # Построение 2D графиков
    print("\n🎨 ПОСТРОЕНИЕ 2D ГРАФИКОВ...")
    _create_clustering_visualization(
        X_for_plot, cluster_labels, clusters_info, data,
        features_to_show, title_name, path_to_save, pca_info
    )

    # Построение 3D графиков (если включено)
    if make_3d_viz and len(data.feature_names) >= 2:
        print(f"\n🎨 СОЗДАНИЕ 3D ВИЗУАЛИЗАЦИИ...")
        try:
            # Вызываем функцию 3D визуализации
            create_3d_visualization(
                X_scaled=X_scaled,
                cluster_labels=cluster_labels,
                clusters_info=clusters_info,
                data=data,
                title_name=title_name,
                path_to_save=path_to_save,
                create_interactive=make_interactive_3d
            )
            print("   ✅ 3D визуализация создана успешно!")
        except NameError:
            print(f"   ⚠️  Функция create_3d_visualization не найдена")
            print(f"   ⚠️  Убедитесь, что она определена в этом файле или импортирована")
        except ImportError as e:
            print(f"   ⚠️  Ошибка импорта: {e}")
            print(f"   ⚠️  Убедитесь, что установлены необходимые библиотеки")
        except Exception as e:
            print(f"   ⚠️  Ошибка при создании 3D визуализации: {type(e).__name__}")
            print(f"   Причина: {e}")
            import traceback
            traceback.print_exc()
    else:
        reason = "отключена" if not make_3d_viz else f"только {len(data.feature_names)} признака"
        print(f"   ⚠️  3D визуализация пропущена ({reason})")

    print(f"\n💾 ГРАФИКИ СОХРАНЕНЫ:")
    print(f"   Основной график: {path_to_save}")
    if make_3d_viz and len(data.feature_names) >= 2:
        base_name = path_to_save.replace('.png', '')
        print(f"   3D графики: {base_name}_3d*.png")
        if make_interactive_3d:
            print(f"   Интерактивный 3D: {base_name}_3d_interactive.html")

    print("=" * 80)
    print("✅ КЛАСТЕРИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print("=" * 80)

    # Создание результата
    result = _create_clustering_result(
        data, cluster_labels, clusters_info, method, X_for_plot, pca_info
    )

    return result


def print_detailed_cluster_analysis(
        clusters_info: List[ClusterInfo],
        data: GamesClusteringData
) -> None:
    """Выводит детальный анализ кластеров в консоль"""

    print("\n" + "=" * 80)
    print("📊 ДЕТАЛЬНЫЙ АНАЛИЗ КЛАСТЕРОВ")
    print("=" * 80)

    total_games = sum(cluster.size for cluster in clusters_info)

    for cluster in clusters_info:
        print(f"\n{'━' * 60}")
        print(f"🎯 КЛАСТЕР {cluster.cluster_id}")
        print(f"   Размер: {cluster.size} игр ({cluster.size / total_games:.1%} от общего числа)")
        print(f"   {'━' * 40}")

        if cluster.description:
            print(cluster.description)

        print(f"\n   📈 ДЕТАЛЬНАЯ СТАТИСТИКА:")
        for feature_name, stats in cluster.feature_stats.items():
            print(f"      {feature_name:25} | "
                  f"Среднее: {stats['mean']:8.2f} | "
                  f"Медиана: {stats['median']:8.2f} | "
                  f"Std: {stats['std']:6.2f}")

        if cluster.top_games:
            print(f"\n   🎮 ТИПИЧНЫЕ ПРЕДСТАВИТЕЛИ:")
            for i, game in enumerate(cluster.top_games[:5], 1):
                print(f"      {i:2}. {game['name'][:40]:40} (ID: {game['app_id']})")

    print(f"\n{'=' * 80}")
    print("📋 СВОДНАЯ ТАБЛИЦА КЛАСТЕРОВ:")
    print("=" * 80)

    # Создаем сводную таблицу
    headers = ["Кластер", "Игр", "Доля", "Цена(мед)", "Качество", "Возраст", "Платформы"]
    print(f"{headers[0]:^8} | {headers[1]:^6} | {headers[2]:^6} | {headers[3]:^10} | "
          f"{headers[4]:^8} | {headers[5]:^8} | {headers[6]:^10}")
    print("-" * 80)

    for cluster in clusters_info:
        stats = cluster.feature_stats

        price = stats.get('price_rub', {}).get('median', 0)
        quality = stats.get('positive_ratio', {}).get('median', 0) * 100
        age = stats.get('game_age_years', {}).get('median', 0)
        platforms = stats.get('platforms_count', {}).get('median', 0)

        print(f"{cluster.cluster_id:^8} | {cluster.size:^6} | {cluster.size / total_games:^6.1%} | "
              f"{price:^10.0f} | {quality:^8.1f}% | {age:^8.1f} | {platforms:^10.1f}")


def _apply_pca_with_info(X_scaled: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Применяет PCA для снижения размерности с возвратом информации о компонентах"""
    print(f"   Применяем PCA для {len(feature_names)} признаков:")
    for i, name in enumerate(feature_names):
        print(f"     {i + 1}. {name}")

    pca = PCA(n_components=2)
    X_reduced = pca.fit_transform(X_scaled)

    explained_var = pca.explained_variance_ratio_

    # Собираем информацию о компонентах
    components_info = {
        'explained_variance': explained_var.tolist(),
        'components': pca.components_.tolist(),
        'feature_names': feature_names,
        'feature_contributions': {}
    }

    # Анализируем вклад каждого признака в компоненты
    for i, component in enumerate(pca.components_):
        print(f"   Компонента {i + 1}:")
        contributions = []
        for j, (coeff, name) in enumerate(zip(component, feature_names)):
            contribution = abs(coeff) * 100  # Вклад в процентах
            contributions.append((contribution, name, coeff))
            if abs(coeff) > 0.3:  # Значимый вклад
                direction = "положительно" if coeff > 0 else "отрицательно"
                print(f"     {name}: {coeff:.3f} ({direction})")

        # Сортируем по вкладу
        contributions.sort(reverse=True)
        top_features = [(name, coeff) for _, name, coeff in contributions[:3]]
        components_info['feature_contributions'][f'component_{i + 1}'] = top_features

    return X_reduced, components_info

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


def _prepare_data_for_visualization(
        X_scaled: np.ndarray,
        feature_names: List[str]
) -> Tuple[np.ndarray, str, str]:
    """Подготавливает данные для визуализации"""

    if len(feature_names) == 2:
        # Если 2 признака, используем их как есть
        X_for_plot = X_scaled
        x_label = feature_names[0]
        y_label = feature_names[1]

        print(f"   Визуализация по осям: X={x_label}, Y={y_label}")
        return X_for_plot, x_label, y_label

    else:
        # Если больше 2 признаков, применяем PCA
        print("   Применяем PCA для снижения размерности...")
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        explained_var = pca.explained_variance_ratio_
        print(f"   Объясненная дисперсия: {explained_var[0]:.1%} + {explained_var[1]:.1%} = "
              f"{(explained_var[0] + explained_var[1]):.1%}")

        return X_pca, "Компонента 1 (PCA)", "Компонента 2 (PCA)"


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

    # Общее количество игр
    total_games = len(X)

    print(f"   Найдено кластеров: {len(unique_clusters)}")
    print(f"   Всего игр: {total_games}")

    # Собираем общую статистику для сравнения
    overall_stats = {}
    for i, feature_name in enumerate(data.feature_names):
        overall_stats[feature_name] = {
            'mean': float(np.mean(X[:, i])),
            'median': float(np.median(X[:, i])),
            'std': float(np.std(X[:, i]))
        }

    # Добавляем total_games в overall_stats для использования в описании
    overall_stats['total_games'] = {
        'mean': float(total_games),
        'median': float(total_games),
        'std': 0.0
    }

    for cluster_id in unique_clusters:
        print(f"    Анализ кластера {cluster_id}: ", end="", flush=True)
        mask = cluster_labels == cluster_id
        cluster_points = X_scaled[mask]
        cluster_points_original = X[mask]
        cluster_size = int(np.sum(mask))

        # Статистика по признакам
        feature_stats = {}
        for i, feature_name in enumerate(data.feature_names):
            feature_values = cluster_points_original[:, i]
            if len(feature_values) > 0:
                feature_stats[feature_name] = {
                    'mean': float(np.mean(feature_values)),
                    'std': float(np.std(feature_values)),
                    'min': float(np.min(feature_values)),
                    'max': float(np.max(feature_values)),
                    'median': float(np.median(feature_values)),
                    'q25': float(np.percentile(feature_values, 25)),
                    'q75': float(np.percentile(feature_values, 75)),
                    'vs_overall': float(np.mean(feature_values) - overall_stats[feature_name]['mean'])
                }

        # Топ игр
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
                    'distance_to_center': float(distances[idx]),
                    'features': game.features
                })

        # Генерируем описание для консоли
        description = _generate_cluster_description(
            cluster_id, cluster_size, feature_stats, overall_stats, top_games
        )

        clusters_info.append(ClusterInfo(
            cluster_id=int(cluster_id),
            size=cluster_size,
            centroid=clusterer.cluster_centers_[cluster_id].tolist() if hasattr(clusterer, 'cluster_centers_') else [],
            feature_stats=feature_stats,
            top_games=top_games,
            description=description
        ))

        print(f"{cluster_size} игр")

    return clusters_info


def _generate_cluster_description(
        cluster_id: int,
        cluster_size: int,
        feature_stats: Dict[str, Dict[str, float]],
        overall_stats: Dict[str, Dict[str, float]],
        top_games: List[Dict]
) -> str:
    """Генерирует подробное описание кластера"""

    description_parts = []

    # 1. Общая информация (ИСПРАВЛЕННЫЙ РАСЧЕТ)
    if 'total_games' in overall_stats:
        total = overall_stats['total_games']['mean']
        percentage = (cluster_size / total * 100) if total > 0 else 0
        description_parts.append(f"КЛАСТЕР {cluster_id} ({cluster_size} игр, {percentage:.1%} от общего числа)")
    else:
        description_parts.append(f"КЛАСТЕР {cluster_id} ({cluster_size} игр)")


def _determine_player_profile(feature_stats: Dict[str, Dict[str, float]]) -> str:
    """Определяет профиль целевой аудитории на основе характеристик кластера"""

    profile_parts = []

    # Проверяем разные комбинации
    if 'price_rub' in feature_stats and 'positive_ratio' in feature_stats:
        price = feature_stats['price_rub']['mean']
        quality = feature_stats['positive_ratio']['mean']

        if price < 100 and quality > 0.8:
            profile_parts.append("подходит для бюджетных игроков, ценящих качество")
        elif price > 500 and quality > 0.85:
            profile_parts.append("премиум-сегмент для требовательных игроков")

    if 'achievements_count_norm' in feature_stats:
        achievements = feature_stats['achievements_count_norm']['mean']
        if achievements > 0.3:
            profile_parts.append("для коллекционеров достижений")

    if 'game_age_years' in feature_stats:
        age = feature_stats['game_age_years']['mean']
        if age > 7:
            profile_parts.append("для любителей классики")

    return " | ".join(profile_parts) if profile_parts else ""


def _generate_recommendations(feature_stats: Dict[str, Dict[str, float]]) -> str:
    """Генерирует рекомендации на основе характеристик кластера"""

    recommendations = []

    # Анализ качества
    if 'positive_ratio' in feature_stats:
        quality = feature_stats['positive_ratio']['mean']
        if quality < 0.7:
            recommendations.append("• Низкое качество: рассмотреть улучшение контента")
        elif quality > 0.9:
            recommendations.append("• Высокое качество: хороший потенциал для продвижения")

    # Анализ цены
    if 'price_rub' in feature_stats:
        price = feature_stats['price_rub']['mean']
        if 'positive_ratio' in feature_stats:
            quality = feature_stats['positive_ratio']['mean']
            if price > 1000 and quality < 0.8:
                recommendations.append("• Возможна переоценка: высокая цена при среднем качестве")
            elif price < 100 and quality > 0.85:
                recommendations.append("• Хорошее соотношение цена/качество")

    # Анализ возраста
    if 'game_age_years' in feature_stats:
        age = feature_stats['game_age_years']['mean']
        if age > 5:
            recommendations.append(f"• Старые игры ({age:.0f} лет): возможна перевыпуск или скидки")

    return "\n".join(recommendations) if recommendations else "Нет специфических рекомендаций"


def _create_clustering_visualization(
        X_for_plot: np.ndarray,
        cluster_labels: np.ndarray,
        clusters_info: List[ClusterInfo],
        data: GamesClusteringData,
        features_to_show: Optional[List[str]],
        title_name: str,
        path_to_save: str,
        pca_info: Optional[Dict[str, Any]] = None  # Добавляем параметр
) -> None:
    """Создает визуализацию результатов кластеризации"""

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    axes = axes.flatten()

    # График 1: Визуализация кластеров в 2D
    _plot_clusters_2d(axes[0], X_for_plot, cluster_labels, clusters_info,
                      data, data.feature_names, pca_info)  # Передаем pca_info

    # График 2: Размеры кластеров
    _plot_cluster_sizes(axes[1], clusters_info)

    # График 3: Heatmap признаков
    _plot_feature_heatmap(axes[2], clusters_info, data, features_to_show)

    # График 4: Упрощенная информация о кластерах
    _plot_cluster_descriptions(axes[3], clusters_info, data)

    plt.suptitle(title_name, fontsize=18, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
    plt.close(fig)


def _plot_clusters_2d(ax, X_for_plot, cluster_labels, clusters_info, data, feature_names, pca_info=None):
    """Строит 2D визуализацию кластеров"""
    unique_clusters = sorted(np.unique(cluster_labels))
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))

    for cluster_id, color in zip(unique_clusters, colors):
        mask = cluster_labels == cluster_id
        ax.scatter(X_for_plot[mask, 0], X_for_plot[mask, 1],
                   c=[color], s=30, alpha=0.6,
                   edgecolors='black', linewidth=0.5,
                   label=f'Кластер {cluster_id}')

    # Определяем подписи осей
    if len(data.feature_names) == 2:
        x_label = data.feature_names[0]
        y_label = data.feature_names[1]

        # Форматируем для читаемости
        if x_label == "price_rub":
            x_label_display = "Цена (price_rub)"
        elif x_label == "positive_ratio":
            x_label_display = "Качество (positive_ratio)"
        elif x_label == "platforms_count":
            x_label_display = "Платформы (platforms_count)"
        else:
            x_label_display = x_label

        if y_label == "positive_ratio":
            y_label_display = "Качество (positive_ratio)"
        elif y_label == "price_rub":
            y_label_display = "Цена (price_rub)"
        elif y_label == "platforms_count":
            y_label_display = "Платформы (platforms_count)"
        else:
            y_label_display = y_label

        title = f"Кластеризация игр: {x_label_display} × {y_label_display}"

        # Добавляем пояснение осей
        ax.text(0.02, 0.98,
                f"X: {x_label_display} (масштабированная)\nY: {y_label_display} (масштабированная)",
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    else:
        # Для PCA
        if pca_info:
            # Используем информацию о PCA для лучшего описания
            var1 = pca_info['explained_variance'][0] * 100
            var2 = pca_info['explained_variance'][1] * 100

            # Получаем топ признаки для каждой компоненты
            comp1_features = pca_info['feature_contributions'].get('component_1', [])
            comp2_features = pca_info['feature_contributions'].get('component_2', [])

            # Формируем описания
            comp1_desc = " + ".join([f"{coeff:.1f}×{name}" for name, coeff in comp1_features[:2]])
            comp2_desc = " + ".join([f"{coeff:.1f}×{name}" for name, coeff in comp2_features[:2]])

            x_label_display = f"Компонента 1 ({var1:.0f}% дисперсии)"
            y_label_display = f"Компонента 2 ({var2:.0f}% дисперсии)"

            title = f"Кластеризация игр (PCA проекция)"

            # Добавляем подробное описание PCA
            pca_text = f"PCA компоненты:\n"
            pca_text += f"• Компонента 1: {comp1_desc}\n"
            pca_text += f"• Компонента 2: {comp2_desc}\n"
            pca_text += f"Объясненная дисперсия: {var1 + var2:.0f}%"

            ax.text(0.02, 0.98, pca_text,
                    transform=ax.transAxes,
                    fontsize=8,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        else:
            x_label_display = "Компонента 1 (PCA)"
            y_label_display = "Компонента 2 (PCA)"
            title = f"Кластеризация игр (PCA проекция)"

    ax.set_title(f"{title}\nВсего: {len(data.games)} игр, {len(unique_clusters)} кластеров",
                 fontsize=14, fontweight='bold')
    ax.set_xlabel(x_label_display, fontsize=12)
    ax.set_ylabel(y_label_display, fontsize=12)
    ax.legend(title="Кластеры", fontsize=10)
    ax.grid(True, alpha=0.3)

    # Добавляем сетку для лучшей читаемости
    ax.grid(True, alpha=0.2, linestyle='--')


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


def _plot_cluster_descriptions(ax, clusters_info, data):
    """Упрощенное отображение информации о кластерах на графике"""
    ax.axis('off')

    n_clusters = len(clusters_info)
    if n_clusters <= 4:
        n_cols = 2
    elif n_clusters <= 9:
        n_cols = 3
    else:
        n_cols = 4

    n_rows = (n_clusters + n_cols - 1) // n_cols

    col_width = 1.0 / n_cols
    row_height = 1.0 / n_rows

    # Используем цветовую схему как на графике
    colors = plt.cm.Set3(np.linspace(0, 1, n_clusters))

    for idx, cluster_info in enumerate(clusters_info):
        row = idx // n_cols
        col = idx % n_cols

        x_pos = col * col_width + 0.01  # Уменьшаем отступ
        y_pos = 1.0 - (row + 1) * row_height + 0.01  # Уменьшаем отступ

        # Размер блока
        block_width = col_width - 0.02
        block_height = row_height - 0.02

        # Фон блока с цветом кластера
        from matplotlib.patches import FancyBboxPatch
        rect = FancyBboxPatch((x_pos, y_pos),
                              block_width,
                              block_height,
                              boxstyle="round,pad=0.01",  # Уменьшаем padding
                              facecolor=colors[idx],
                              alpha=0.3,
                              edgecolor='black',
                              linewidth=1)
        ax.add_patch(rect)

        # Начальные координаты текста внутри блока
        text_y = y_pos + block_height - 0.02  # Начинаем почти сверху

        # Заголовок блока
        ax.text(x_pos + 0.005, text_y,
                f"Кластер {cluster_info.cluster_id}",
                verticalalignment='top',
                fontsize=9,
                fontweight='bold',
                color='darkblue')

        # Сдвигаем вниз для статистики
        text_y -= 0.03

        # Статистика по ключевым признакам
        key_features = ['price_rub', 'positive_ratio', 'game_age_years', 'platforms_count']

        for feature in key_features:
            if feature in cluster_info.feature_stats:
                stats = cluster_info.feature_stats[feature]
                value = stats['median']

                # Форматируем значения
                if feature == 'price_rub':
                    if value == 0:
                        text = f"Бесплатные"
                    else:
                        text = f"Средняя стоимость {value} руб."
                elif feature == 'positive_ratio':
                    text = f"{value * 100:.2f}% положительных отзывов"
                elif feature == 'game_age_years':
                    text = f"Средний возраст игры - {value:.2f}"
                elif feature == 'platforms_count':
                    text = f"Поддержка {value} платформ"

                ax.text(x_pos + 0.005, text_y,
                        text,
                        verticalalignment='top',
                        fontsize=8)
                text_y -= 0.025  # Меньший интервал между строками

        # Размер кластера
        ax.text(x_pos + 0.005, text_y,
                f"{cluster_info.size} игр",
                verticalalignment='top',
                fontsize=8)
        text_y -= 0.03

        # Примеры игр (максимум 2)
        if cluster_info.top_games:
            ax.text(x_pos + 0.005, text_y,
                    "Примеры:",
                    verticalalignment='top',
                    fontsize=8,
                    fontstyle='italic',
                    color='darkgreen')
            text_y -= 0.02

            for game in cluster_info.top_games[:4]:
                # Обрезаем длинные названия
                name = game['name']
                if len(name) > 18:
                    name = name[:16] + "..."
                ax.text(x_pos + 0.005, text_y,
                        f"• {name}",
                        verticalalignment='top',
                        fontsize=7)
                text_y -= 0.02


def _create_clustering_result(
        data: GamesClusteringData,
        cluster_labels: np.ndarray,
        clusters_info: List[ClusterInfo],
        method: str,
        X_reduced: np.ndarray,
        pca_info: Optional[Dict[str, Any]] = None
) -> ClusteringResult:
    """Создает объект результата кластеризации"""

    unique_clusters = sorted(np.unique(cluster_labels))
    game_assignments = {
        game.app_id: int(cluster_labels[i])
        for i, game in enumerate(data.games)
    }

    # Добавляем информацию о PCA если есть
    values = {
        "total_games": len(data.games),
        "n_clusters": len(unique_clusters),
        "feature_count": len(data.feature_names),
        "features": data.feature_names
    }

    if pca_info:
        values["pca_info"] = {
            "explained_variance": pca_info.get('explained_variance', []),
            "n_original_features": len(pca_info.get('feature_names', []))
        }

    return ClusteringResult(
        clusters=clusters_info,
        game_assignments=game_assignments,
        n_clusters=len(unique_clusters),
        method=method,
        reduced_2d=X_reduced.tolist(),
        values=values,
        ticks=[f"Cluster_{cid}" for cid in unique_clusters]
    )