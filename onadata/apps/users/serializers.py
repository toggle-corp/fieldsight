from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from onadata.apps.users.models import UserProfile


def validateEmail( email ):
    from django.core.validators import validate_email
    try:
        validate_email( email )
        try:
            user = User.objects.get(email__iexact=email)
            return True
        except:
            raise ValidationError("Email not in use")
    except ValidationError:
        return False


class AuthCustomTokenSerializer(serializers.Serializer):
    email_or_username = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email_or_username = attrs.get('email_or_username')
        password = attrs.get('password')

        if email_or_username and password:
            # Check if user sent email
            if validateEmail(email_or_username):
                user_request = get_object_or_404(
                    User,
                    email=email_or_username,
                )

                email_or_username = user_request.username

            user = authenticate(username=email_or_username, password=password)

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise ValidationError(msg)
            else:
                msg = _('Unable to log in with provided credentials.')
                raise ValidationError(msg)
        else:
            msg = _('Must include "email or username" and "password"')
            raise ValidationError(msg)

        attrs['user'] = user
        return attrs


# class ProfileSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = UserProfile
#         exclude = ('user', 'id', 'organization')
#

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    password = serializers.CharField()

    class Meta:
        model = User
        exclude = ('last_login', 'is_superuser', 'is_staff', 'is_active', 'date_joined', 'groups', 'user_permissions')

    def get_profile_picture(self, obj):
        if obj.user_profile.profile_picture:
            return obj.user_profile.profile_picture.url
        return None


class ProfileUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        exclude = ('last_login', 'is_superuser', 'is_staff', 'is_active', 'date_joined', 'groups', 'user_permissions','password')
        read_only_fields = ('username', 'email', 'last_login', 'date_joined', 'id')


class UserSerializerProfile(serializers.ModelSerializer):
    user = ProfileUserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        read_only_fields = ('id')

    def update(self,  instance, validated_data):
        data = self.context['request'].data
        user = data.pop('user')
        UserProfile.objects.filter(pk=instance.pk).update(**validated_data)
        User.objects.filter(user_profile=instance).update(**user)
        return instance

