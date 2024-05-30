from aws_cdk import RemovalPolicy
from aws_cdk.aws_kms import Key
from constructs import Construct

from common_constructs.stack import Stack
from stacks.persistent_stack.table import LicenseDataTable


class PersistentStack(Stack):
    """
    The stack that holds long-lived resources such as license data and other things that should probably never
    be destroyed in production
    """

    def __init__(
            self, scope: Construct, construct_id: str, *,
            environment_name: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # If we delete this stack, retain the resource (orphan but prevent data loss) or destroy it (clean up)?
        removal_policy = RemovalPolicy.RETAIN if environment_name == 'prod' else RemovalPolicy.DESTROY

        self.shared_encryption_key = Key(
            self, 'SharedEncryptionKey',
            enable_key_rotation=True,
            alias=f'{self.stack_name}-shared-encryption-key'
        )

        self.license_table = LicenseDataTable(
            self, 'LicenseTable',
            environment_name=environment_name,
            encryption_key=self.shared_encryption_key,
            removal_policy=removal_policy
        )
