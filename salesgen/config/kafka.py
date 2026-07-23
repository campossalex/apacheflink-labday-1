import configparser


def get_configs():
    config = configparser.ConfigParser()
    config.read("configuration/configuration.ini")

    bootstrap_servers = config["KAFKA"]["bootstrap_servers"]

    configs = {"bootstrap_servers": bootstrap_servers}

    return configs
