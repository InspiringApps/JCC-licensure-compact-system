from __future__ import annotations

import json
import os

from aws_cdk import Duration, Stack
from aws_cdk.aws_apigateway import Resource, MethodResponse, JsonSchema, \
    JsonSchemaType, MethodOptions, AuthorizationType, Model, LambdaIntegration
from aws_cdk.aws_kms import IKey
from cdk_nag import NagSuppressions

from common_constructs.python_function import PythonFunction
# Importing module level to allow lazy loading for typing
from . import license_api
from ..persistent_stack import LicenseTable


YMD_FORMAT = '^[12]{1}[0-9]{3}-[01]{1}[0-9]{1}-[0-3]{1}[0-9]{1}$'
SSN_FORMAT = '^[0-9]{3}-[0-9]{2}-[0-9]{4}$'


class QueryLicenses:
    def __init__(
            self,
            resource: Resource,
            method_options: MethodOptions,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ):
        super().__init__()

        self.resource = resource.add_resource('query')
        self.api: license_api.LicenseApi = resource.api
        self._add_query_one_license(
            method_options=method_options,
            data_encryption_key=data_encryption_key,
            license_data_table=license_data_table
        )
        self._add_query_licenses_by_family_name(
            method_options=method_options,
            data_encryption_key=data_encryption_key,
            license_data_table=license_data_table
        )
        self._add_query_licenses_by_updated(
            method_options=method_options,
            data_encryption_key=data_encryption_key,
            license_data_table=license_data_table
        )

    def _add_query_one_license(
            self,
            method_options: MethodOptions,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ):
        self.resource.add_method(
            'POST',
            request_validator=self.api.parameter_body_validator,
            request_models={
                'application/json': self.get_query_one_license_request_model()
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_models={
                        'application/json': self.get_query_license_response_model()
                    }
                )
            ],
            integration=LambdaIntegration(
                self._get_query_one_license_handler(
                    data_encryption_key=data_encryption_key,
                    license_data_table=license_data_table
                ),
                timeout=Duration.seconds(29)
            ),
            request_parameters={
                'method.request.header.Authorization': True
            } if method_options.authorization_type != AuthorizationType.NONE else {},
            authorization_type=method_options.authorization_type,
            authorizer=method_options.authorizer
        )

    def _add_query_licenses_by_family_name(
            self,
            method_options: MethodOptions,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ):
        resource = self.resource.add_resource('by-family-name')
        resource.add_method(
            'POST',
            request_validator=self.api.parameter_body_validator,
            request_models={
                'application/json': self.get_query_licenses_request_model()
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_models={
                        'application/json': self.get_query_license_response_model()
                    }
                )
            ],
            integration=LambdaIntegration(
                self._get_query_licenses_by_family_name_handler(
                    data_encryption_key=data_encryption_key,
                    license_data_table=license_data_table
                ),
                timeout=Duration.seconds(29)
            ),
            request_parameters={
                'method.request.header.Authorization': True
            } if method_options.authorization_type != AuthorizationType.NONE else {},
            authorization_type=method_options.authorization_type,
            authorizer=method_options.authorizer
        )

    def _add_query_licenses_by_updated(
            self,
            method_options: MethodOptions,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ):
        resource = self.resource.add_resource('by-updated')
        resource.add_method(
            'POST',
            request_validator=self.api.parameter_body_validator,
            request_models={
                'application/json': self.get_query_licenses_request_model()
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_models={
                        'application/json': self.get_query_license_response_model()
                    }
                )
            ],
            integration=LambdaIntegration(
                self._get_query_licenses_by_updated_handler(
                    data_encryption_key=data_encryption_key,
                    license_data_table=license_data_table
                ),
                timeout=Duration.seconds(29)
            ),
            request_parameters={
                'method.request.header.Authorization': True
            } if method_options.authorization_type != AuthorizationType.NONE else {},
            authorization_type=method_options.authorization_type,
            authorizer=method_options.authorizer
        )

    def get_query_one_license_request_model(self) -> Model:
        """
        Return the query one license request model, which should only be created once per API
        """
        if not hasattr(self.api, 'query_license_request_model'):
            self.api.query_license_request_model = self.api.add_model(
                'QueryLicenseRequestModel',
                schema=JsonSchema(
                    type=JsonSchemaType.OBJECT,
                    required=['ssn'],
                    properties={
                        'ssn': JsonSchema(
                            type=JsonSchemaType.STRING,
                            pattern=SSN_FORMAT
                        ),
                        'pagination': self.pagination_schema
                    }
                )
            )
        return self.api.query_license_request_model

    def get_query_licenses_request_model(self) -> Model:
        """
        Return the query licenses request model, which should only be created once per API
        """
        if not hasattr(self.api, 'query_licenses_request_model'):
            self.api.query_licenses_request_model = self.api.add_model(
                'QueryLicensesRequestModel',
                schema=JsonSchema(
                    type=JsonSchemaType.OBJECT,
                    properties={
                        'pagination': self.pagination_schema
                    }
                )
            )
        return self.api.query_licenses_request_model

    @property
    def pagination_schema(self):
        return JsonSchema(
            type=JsonSchemaType.OBJECT,
            properties={
                'lastKey': JsonSchema(type=JsonSchemaType.STRING, min_length=1, max_length=1024),
                'pageSize': JsonSchema(type=JsonSchemaType.INTEGER, minimum=5, maximum=100)
            }
        )

    def get_query_license_response_model(self) -> Model:
        """
        Return the query license response model, which should only be created once per API
        """
        if not hasattr(self.api, 'query_license_response_model'):
            self.api.query_license_response_model = self.api.add_model(
                'QueryLicenseResponseModel',
                schema=JsonSchema(
                    type=JsonSchemaType.ARRAY,
                    max_length=100,
                    items=self.license_response_schema
                )
            )
        return self.api.query_license_response_model

    @property
    def license_response_schema(self):
        stack = Stack.of(self.api)
        return JsonSchema(
            type=JsonSchemaType.OBJECT,
            required=[
                'type',
                'compact',
                'jurisdiction',
                'ssn',
                'given_name',
                'family_name',
                'date_of_birth',
                'home_state_street_1',
                'home_state_street_2',
                'home_state_city',
                'home_state_postal_code',
                'license_type',
                'date_of_issuance',
                'date_of_renewal',
                'date_of_expiration',
                'date_of_update',
                'status'
            ],
            additional_properties=False,
            properties={
                'type': JsonSchema(
                    type=JsonSchemaType.STRING,
                    enum=['license-home']
                ),
                'compact': JsonSchema(
                    type=JsonSchemaType.STRING,
                    enum=stack.node.get_context('compacts')
                ),
                'jurisdiction': JsonSchema(
                    type=JsonSchemaType.STRING,
                    enum=stack.node.get_context('jurisdictions')
                ),
                'ssn': JsonSchema(
                    type=JsonSchemaType.STRING,
                    pattern=SSN_FORMAT
                ),
                'npi': JsonSchema(
                    type=JsonSchemaType.STRING,
                    pattern='^[0-9]{10}$'
                ),
                'given_name': JsonSchema(type=JsonSchemaType.STRING, min_length=1, max_length=100),
                'middle_name': JsonSchema(type=JsonSchemaType.STRING, min_length=1, max_length=100),
                'family_name': JsonSchema(type=JsonSchemaType.STRING, min_length=1, max_length=100),
                'date_of_birth': JsonSchema(
                    type=JsonSchemaType.STRING,
                    format='date',
                    pattern=YMD_FORMAT
                ),
                'home_state_street_1': JsonSchema(type=JsonSchemaType.STRING, min_length=2, max_length=100),
                'home_state_street_2': JsonSchema(type=JsonSchemaType.STRING, min_length=1, max_length=100),
                'home_state_city': JsonSchema(type=JsonSchemaType.STRING, min_length=2, max_length=100),
                'home_state_postal_code': JsonSchema(type=JsonSchemaType.STRING, min_length=5, max_length=7),
                'license_type': JsonSchema(
                    type=JsonSchemaType.STRING,
                    enum=stack.node.get_context('license_types')
                ),
                'date_of_issuance': JsonSchema(
                    type=JsonSchemaType.STRING,
                    format='date',
                    pattern=YMD_FORMAT
                ),
                'date_of_renewal': JsonSchema(
                    type=JsonSchemaType.STRING,
                    format='date',
                    pattern=YMD_FORMAT
                ),
                'date_of_expiration': JsonSchema(
                    type=JsonSchemaType.STRING,
                    format='date',
                    pattern=YMD_FORMAT
                ),
                'date_of_update': JsonSchema(
                    type=JsonSchemaType.STRING,
                    format='date',
                    pattern=YMD_FORMAT
                ),
                'status': JsonSchema(
                    type=JsonSchemaType.STRING,
                    enum=[
                        'active',
                        'inactive'
                    ]
                )
            }
        )

    def _get_query_one_license_handler(
            self,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ) -> PythonFunction:
        stack = Stack.of(self.resource)
        handler = PythonFunction(
            self.resource, 'QueryOneLicenseHandler',
            entry=os.path.join('lambdas', 'license-data'),
            index='handlers/license.py',
            handler='query_one_license',
            environment={
                'DEBUG': 'true',
                'LICENSE_TABLE_NAME': license_data_table.table_name,
                'CJNS_INDEX_NAME': license_data_table.cjns_index_name,
                'UPDATED_INDEX_NAME': license_data_table.updated_index_name,
                'COMPACTS': json.dumps(stack.node.get_context('compacts')),
                'JURISDICTIONS': json.dumps(stack.node.get_context('jurisdictions'))
            }
        )
        data_encryption_key.grant_decrypt(handler)
        license_data_table.grant_read_data(handler)

        NagSuppressions.add_resource_suppressions_by_path(
            stack,
            path=f'{handler.node.path}/ServiceRole/DefaultPolicy/Resource',
            suppressions=[
                {
                    'id': 'AwsSolutions-IAM5',
                    'reason': 'The actions in this policy are specifically what this lambda needs to read '
                              'and is scoped to one table and encryption key.'
                }
            ]
        )
        return handler

    def _get_query_licenses_by_family_name_handler(
            self,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ) -> PythonFunction:
        stack = Stack.of(self.resource)
        handler = PythonFunction(
            self.resource, 'QueryLicensesByFamilyHandler',
            entry=os.path.join('lambdas', 'license-data'),
            index='handlers/license.py',
            handler='query_licenses_family',
            environment={
                'DEBUG': 'true',
                'LICENSE_TABLE_NAME': license_data_table.table_name,
                'CJNS_INDEX_NAME': license_data_table.cjns_index_name,
                'UPDATED_INDEX_NAME': license_data_table.updated_index_name,
                'COMPACTS': json.dumps(stack.node.get_context('compacts')),
                'JURISDICTIONS': json.dumps(stack.node.get_context('jurisdictions'))
            }
        )
        data_encryption_key.grant_decrypt(handler)
        license_data_table.grant_read_data(handler)

        NagSuppressions.add_resource_suppressions_by_path(
            stack,
            path=f'{handler.node.path}/ServiceRole/DefaultPolicy/Resource',
            suppressions=[
                {
                    'id': 'AwsSolutions-IAM5',
                    'reason': 'The actions in this policy are specifically what this lambda needs to read '
                              'and is scoped to one table and encryption key.'
                }
            ]
        )
        return handler

    def _get_query_licenses_by_updated_handler(
            self,
            data_encryption_key: IKey,
            license_data_table: LicenseTable
    ) -> PythonFunction:
        stack = Stack.of(self.resource)
        handler = PythonFunction(
            self.resource, 'QueryLicensesByUpdatedHandler',
            entry=os.path.join('lambdas', 'license-data'),
            index='handlers/license.py',
            handler='query_licenses_updated',
            environment={
                'DEBUG': 'true',
                'LICENSE_TABLE_NAME': license_data_table.table_name,
                'CJNS_INDEX_NAME': license_data_table.cjns_index_name,
                'UPDATED_INDEX_NAME': license_data_table.updated_index_name,
                'COMPACTS': json.dumps(stack.node.get_context('compacts')),
                'JURISDICTIONS': json.dumps(stack.node.get_context('jurisdictions'))
            }
        )
        data_encryption_key.grant_decrypt(handler)
        license_data_table.grant_read_data(handler)

        NagSuppressions.add_resource_suppressions_by_path(
            stack,
            path=f'{handler.node.path}/ServiceRole/DefaultPolicy/Resource',
            suppressions=[
                {
                    'id': 'AwsSolutions-IAM5',
                    'reason': 'The actions in this policy are specifically what this lambda needs to read '
                              'and is scoped to one table and encryption key.'
                }
            ]
        )
        return handler
