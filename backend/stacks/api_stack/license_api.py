import json
from functools import cached_property

from aws_cdk.aws_apigateway import RestApi, StageOptions, MethodLoggingLevel, MockIntegration, IntegrationResponse, \
    LogGroupLogDestination, AccessLogFormat, AuthorizationType, MethodResponse, MethodOptions, Resource, \
    JsonSchema, JsonSchemaType, ResponseType, CorsOptions, Cors
from aws_cdk.aws_logs import LogGroup, RetentionDays
from cdk_nag import NagSuppressions
from constructs import Construct

from common_constructs.stack import Stack
from common_constructs.webacl import WebACL, WebACLScope


class LicenseApi(RestApi):
    def __init__(
            self, scope: Construct, construct_id: str, *,
            environment_name: str,
            **kwargs
    ):
        access_log_group = LogGroup(
            scope, 'ApiAccessLogGroup',
            retention=RetentionDays.ONE_MONTH
        )
        NagSuppressions.add_resource_suppressions(
            access_log_group,
            suppressions=[{
                'id': 'HIPAA.Security-CloudWatchLogGroupEncrypted',
                'reason': 'This group will contain no PII or PHI and should be accessible by anyone with access'
                ' to the AWS account for basic operational support visibility. Encrypting is not appropriate here.'
            }]
        )

        super().__init__(
            scope, construct_id,
            cloud_watch_role=True,
            deploy_options=StageOptions(
                stage_name=environment_name,
                logging_level=MethodLoggingLevel.INFO,
                access_log_destination=LogGroupLogDestination(access_log_group),
                access_log_format=AccessLogFormat.custom(json.dumps({
                    'source_ip': '$context.identity.sourceIp',
                    'identity': {
                        'caller': '$context.identity.caller',
                        'user': '$context.identity.user',
                        'user_agent': '$context.identity.userAgent'
                    },
                    'level': 'INFO',
                    'message': 'API Access log',
                    'request_time': '[$context.requestTime]',
                    'http_method': '$context.httpMethod',
                    'domain_name': '$context.domainName',
                    'resource_path': '$context.resourcePath',
                    'path': '$context.path',
                    'protocol': '$context.protocol',
                    'status': '$context.status',
                    'response_length': '$context.responseLength',
                    'request_id': '$context.requestId'
                })),
                tracing_enabled=True,
                metrics_enabled=True
            ),
            # This API is for a variety of integrations including any state IT integrations, so we will
            # allow all origins
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS,
                allow_methods=Cors.ALL_METHODS,
                allow_headers=Cors.DEFAULT_HEADERS + ['cache-control']
            ),
            **kwargs
        )
        self.web_acl = WebACL(
            self, 'WebACL',
            acl_scope=WebACLScope.REGIONAL
        )
        self.web_acl.associate_stage(self.deployment_stage)

        self.add_gateway_response(
            'BadBodyResponse',
            type=ResponseType.BAD_REQUEST_BODY,
            status_code='400',
            response_headers={
                'Access-Control-Allow-Origin': "'*'"
            },
            templates={
                'application/json': '{"message": "$context.error.validationErrorString"}'
            }
        )

        v0_resource = self.root.add_resource('v0')

        license_noauth_resource = v0_resource.add_resource(
            'licenses-noauth', default_method_options=MethodOptions(
                authorization_type=AuthorizationType.NONE
            )
        )
        self._add_post_license(license_noauth_resource)

        stack = Stack.of(self)
        NagSuppressions.add_resource_suppressions_by_path(
            stack,
            f'{self.node.path}/CloudWatchRole/Resource',
            suppressions=[{
                'id': 'AwsSolutions-IAM4',
                'applies_to': [
                    'Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs'
                ],
                'reason': 'This policy is crafted specifically for the account-level role created here.'
            }]
        )
        NagSuppressions.add_resource_suppressions(
            self.deployment_stage,
            suppressions=[
                {
                    'id': 'HIPAA.Security-APIGWCacheEnabledAndEncrypted',
                    'reason': 'We will assess this after the API is more built out'
                },
                {
                    'id': 'HIPAA.Security-APIGWSSLEnabled',
                    'reason': 'We will add a TLS certificate after we have a domain name'
                }
            ]
        )
        NagSuppressions.add_stack_suppressions(
            stack,
            suppressions=[
                {
                    'id': 'AwsSolutions-APIG4',
                    'reason': 'We will implement authorization soon'
                },
                {
                    'id': 'AwsSolutions-COG4',
                    'reason': 'We will implement authorization soon'
                }
            ]
        )

    def _add_post_license(self, resource: Resource):
        resource.add_method(
            'POST',
            authorization_type=AuthorizationType.NONE,
            request_validator=self.parameter_body_validator,
            request_models={
                'application/json': self.post_license_model
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_models={
                        'application/json': self.message_response_model
                    }
                )
            ],
            integration=MockIntegration(
                request_templates={
                    'application/json': '{"statusCode": 200}'
                },
                integration_responses=[
                    IntegrationResponse(
                        status_code='200',
                        response_templates={
                            'application/json': '{"message": "OK"}'
                        }
                    )
                ]
            )
        )

    @cached_property
    def parameter_body_validator(self):
        return self.add_request_validator(
            'BodyValidator',
            validate_request_body=True,
            validate_request_parameters=True
        )

    @cached_property
    def post_license_model(self):
        ymd_format = '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        return self.add_model(
            'PostLicenseModel',
            schema=JsonSchema(
                type=JsonSchemaType.ARRAY,
                items=JsonSchema(
                    type=JsonSchemaType.OBJECT,
                    required=[
                        'npi',
                        'first_name',
                        'last_name',
                        'date_of_birth',
                        'home_state_address',
                        'jurisdiction',
                        'license_type',
                        'date_of_issuance',
                        'date_of_renewal',
                        'date_of_expiration',
                        'license_status'
                    ],
                    additional_properties=False,
                    properties={
                        'npi': JsonSchema(type=JsonSchemaType.STRING),
                        'first_name': JsonSchema(type=JsonSchemaType.STRING),
                        'middle_name': JsonSchema(type=JsonSchemaType.STRING),
                        'last_name': JsonSchema(type=JsonSchemaType.STRING),
                        'date_of_birth': JsonSchema(
                            type=JsonSchemaType.STRING,
                            pattern=ymd_format,
                            format='date'
                        ),
                        'other_identifiers': JsonSchema(
                            type=JsonSchemaType.OBJECT,
                            additional_properties=JsonSchema(type=JsonSchemaType.STRING)
                        ),
                        'home_state_address': JsonSchema(type=JsonSchemaType.STRING),
                        'jurisdiction': JsonSchema(type=JsonSchemaType.STRING, min_length=4, max_length=100),
                        'license_type': JsonSchema(
                            type=JsonSchemaType.STRING,
                            enum=self.node.get_context('license_types')
                        ),
                        'date_of_issuance': JsonSchema(
                            type=JsonSchemaType.STRING,
                            pattern=ymd_format,
                            format='date'
                        ),
                        'date_of_renewal': JsonSchema(
                            type=JsonSchemaType.STRING,
                            pattern=ymd_format,
                            format='date'
                        ),
                        'date_of_expiration': JsonSchema(
                            type=JsonSchemaType.STRING,
                            pattern=ymd_format,
                            format='date'
                        ),
                        'license_status': JsonSchema(
                            type=JsonSchemaType.STRING,
                            enum=[
                                'active',
                                'inactive'
                            ]
                        )
                    }
                )
            )
        )

    @cached_property
    def message_response_model(self):
        return self.add_model(
            'MessageResponseModel',
            schema=JsonSchema(
                type=JsonSchemaType.OBJECT,
                required=['message'],
                additional_properties=False,
                properties={
                    'message': JsonSchema(type=JsonSchemaType.STRING)
                }
            )
        )
