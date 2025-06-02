# coding: utf-8
from rest_framework import serializers


class CreateGroupSerializer(serializers.Serializer):
    group_name = serializers.CharField(max_length=20, required=True)
    creator_id = serializers.IntegerField(required=True)
    member_list = serializers.ListField(child=serializers.IntegerField(), default=[], required=False)

    def validate_member_list(self, value):
        print(value, 'xjh xixi')
        return value

    def create(self, validated_data):
        return {'code': '?'}
