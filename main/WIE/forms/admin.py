# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from wtforms import StringField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email

from WIE.forms.user import EditProfileForm
from WIE.models import User, Role

class EditProfileAdminForm(EditProfileForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    role = SelectField('Role', coerce=int)
    acm_score = IntegerField('ACM分数')
    ds_score = IntegerField('数据科学分数')
    web_score = IntegerField('WEB分数')
    hw_score = IntegerField('硬件分数')
    active = BooleanField('激活')
    confirmed = BooleanField('确认')
    submit = SubmitField('提交')


    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already in use.')

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('The email is already in use.')
