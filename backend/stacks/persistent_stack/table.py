from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk.aws_backup import BackupPlan, BackupPlanRule, BackupResource, BackupVault
from aws_cdk.aws_dynamodb import Table, BillingMode, Attribute, AttributeType, TableEncryption
from aws_cdk.aws_events import Schedule
from aws_cdk.aws_iam import ServicePrincipal
from aws_cdk.aws_kms import IKey
from cdk_nag import NagSuppressions
from constructs import Construct


class LicenseDataTable(Table):
    def __init__(
            self, scope: Construct, id: str, *,
            environment_name: str,
            encryption_key: IKey,
            removal_policy: RemovalPolicy,
            **kwargs
    ):
        dynamo_principal = ServicePrincipal('dynamodb.amazonaws.com')
        encryption_key.grant_encrypt_decrypt(dynamo_principal)

        super().__init__(
            scope, id,
            encryption=TableEncryption.CUSTOMER_MANAGED,
            encryption_key=encryption_key,
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=True,
            partition_key=Attribute(name='pk', type=AttributeType.STRING),
            sort_key=Attribute(name='sk', type=AttributeType.STRING),
            time_to_live_attribute='ttl',
            **kwargs
        )

        backup_vault = BackupVault(
            self, 'BackupVault',
            # CloudFormation requires that you specifically provide a resource name
            # for a BackupVault, even though CFn does not handle resources with forced names well.
            # CDK will accommodate this by providing a 'unique' name to CFn, but then we don't
            # control the name and CFn will refuse to deploy if we need to replace this resource
            # due to a configuration change. Instead of leaving it to CDK, we will specifically
            # name this resource, so we can add a '-2' or something to the name next time we
            # need to recreate it.
            backup_vault_name=f'{self.node.path}-{environment_name}'.replace('/', '-'),
            encryption_key=encryption_key,
            removal_policy=removal_policy
        )

        backup_plan = BackupPlan(
            self, 'BackupPlan',
            backup_vault=backup_vault,
            backup_plan_rules=[BackupPlanRule(
                schedule_expression=Schedule.cron(
                    hour='0',
                    minute='0',
                    week_day='7',
                    month='*',
                    year='*'
                ),
                move_to_cold_storage_after=Duration.days(30),
                delete_after=Duration.days(365)
            )]
        )
        backup_selection = backup_plan.add_selection(
            'WeeklyBackups',
            resources=[BackupResource.from_dynamo_db_table(self)]
        )
        encryption_key.grant_encrypt_decrypt(backup_selection)
        self.grant_read_data(backup_selection)

        NagSuppressions.add_resource_suppressions(
            backup_selection.grant_principal,
            suppressions=[
                {
                    'id': 'AwsSolutions-IAM4',
                    'applies_to': [
                        'Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup'
                    ],
                    'reason': 'This policy is suitable for our purposes'
                },
            ]
        )
        NagSuppressions.add_resource_suppressions_by_path(
            Stack.of(self),
            f'{backup_selection.node.path}/Role/DefaultPolicy/Resource',
            suppressions=[{
                'id': 'AwsSolutions-IAM5',
                'applies_to': [
                    'Action::kms:GenerateDataKey*',
                    'Action::kms:ReEncrypt:*'
                ],
                'reason': 'These wild-carded actions are scoped specifically to the KMS key this resource needs to'
                          ' be able to decrypt, so no additional access is granted beyond what is required.'
            }]
        )
