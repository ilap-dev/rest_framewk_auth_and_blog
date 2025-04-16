from django.test import TestCase

from backend.apps.blog.models import Category


# Create your tests here.

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            title="Techonology",
            description="All About Technology",
            slug="tech"
        )

    def test_category_creation(self):
        self.assertEqual(str(self.category), 'Tech')
        self.assertEqual(self.category.title, 'Tech')
