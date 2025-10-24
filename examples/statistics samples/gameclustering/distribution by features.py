from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.config import examples_statistics_images_path


def generate_distribution_by_feature(data, title_name,
                                     features_name,
                                     path_to_save) -> None:
    return


def main():
    dir_to_save = fr"{examples_statistics_images_path}gameclustering"
    pdp = ProcessedDataProvider()

    distribution, genres_name = pdp.get_games_by_genres()
    generate_distribution_by_feature(data=distribution,
                                     features_name=genres_name,
                                     title_name="жанрам",
                                     path_to_save=fr"{dir_to_save}/distribution_by_genres.png")

    distribution, categories_name = pdp.get_games_by_categories()
    generate_distribution_by_feature(data=distribution,
                                     features_name=categories_name,
                                     title_name="категориям",
                                     path_to_save=fr"{dir_to_save}/distribution_by_categories.png")
    pass
