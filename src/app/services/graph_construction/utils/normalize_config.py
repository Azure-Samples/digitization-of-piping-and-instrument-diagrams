def normalize_pixel_config_value(config_in_pixels: int, image_width: int, image_height: int) -> float:
    '''Denormalizes the config value in pixels to the actual value in the image.

    :param config_in_pixels: The config value in pixels
    :type config_in_pixels: int
    :param image_width: The image width in pixels
    :type image_width: int
    :param image_height: The image height in pixels
    :type image_height: int
    :return: The normalized config value
    :rtype: float
    '''

    return config_in_pixels / max(image_width, image_height)
