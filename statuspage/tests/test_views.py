from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

from .. import views


class RegisterViewTestCase(TestCase):
    """Register a new user."""

    def setUp(self):
        self.url = reverse('register')
        self.factory = RequestFactory()
        self.view = views.RegistrationView.as_view()
        self.User = get_user_model()

    def get_valid_data(self):
        return {
            'username': 'test',
            'password1': 'test',
            'password2': 'test',
        }

    def test_render_form(self):
        """Get page and render the registration form."""
        with self.assertTemplateUsed('register.html'):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        """Create a new user with the registration form."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.session = MagicMock()
        self.view(request)
        user = self.User.objects.latest('pk')
        self.assertEqual(user.username, 'test')
        self.assertTrue(user.check_password('test'))

    def test_login_user(self):
        """New user should be logged in after registering."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.session = MagicMock()
        with patch('statuspage.views.login') as mock_login:
            response = self.view(request)
            user = self.User.objects.latest('pk')
            mock_login.assert_called_with(request, user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], settings.LOGIN_REDIRECT_URL)

    def test_existing_user(self):
        """Handle registering username which already exists."""
        self.User.objects.create_user(username='test')
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        response = self.view(request)
        self.assertContains(response, 'A user with that username already exists.')

    def test_mismatched_passwords(self):
        """Two password fields must match."""
        data = self.get_valid_data()
        data['password1'] = 'abc123'
        data['password2'] = '123abc'
        request = self.factory.post(self.url, data=data)
        response = self.view(request)
        self.assertContains(response, 'The two password fields didn&#39;t match.')
