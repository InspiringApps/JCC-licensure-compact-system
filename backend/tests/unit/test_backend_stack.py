from unittest import TestCase
# import aws_cdk.assertions as assertions

from app import LicensureApp


class TestLicensureApp(TestCase):
    def test_sqs_queue_created(self):
        LicensureApp()
        # template = assertions.Template.from_stack(app.backend_stack)
