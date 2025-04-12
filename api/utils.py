import os
import uuid


def upload_to_uniqe(instance, filename, directory):
    ext = filename.split('.')[-1]
    return os.path.join(f"{directory}/", f"{uuid.uuid4()}.{ext}")


def product_upload_to_unique(instance, filename):
    """
    Generate a unique file name for the product image.
    :param instance:
    :param filename:
    :return:
    """
    return upload_to_uniqe(instance, filename, directory="products/")

def profile_upload_to_unique(instance, filename):
    """
    Generate a unique file name for the profile image.
    :param instance:
    :param filename:
    :return:
    """
    return upload_to_uniqe(instance, filename, directory="profiles/")