from aws_cdk import CfnOutput, Duration
from aws_cdk.aws_cognito import UserPool, UserPoolEmail, AccountRecovery, AutoVerifiedAttrs, AdvancedSecurityMode, \
    DeviceTracking, Mfa, MfaSecondFactor, PasswordPolicy, StandardAttributes, StandardAttribute, StringAttribute, \
    CognitoDomainOptions, AuthFlow, OAuthSettings, OAuthFlows, ClientAttributes, ResourceServerScope
from aws_cdk.aws_kms import IKey
from cdk_nag import NagSuppressions
from constructs import Construct


class BoardUsers(UserPool):
    def __init__(
            self, scope: Construct, construct_id: str, *,
            cognito_domain_prefix: str,
            environment_name: str,
            compact_context: dict,
            encryption_key: IKey,
            removal_policy,
            **kwargs
    ):
        super().__init__(
            scope, construct_id,
            removal_policy=removal_policy,
            deletion_protection=False,
            email=UserPoolEmail.with_cognito(),
            # user_invitation=UserInvitationConfig(...),
            account_recovery=AccountRecovery.EMAIL_ONLY,
            auto_verify=AutoVerifiedAttrs(email=True),
            advanced_security_mode=AdvancedSecurityMode.ENFORCED,
            custom_sender_kms_key=encryption_key,
            device_tracking=DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True
            ),
            mfa=Mfa.REQUIRED if environment_name in ('prod', 'test') else Mfa.OPTIONAL,
            mfa_second_factor=MfaSecondFactor(otp=True, sms=False),
            password_policy=PasswordPolicy(
                min_length=12,
                require_digits=True,
                require_symbols=True,
                require_lowercase=True,
                require_uppercase=True
            ),
            self_sign_up_enabled=False,
            sign_in_aliases=None,
            sign_in_case_sensitive=False,
            standard_attributes=StandardAttributes(
                email=StandardAttribute(
                    mutable=False,
                    required=True
                )
            ),
            custom_attributes={
                'jurisdiction': StringAttribute(
                    min_len=4,
                    max_len=60,
                    mutable=False
                )
            },
            **kwargs
        )
        if environment_name not in ('prod', 'test'):
            NagSuppressions.add_resource_suppressions(
                self,
                suppressions=[
                    {
                        'id': 'AwsSolutions-COG2',
                        'reason': 'MFA is not necessary in the sandboxes/dev environment as there is '
                                  'no real user data to protect'
                    }
                ]
            )

        self.add_domain(
            'APIDomain',
            cognito_domain=CognitoDomainOptions(
                domain_prefix=cognito_domain_prefix
            )
        )

        CfnOutput(self, 'UserPoolId', value=self.user_pool_id)

        self.scopes = {
            jurisdiction: ResourceServerScope(
                scope_name=jurisdiction,
                scope_description=f'Write access for {jurisdiction}'
            )
            for jurisdiction in compact_context['jurisdictions']
        }
        self.add_resource_server(
            'LicenseData',
            identifier='license-data',
            scopes=list(self.scopes.values())
        )

        self.user_pool_client = self.add_client(
            'UIClient',
            auth_flows=AuthFlow(
                admin_user_password=True,
                custom=False,
                user_srp=False,
                user_password=False
            ),
            o_auth=OAuthSettings(
                callback_urls=[
                    'http://localhost:8000/auth'
                ],
                flows=OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False
                )
            ),
            access_token_validity=Duration.minutes(60),
            auth_session_validity=Duration.minutes(3),
            enable_token_revocation=True,
            generate_secret=False,
            refresh_token_validity=Duration.days(30),
            # If you provide no attributes at all here, it will default
            # to making _all_ attributes writeable, so if we want to limit writes,
            # we have to provide at least _one_ that the client _can_ write.
            write_attributes=ClientAttributes().with_standard_attributes(email=True),
            read_attributes=ClientAttributes().with_custom_attributes('jurisdiction')
        )

        # We will create some admins to get access started for the app and for support
        # for email in compact_context.get('admins', []):
        #     user = CfnUserPoolUser(
        #         self, f'Admin{email}',
        #         user_pool_id=self.user_pool_id,
        #         username=email,
        #         user_attributes=[
        #             CfnUserPoolUser.AttributeTypeProperty(
        #                 name='email',
        #                 value=email
        #             ),
        #             CfnUserPoolUser.AttributeTypeProperty(
        #                 name='custom:jurisdiction',
        #                 value='colorado'
        #             )
        #         ],
        #         desired_delivery_mediums=['EMAIL']
        #     )
        #     user.add_dependency(self.node.default_child)
