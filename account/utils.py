from ecommerce_api.utils.file_handling import upload_to_unique


def profile_upload_to_unique(instance, filename):
    """
    Generate a unique file name for the profile image.
    :param instance:
    :param filename:
    :return:
    """
    return upload_to_unique(instance, filename, directory="profiles/")