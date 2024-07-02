"""
This module contains serializers that are used for formatting the response data.

Each serializer in this module corresponds to a specific API endpoint.
These serve to map internal Python data types
to JSON-compatible data types that can be sent in the HTTP response,
and to clearly document the structure of the response data.
"""
from rest_framework import serializers
from home.models import Account


class GetUsersRespSerializer(serializers.ModelSerializer):
    # Daily walk metrics.
    dw_count = serializers.IntegerField()
    dw_steps = serializers.IntegerField()
    dw_distance = serializers.FloatField()

    # Contest-id specific metrics. These only appear if contest_id
    # was specified in the query URL.
    iw_count = serializers.IntegerField(required=False)
    iw_steps = serializers.IntegerField(required=False)
    iw_distance = serializers.FloatField(required=False)
    iw_time = serializers.IntegerField(required=False)

    # True if the user's Account was created within the contest period.
    is_new = serializers.BooleanField(
        required=False,
    )
    # True is the user has walked at least one step.
    is_active = serializers.BooleanField(
        required=False,
    )

    class Meta:
        model = Account
        fields = "__all__"
