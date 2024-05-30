#!/usr/bin/env python3
from aws_cdk import App

from common_constructs.stack import StandardTags
from stacks.persistent_stack import PersistentStack


class LicensureApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        environment_name = self.node.get_context('environment_name')
        tags = self.node.get_context('tags')

        self.persistent_stack = PersistentStack(
            self, "BackendStack",
            standard_tags=StandardTags(
                **tags,
                environment=environment_name
            ),
            environment_name=environment_name
        )


if __name__ == '__main__':
    app = LicensureApp()
    app.synth()
