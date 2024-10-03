from api.models import VerificationV
from rest_framework import serializers


class ParametersSerializer(serializers.Serializer):
    Email = serializers.EmailField(
        allow_null=True,
        default=None
    )
    PhoneNumber = serializers.CharField(
        max_length=200,
        allow_null=True,
        default=None
    )
    PersonIdentityCard1 = serializers.CharField(
        max_length=200,
        allow_null=True,
        default=None
    )
    PersonIdentityCard = serializers.CharField(
        max_length=200,
        allow_null=True,
        default=None
    )
    PersonIdentityCard2 = serializers.CharField(
        max_length=200,
        allow_null=True,
        default=None
    )
    application_id = serializers.CharField(
        max_length=200,
        allow_null=True,
        default=None
    )
    application_date = serializers.DateTimeField(
        allow_null=True,
        default=None
    )
    mode = serializers.IntegerField(
        allow_null=True,
        default=None
    )
    # class Meta:
    #     model = VerificationV
    #     fields = [
    #         'id',
    #         'phone_number',
    #         'email',
    #         'persons_identity_card1',
    #         'persons_identity_card2',
    #         'application_date'
    #     ]
    #     extra_kwargs = {'id': {'read_only': False, 'allow_null': True, 'default': None},
    #                     'phone_number': {'default': None},
    #                     'email': {'default': None},
    #                     'persons_identity_card1': {'default': None},
    #                     'persons_identity_card2': {'default': None},
    #                     'application_date': {'default': None}}


class DataRequestSerializer(serializers.Serializer):
    MethodName = serializers.CharField(
        max_length=100,
        allow_null=True,
        default=None,
    )
    Parameters = ParametersSerializer()
    Type = serializers.CharField(
        max_length=100,
        allow_null=True,
        default=None,
    )
