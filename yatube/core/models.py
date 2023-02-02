from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель."""
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Publication date',
        help_text='Выберите дату публикации',
    )
    text = models.TextField(verbose_name='Text',
                            help_text='Напишите текст')

    class Meta:
        # Это абстрактная модель:
        abstract = True
