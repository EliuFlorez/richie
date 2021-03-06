"""
End-to-end tests for the course detail view
"""
import random
from datetime import datetime
from unittest import mock

from cms.test_utils.testcases import CMSTestCase

from richie.apps.core.factories import UserFactory
from richie.apps.courses.factories import (
    CategoryFactory,
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
)
from richie.apps.courses.models import CourseRun, CourseState


class CourseCMSTestCase(CMSTestCase):
    """
    End-to-end test suite to validate the content and Ux of the course detail view

    It's worth to notice related draft items (Person, Organization) are only
    displayed on a draft course page so admin can preview them. But draft items are
    hidden from published page so common users can not see them.
    """

    def test_templates_course_detail_cms_published_content(self):
        """
        Validate that the important elements are displayed on a published course page
        """
        categories = CategoryFactory.create_batch(4)
        organizations = OrganizationFactory.create_batch(4)

        course = CourseFactory(
            page_title="Very interesting course",
            fill_organizations=organizations,
            fill_categories=categories,
        )
        page = course.extended_object
        course_run1, _course_run2 = CourseRunFactory.create_batch(
            2, page_parent=course.extended_object, languages=["en", "fr"]
        )
        self.assertFalse(course_run1.extended_object.publish("en"))

        # Publish only 2 out of 4 categories and 2 out of 4 organizations
        categories[0].extended_object.publish("en")
        categories[1].extended_object.publish("en")
        organizations[0].extended_object.publish("en")
        organizations[1].extended_object.publish("en")

        # The unpublished objects may have been published and unpublished which puts them in a
        # status different from objects that have never been published.
        # We want to test both cases.
        categories[2].extended_object.publish("en")
        categories[2].extended_object.unpublish("en")
        organizations[2].extended_object.publish("en")
        organizations[2].extended_object.unpublish("en")

        # The page should not be visible before it is published
        url = page.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Publish and ensure content is correct
        page.publish("en")

        # Now we can publish children course runs: publish only 1 of the 2
        course_run1.extended_object.parent_page.refresh_from_db()
        self.assertTrue(course_run1.extended_object.publish("en"))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response, "<title>Very interesting course</title>", html=True
        )
        self.assertContains(
            response,
            '<h1 class="course-detail__content__title">Very interesting course</h1>',
            html=True,
        )

        # Only published categories should be present on the page
        for category in categories[:2]:
            self.assertContains(
                response,
                '<a class="category-plugin-tag" href="{:s}">{:s}</a>'.format(
                    category.extended_object.get_absolute_url(),
                    category.extended_object.get_title(),
                ),
                html=True,
            )
        for category in categories[-2:]:
            self.assertNotContains(response, category.extended_object.get_title())

        # Public organizations should be in response content
        for organization in organizations[:2]:
            self.assertContains(
                response,
                '<div class="organization-plugin__title">{title:s}</div>'.format(
                    title=organization.extended_object.get_title()
                ),
                html=True,
            )

        # Draft organizations should not be in response content
        for organization in organizations[-2:]:
            self.assertNotContains(
                response, organization.extended_object.get_title(), html=True
            )

        # Only the published course run should be in response content
        self.assertContains(response, "<dd>English and french</dd>", html=True, count=1)

    def test_templates_course_detail_cms_draft_content(self):
        """
        A staff user should see a draft course including its draft elements with
        an annotation
        """
        user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=user.username, password="password")

        categories = CategoryFactory.create_batch(4)
        organizations = OrganizationFactory.create_batch(4)

        course = CourseFactory(
            page_title="Very interesting course",
            fill_organizations=organizations,
            fill_categories=categories,
        )
        page = course.extended_object
        course_run1, _course_run2 = CourseRunFactory.create_batch(
            2, page_parent=course.extended_object, languages=["en", "fr"]
        )

        # Publish only 1 of the course runs
        course_run1.extended_object.publish("en")

        # Publish only 2 out of 4 categories and 2 out of 4 organizations
        categories[0].extended_object.publish("en")
        categories[1].extended_object.publish("en")
        organizations[0].extended_object.publish("en")
        organizations[1].extended_object.publish("en")

        # The unpublished objects may have been published and unpublished which puts them in a
        # status different from objects that have never been published.
        # We want to test both cases.
        categories[2].extended_object.publish("en")
        categories[2].extended_object.unpublish("en")
        organizations[2].extended_object.publish("en")
        organizations[2].extended_object.unpublish("en")

        # The page should be visible as draft to the staff user
        url = page.get_absolute_url()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response, "<title>Very interesting course</title>", html=True
        )
        self.assertContains(
            response,
            '<h1 class="course-detail__content__title">Very interesting course</h1>',
            html=True,
        )

        # Draft and public organizations should all be present on the page
        for organization in organizations:
            self.assertContains(
                response,
                '<div class="organization-plugin__title">{title:s}</div>'.format(
                    title=organization.extended_object.get_title()
                ),
                html=True,
            )

        # Draft organizations should be annotated for styling
        self.assertContains(response, "organization-plugin-container--draft", count=2)

        # The published categories should be present on the page
        for category in categories[:2]:
            self.assertContains(
                response,
                '<a class="category-plugin-tag" href="{:s}">{:s}</a>'.format(
                    category.extended_object.get_absolute_url(),
                    category.extended_object.get_title(),
                ),
                html=True,
            )
        # Draft categories should also be present on the page with an annotation for styling
        for category in categories[-2:]:
            self.assertContains(
                response,
                '<a class="{element:s} {element:s}--draft" href="{url:s}">{title:s}</a>'.format(
                    url=category.extended_object.get_absolute_url(),
                    element="category-plugin-tag",
                    title=category.extended_object.get_title(),
                ),
                html=True,
            )
        # The draft and the published course runs should both be in the page
        self.assertContains(response, "<dd>English and french</dd>", html=True, count=2)

    def test_templates_course_detail_no_index(self):
        """
        A course snapshot page should not be indexable by search engine robots.
        """
        course = CourseFactory(should_publish=True)
        url = course.extended_object.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<meta name="robots" content="noindex">')

        snapshot = CourseFactory(
            page_parent=course.extended_object, should_publish=True
        )
        url = snapshot.extended_object.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="robots" content="noindex">')

    def prepare_to_test_state(self, state):
        """
        Not a test.
        Create objects and mock to help testing the impact of the state on template rendering.
        """
        course = CourseFactory(page_title="my course", should_publish=True)
        CourseRunFactory(
            page_parent=course.extended_object,
            page_title="my course run",
            should_publish=True,
        )

        url = course.extended_object.get_absolute_url()
        with mock.patch.object(
            CourseRun, "state", new_callable=mock.PropertyMock, return_value=state
        ):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        return response

    def test_templates_course_detail_state_with_cta(self):
        """A course run in a state with a call to action should include a link and the CTA."""
        response = self.prepare_to_test_state(
            CourseState(
                random.randint(0, 6),
                "state cta",
                random.choice(["state text", None]),
                random.choice([datetime.now(), None]),
            )
        )
        self.assertContains(
            response,
            '<a class="course-detail__aside__run__block__cta" '
            'href="/en/my-course/my-course-run/">State cta</a>',
            html=True,
        )

    def test_templates_course_detail_state_without_cta(self):
        """A course run in a state without a call to action should include a state button."""
        response = self.prepare_to_test_state(
            CourseState(
                random.randint(0, 6),
                None,
                "state text",
                random.choice([datetime.now(), None]),
            )
        )
        self.assertContains(
            response,
            '<a class="course-detail__aside__run__block__cta '
            'course-detail__aside__run__block__cta--projected" '
            'href="/en/my-course/my-course-run/">State text</a>',
            html=True,
        )
