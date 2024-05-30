from constructs import Construct

from common_constructs.stack import Stack
from stacks.api_stack.license_api import LicenseApi


class ApiStack(Stack):
    def __init__(
            self, scope: Construct, construct_id: str, *,
            environment_name: str,
            **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)
        self.license_api = LicenseApi(
            self, 'LicenseApi',
            environment_name=environment_name
        )
