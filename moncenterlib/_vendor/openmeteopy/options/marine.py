from moncenterlib._vendor.openmeteopy.utils.constants import *
from moncenterlib._vendor.openmeteopy.utils.timezones import *
from moncenterlib._vendor.openmeteopy.options.forecast import ForecastOptions


class MarineOptions(ForecastOptions):
    API_PATH = "https://marine-api.open-meteo.com/v1/marine?"

    def get_api_path(self):
        return self.API_PATH

    pass
