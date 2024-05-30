import json
from unittest import TestCase

from aws_cdk import Stack
from aws_cdk.assertions import Annotations, Match

# import aws_cdk.assertions as assertions

from app import LicensureApp


class TestLicensureApp(TestCase):
    def test_synth(self):
        with open('cdk.json', 'r') as f:
            context = json.load(f)['context']
        with open('cdk.context.example.json', 'r') as f:
            context.update(json.load(f))
        app = LicensureApp(context=context)

        # Identify any findings from our AwsSolutions or HIPAASecurity rule sets
        self._check_no_annotations(app.persistent_stack)
        self._check_no_annotations(app.api_stack)

        # template = assertions.Template.from_stack(app.backend_stack)

    def _check_no_annotations(self, stack: Stack):
        errors = Annotations.from_stack(stack).find_error(
            '*',
            Match.string_like_regexp('.*')
        )
        self.assertEqual(0,
                         len(errors),
                         msg='\n'.join((f'{err.id}: {err.entry.data.strip()}' for err in errors)))

        warnings = Annotations.from_stack(stack).find_warning(
            '*',
            Match.string_like_regexp('.*')
        )
        self.assertEqual(0,
                         len(warnings),
                         msg='\n'.join((f'{warn.id}: {warn.entry.data.strip()}' for warn in warnings)))
