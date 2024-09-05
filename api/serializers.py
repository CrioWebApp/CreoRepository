from api.models import VerificationV
from rest_framework import serializers


class ParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationV
        fields = [
            'id',
            'phone_number',
            'email',
            'persons_identity_card1',
            'persons_identity_card2',
            'application_date'
        ]
        extra_kwargs = {'id': {'read_only': False, 'allow_null': True, 'default': None},
                        'phone_number': {'default': None},
                        'email': {'default': None},
                        'persons_identity_card1': {'default': None},
                        'persons_identity_card2': {'default': None},
                        'application_date': {'default': None}}


class DataRequestSerializer(serializers.Serializer):
    Parameters = ParametersSerializer()
    Type = serializers.CharField(max_length=50)


class VerificationVSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationV
        fields = "__all__"
