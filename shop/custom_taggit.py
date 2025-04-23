from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from taggit.models import GenericTaggedItemBase, TagBase


class CustomTag(TagBase):
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class CustomTaggedItem(GenericTaggedItemBase):
    # Override the object_id field from the default IntegerField to a UUIDField.
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    tag = models.ForeignKey(
        CustomTag,
        related_name="custom_tagged_items",
        on_delete=models.CASCADE,
    )
