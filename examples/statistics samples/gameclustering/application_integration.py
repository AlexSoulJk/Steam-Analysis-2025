from steam_analysis.analysis.finalapplication import Application
from steam_analysis.config import examples_statistics_images_path


def main():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_type()


def categories():
    app = Application(path_to_save_work=examples_statistics_images_path)
    app.generate_distribution_by_category(15)

if __name__ == "__main__":
    categories()