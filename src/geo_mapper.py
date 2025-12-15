from distribution.utils.constans import DATAWRAPPER_MAP
from steam_analysis.core.schemas.analysis.geoshemas import ListGeoItems


class GeoRemapper:
    @staticmethod
    def convert_for_datawrapper(collection: ListGeoItems):
        data = collection.data

        for item in data:
            new_key = DATAWRAPPER_MAP.get(item.country_code, None)
            if new_key:
                item.country_code = new_key

        collection.data = data
        return collection