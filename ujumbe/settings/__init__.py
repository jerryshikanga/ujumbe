import logging

def get_boolean_value_from_config(config_value : str=None):
    """Checks if value is 1 returns true, if zero returns false else raises value error"""
    if config_value is None: raise ValueError
    if not isinstance(config_value, int):
        config_value = int(config_value)
    if config_value == 1:
        return True
    elif config_value == 0:
        return False
    else:
        raise ValueError("Unexpected value. Only are 0 and 1 are valids")


def check_if_config_dict_exists(value_key : str = None, config_dict : dict = None):
    if config_dict is None or value_key is None:
        message = "No {} setting found".format(value_key)
        logging.error(message)
        raise KeyError(message)
