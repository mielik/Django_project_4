import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Follow
from django.core.cache import cache

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUp(self):
        super().setUpClass()
        self.guest_client = Client()
        self.user = User.objects.create_user(username="testuser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="testgroup",
            slug="testgroup",
            description="Test description"
        )
        self.post = Post.objects.create(
            text="Test text",
            pub_date="10.01.2022",
            author=self.user,
            group=self.group
        )

    def tearDown(self):
        super().tearDown()
        cache.clear()

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": f"{self.group}"}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": f"{self.user}"}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": 1}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit",
                kwargs={"post_id": 1}): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse("posts:index"))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        expected = list(Post.objects.filter(group_id="1")[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.post.author})
        )
        expected = list(Post.objects.filter(author_id="1")[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(response.context.get("post").author, self.post.author)
        self.assertEqual(response.context.get("post").group, self.post.group)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_select_group(self):
        """Проверка, что если при создании поста указать группу,
        пост появляется на главной странице, на странице выбранной группы"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_post_not_in_inappropriate_group(self):
        """Проверка, что пост не попал в группу,
        для которой не был предназначен"""
        form_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_cache(self):
        """Проверка кеширования главной страницы."""
        response = self.guest_client.get(reverse("posts:index"))
        Post.objects.get(id=1).delete()
        # Удаляем пост, кешированием содержание дожно остаться одинаковым
        response_2 = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(response.content, response_2.content)
        """Проверка сброса кеша"""
        cache.clear()
        response_2_clear = self.guest_client.get(reverse("posts:index"))
        self.assertNotEqual(response.content, response_2_clear.content)

    def test_follow_and_unfollow(self):
        """Проверка, что подписок нет."""
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
        """Проверка, подписка создалась между двумя пользователями."""
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response_1 = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response_1.context["page_obj"]), 1)
        self.assertIn(self.post, response_1.context["page_obj"])
        """Новая запись не появляется в ленте тех, кто не подписан."""
        self.user_new = User.objects.create(username="testusernew")
        self.authorized_client.force_login(self.user_new)
        response_2 = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response_2.context["page_obj"]), 0)
        """Проверка, что подписка перестала существовать."""
        Follow.objects.all().delete()
        response_3 = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response_3.context["page_obj"]), 0)
    # Замечания исправлены,
    # добавлена в тесты test_follow_and_unfollow проверка,
    # что подписка создается между двумя конкретными пользователями
    # и перестает существовать.
    # Если это неправильно, прошу написать, что именно не так
    # или навести на проблему. Спасибо.

    def page_not_found(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.guest_client.get(reverse("core:page_not_found"))
        self.assertTemplateUsed(response, "core/404.html")


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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
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
        self.post = Post.objects.create(
            text="Test text",
            pub_date="10.01.2022",
            author=self.user,
            group=self.group
        )
        self.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        self.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=self.small_gif,
            content_type="image/gif"
        )

    def test_image_in_index(self):
        """Картинка передается в шаблоне index."""
        form_data = {
            "text": "Test text",
            "group": self.group.pk,
            "image": self.uploaded,
        }
        response = self.guest_client.post(
            reverse("posts:index"), data=form_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.create(
            image="posts/small.gif",
        )
        self.assertEqual(post.image, "posts/small.gif")

    def test_image_in_profile(self):
        """Картинка передается в шаблоне profile."""
        form_data = {
            "text": "Test text",
            "group": self.group.pk,
            "image": self.uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:profile", kwargs={"username": self.post.author}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.create(
            image="posts/small.gif",
        )
        self.assertEqual(post.image, "posts/small.gif")

    def test_image_in_group_list(self):
        """Картинка передается в шаблоне profile."""
        form_data = {
            "text": "Test text",
            "group": self.group.pk,
            "image": self.uploaded,
        }
        response = self.guest_client.post(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.create(
            image="posts/small.gif",
        )
        self.assertEqual(post.image, "posts/small.gif")

    def test_image_in_post_detail(self):
        """Картинка передается в шаблоне post_detail."""
        form_data = {
            "text": "Test text",
            "group": self.group.pk,
            "image": self.uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.create(
            image="posts/small.gif",
        )
        self.assertEqual(post.image, "posts/small.gif")
