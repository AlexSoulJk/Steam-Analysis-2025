from steam_analysis.analysis.finalapplication import Application
from steam_analysis.config import examples_statistics_images_path


def main():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_type(15)


def categories():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_category(25)

def main2():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_price(25, type="genre")


def main3():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_price(25, type="genre")


# def categories_count():
#     app = Application(path_to_save_work=examples_statistics_images_path)
#     app.generate_distribution_by_price(type="category")


def release_by_season():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_for_release_by_season("monthly")

def clustering():
    app = Application(path_to_save_work=examples_statistics_images_path)
    # app.generate_game_clustering(method="kmeans", n_clusters=6)
    # app.generate_game_clustering(method="kmeans", auto_select_params=True)
    app.generate_game_clustering(method="kmeans", auto_select_params=True)
    # app.generate_game_clustering(method="dbscan")


if __name__ == "__main__":
    # main()
    # categories()
    # main2()
    main3()
    # categories_count()
    # release_by_season()
    # clustering()
