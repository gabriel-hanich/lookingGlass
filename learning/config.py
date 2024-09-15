import json

def load_config():
    with open("./settings.json", "r") as configFile:
        return json.load(configFile)
    
def save_config(data):
    with open("./settings.json", "w") as configFile:
        json.dump(data, configFile)