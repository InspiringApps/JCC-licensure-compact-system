#!/usr/bin/env python3
from aws_cdk import App

from backend.backend_stack import BackendStack


class LicensureApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_stack = BackendStack(self, "BackendStack")


if __name__ == '__main__':
    app = LicensureApp()
    app.synth()
