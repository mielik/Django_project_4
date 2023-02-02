import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post, Comment

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.create(
            text=" текст",
            author=User.objects.create(username="testuser"),
            group=Group.objects.create(
                title="testgroup",
                slug="testgroup",
                description="testdescription"
            ),
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование,
        # перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="testuser2")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="testgroup2",
            slug="testgroup2",
            description="testdescription2"
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Test text",
            "group": self.group.pk,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse(
                "posts:profile", kwargs={"username": self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Test text", image="posts/small.gif").exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        new_post = Post.objects.first()
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post"""
        self.post = Post.objects.create(
            author=self.user, text="Test text", group=self.group
        )
        self.other_group = Group.objects.create(
            title="Title text",
            slug="text-slug",
            description="Text description",
        )
        form_data = {"text": "New test text", "group": self.other_group.pk}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text="New test text",
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        old_group_response = self.authorized_client.get(
            reverse("posts:group_list", args=(self.group.slug,))
        )
        self.assertEqual(
            old_group_response.context["page_obj"].paginator.count, 0
        )

    def test_comment(self):
        """Валидная форма добавляет комментарий к посту."""
        self.post = Post.objects.create(
            author=self.user, text="Test text", group=self.group
        )
        comment_count = Comment.objects.count()
        form_data = {"text": "Test text"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            )
        )
        self.assertTrue(
            Comment.objects.filter(
                text="Test text",
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
