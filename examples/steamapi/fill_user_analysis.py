from examples.steamapi.utils import load_api_key
from steam_analysis.app.application import AppMediator

PROCESSOR_NAME = ["AlexSoulJK",
                  "Ekaterina Lips",
                  "Lo-Lap",
                  "baru1ina"]
def main():
    api_key = load_api_key()

    for i in range(1000):
        app = AppMediator(steam_api_key=api_key, processor_name=PROCESSOR_NAME[(i//30) % 4])
        app.fill_analysis_user()

if __name__ == "__main__":
    main()
