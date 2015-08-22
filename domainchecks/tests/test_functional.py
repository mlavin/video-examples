import shutil
import unittest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver

from . import factories


@unittest.skipUnless(shutil.which('phantomjs'), 'PhantomJS is not installed.')
class BrowserTestCase(StaticLiveServerTestCase):
    """Functional user tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = factories.create_user(password='test')
        self.domain = factories.create_domain(owner=self.user)
        self.check = factories.create_domain_check(domain=self.domain)
        self.login(self.user.username, 'test')

    def tearDown(self):
        self.logout()

    def get(self, url):
        self.browser.get('%s%s' % (self.live_server_url, url))

    def login(self, username, password):
        """Navigate to login page and login."""
        self.get('/login/')
        self.browser.find_element_by_name('username').send_keys(username)
        self.browser.find_element_by_name('password').send_keys(password)
        self.browser.find_element_by_tag_name('form').submit()

    def logout(self):
        """Logout current user."""
        self.get('/logout/')

    def test_view_domains(self):
        """Login and view user's domains."""
        self.get('/')
        domain = self.browser.find_element_by_class_name('domain')
        name = domain.find_element_by_class_name('name')
        self.assertEqual(name.text, self.domain.name)

    def test_view_domain_detail(self):
        """View the status detail for a single domain."""
        self.get('/domains/{}/'.format(self.domain.name))
        title = self.browser.find_element_by_tag_name('h1')
        self.assertEqual(title.text, self.domain.name)
        check = self.browser.find_element_by_class_name('check')
        name = check.find_element_by_class_name('name')
        expected = '{protocol} {method} {path}'.format(
            protocol=self.check.get_protocol_display(),
            method=self.check.get_method_display(),
            path=self.check.path)
        self.assertEqual(name.text, expected)

    def test_add_domain(self):
        """Create a new domain for this user."""
        self.get('/domains/add/')
        form = self.browser.find_element_by_tag_name('form')
        form.find_element_by_name('name').send_keys('new.com')
        form.find_element_by_name('checks-0-path').send_keys('/')
        form.submit()
        title = self.browser.find_element_by_tag_name('h1')
        self.assertEqual(title.text, 'new.com')

    def test_edit_domain(self):
        """Edit a domain for this user."""
        self.get('/domains/{}/edit/'.format(self.domain.name))
        form = self.browser.find_element_by_tag_name('form')
        name = form.find_element_by_name('name')
        name.clear()
        name.send_keys('edit.com')
        form.submit()
        title = self.browser.find_element_by_tag_name('h1')
        self.assertEqual(title.text, 'edit.com')

    def test_change_password(self):
        """Change user's password."""
        self.get('/password/change/'.format(self.domain.name))
        form = self.browser.find_element_by_tag_name('form')
        form.find_element_by_name('old_password').send_keys('test')
        form.find_element_by_name('new_password1').send_keys('newpassword')
        form.find_element_by_name('new_password2').send_keys('newpassword')
        form.submit()
        message = self.browser.find_element_by_class_name('message')
        self.assertEqual(message.text, 'Your password was successfully changed.')
