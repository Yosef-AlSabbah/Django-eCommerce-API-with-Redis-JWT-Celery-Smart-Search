import os
import uuid


def upload_to_unique(instance, filename, directory):
    ext = filename.split('.')[-1]
    return os.path.join(f"{directory}/", f"{uuid.uuid4()}.{ext}")