# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length


class DescriptionForm(FlaskForm):
    description = TextAreaField('描述', validators=[Optional(), Length(0, 500)])
    submit = SubmitField('提交')


class TagForm(FlaskForm):
    tag = StringField('添加标签(使用空格区分)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField('提交')


class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('提交')

class ArticleForm(FlaskForm):
    title = TextAreaField('标题(30字)', validators=[Optional(), Length(0,30)])
    main_text = TextAreaField('正文', validators=[Optional(), Length(0,500)])
    submit = SubmitField('提交')