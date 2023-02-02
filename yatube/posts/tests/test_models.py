from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост, который содержит больше 15 символов",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        vals = ((str(post), post.text[:15]), (str(group), group.title))
        for value, expected in vals:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name_post(self):
        """verbose_name в полях post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses_post = {
            "text": "Text",
            "pub_date": "Publication date",
            "author": "Author",
            "group": "Group",
        }
        for field, expected_value in field_verboses_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_verbose_name_group(self):
        """verbose_name в полях group совпадает с ожидаемым."""
        group = PostModelTest.group
        field_verboses_group = {
            "title": "Title of the group",
            "slug": "URL label",
            "description": "Description",
        }
        for field, expected_value in field_verboses_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text_post(self):
        """help_text в полях post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            "text": "Напишите текст для своего поста",
            "pub_date": "Выберите дату публикации",
            "author": "Укажите автора поста",
            "group": "Укажите группу, к которой будет принадлежать пост",
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_help_text_group(self):
        """help_text в полях group совпадает с ожидаемым."""
        group = PostModelTest.group
        field_help_texts = {
            "title": "Дайте название группе до 200 символов",
            "slug": "Название URL",
            "description": "Опишите группу",
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value
                )
