import requests

MODS_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/Mods.json"
SECONDARIES_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/Secondary.json"


class DataHandler:
    @staticmethod
    def get_json_cached(url: str):
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def get_mods_data():
        return DataHandler.get_json_cached(MODS_URL)
    
    @staticmethod
    def get_weapon_data():
        return DataHandler.get_json_cached(SECONDARIES_URL)