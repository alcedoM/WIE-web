# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import url_for

from WIE.extensions import db
from WIE.models import Notification


def push_follow_notification(follower, receiver):
    message = '<a href="%s">%s</a>关注了你.' % \
              (url_for('user.index', username=follower.username), follower.username)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_comment_notification(photo_id, receiver, page=1):
    message = '<a href="%s#comments">这张图片</a>收到了评论' % \
              (url_for('main.show_photo', photo_id=photo_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_art_comment_notification(article_id, receiver, page=1):
    message = '<a href="%s#comments">这篇文章</a>收到了评论' % \
              (url_for('main.show_article', article_id=article_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_collect_notification(collector, photo_id, receiver):
    message = '<a href="%s">%s</a>收藏了你的<a href="%s">图片</a>' % \
              (url_for('user.index', username=collector.username),
               collector.username,
               url_for('main.show_photo', photo_id=photo_id))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()
