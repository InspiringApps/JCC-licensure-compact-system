from urllib.parse import quote

from marshmallow import pre_dump, post_load
from marshmallow.fields import String, Date, UUID
from marshmallow.validate import Regexp, Length, OneOf

from data_model.schema.base_record import BaseRecordSchema, SocialSecurityNumber, ForgivingSchema, StrictSchema


class SSNIndexRecordSchema(StrictSchema):
    pk = UUID(required=True, allow_none=False)
    sk = String(required=True, allow_none=False)
    ssn = SocialSecurityNumber(required=True, allow_none=False)
    license_home_provider_id = UUID(required=True, allow_none=False)


class LicenseCommonSchema(ForgivingSchema):
    given_name = String(required=True, allow_none=False, validate=Length(1, 100))
    middle_name = String(required=False, allow_none=False, validate=Length(1, 100))
    family_name = String(required=True, allow_none=False, validate=Length(1, 100))
    suffix = String(required=False, allow_none=False, validate=Length(1, 100))
    license_type = String(required=True, allow_none=False, validate=OneOf(['audiology', 'speech language']))
    date_of_issuance = Date(required=True, allow_none=False)
    date_of_renewal = Date(required=True, allow_none=False)
    date_of_expiration = Date(required=True, allow_none=False)
    status = String(required=True, allow_none=False, validate=OneOf(['active', 'inactive']))


class LicensePublicSchema(LicenseCommonSchema):
    """
    Schema for license data that can be shared with the public
    """
    birth_month_day = String(required=False, allow_none=False, validate=Regexp('^[0-1]{1}[0-9]{1}-[0-3]{1}[0-9]{1}'))


class LicensePostSchema(LicensePublicSchema):
    """
    Schema for license data as posted by a board
    """
    ssn = SocialSecurityNumber(required=True, allow_none=False)
    npi = String(required=False, allow_none=False, validate=Regexp('^[0-9]{10}$'))
    home_state_street_1 = String(required=True, allow_none=False, validate=Length(2, 100))
    home_state_street_2 = String(required=False, allow_none=False, validate=Length(1, 100))
    home_state_city = String(required=True, allow_none=False, validate=Length(2, 100))
    home_state_postal_code = String(required=True, allow_none=False, validate=Length(5, 7))
    date_of_birth = Date(required=True, allow_none=False)


@BaseRecordSchema.register_schema('license-home')
class LicenseRecordSchema(BaseRecordSchema, LicensePostSchema):
    """
    Schema for license records in the license data table
    """
    _record_type = 'license-home'

    # Provided fields
    provider_id = UUID(required=True, allow_none=False)

    # Generated fields
    fam_giv_mid = String(required=True, allow_none=False)
    license_home_provider_id = UUID(required=True, allow_none=False)

    @post_load
    def drop_license_gen_fields(self, in_data, **kwargs):  # pylint: disable=unused-argument
        del in_data['fam_giv_mid']
        del in_data['license_home_provider_id']
        return in_data

    @pre_dump
    def populate_license_gen_fields(self, in_data, **kwargs):  # pylint: disable=unused-argument
        in_data['license_home_provider_id'] = in_data['provider_id']
        in_data['birth_month_day'] = in_data['date_of_birth'].strftime('%m-%d')
        in_data['fam_giv_mid'] = '/'.join((
            quote(in_data['family_name'], safe=''),
            quote(in_data['given_name'], safe=''),
            quote(in_data.get('middle_name', ''), safe='')
        ))
        return in_data
