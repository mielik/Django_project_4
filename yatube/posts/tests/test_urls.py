from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="testuser")
        self.user_notauthor = User.objects.create_user(username="notauthor")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title="testgroup", slug="testgroup")
        self.post = Post.objects.create(text="hfhf", author=self.user)
        self.post_notauthor = Post.objects.create(
            text="hfhfh", author=self.user_notauthor
        )

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get(f"/group/{self.group}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_url_exists_at_desired_location(self):
        """Страница /profile/<username>/ доступна любому пользователю."""
        response = self.guest_client.get(f"/profile/{self.user}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_exists_at_desired_location(self):
        """Страница /posts/<post_id>/ доступна любому пользователю."""
        response = self.guest_client.get(f"/posts/{self.post.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ доступна любому пользователю."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем редирект edit для неавторизованного пользователя
    def test_edit_url_redirect_anonymous(self):
        """Страница /posts/<int:post_id>/edit/
        перенаправляет анонимного пользователя."""
        response = self.guest_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Проверяем редирект edit для авторизованного пользователя
    def test_edit_url_redirect_anonymous(self):
        """Страница /posts/<int:post_id>/edit/
        перенаправляет авторизованного пользователя."""
        response = self.authorized_client.get(
            f"/posts/{self.post_notauthor.pk}/edit/"
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Проверяем доступность страницы edit для автора
    def test_posts_post_id_edit_url_exists_at_desired_location(self):
        """Страница /posts/<int:post_id>/edit/ доступна автора."""
        response = self.authorized_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group}/": "posts/group_list.html",
            f"/profile/{self.user}/": "posts/profile.html",
            f"/posts/{self.post.pk}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
