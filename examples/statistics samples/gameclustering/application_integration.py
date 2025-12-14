from steam_analysis.analysis.finalapplication import Application
from steam_analysis.config import examples_statistics_images_path


def main():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_type(15)


def categories():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_category(25)


def categories_count():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_count_category(15)


def release_by_season():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_for_release_by_season("monthly")

def clustering():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_game_clustering(n_clusters=5, method="kmeans")


if __name__ == "__main__":
    # main()
    # categories()
    # categories_count()
    # release_by_season()
    clustering()
