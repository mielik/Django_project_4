from django.contrib.auth import get_user_model
from django.db import models
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Title of the group',
                             help_text='Дайте название группе до 200 символов')
    slug = models.SlugField(unique=True,
                            verbose_name='URL label',
                            help_text='Название URL')
    description = models.TextField(verbose_name='Description',
                                   help_text='Опишите группу')

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Text',
                            help_text='Напишите текст для своего поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Publication date',
        help_text='Выберите дату публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, null=True,
        related_name='posts',
        verbose_name='Author',
        help_text='Укажите автора поста',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Group',
        help_text='Укажите группу, к которой будет принадлежать пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self) -> str:
        return (self.text)[:15]

    class Meta:
        ordering = ['-pub_date', ]
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(CreatedModel):
    text = models.TextField(verbose_name='Text',
                            help_text='Напишите текст')
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, null=True,
        related_name='comments',
        verbose_name='Author',
        help_text='Укажите автора',
    )
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Post',
        help_text='Укажите пост, к которой будет принадлежать',
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique follower')
        ]
