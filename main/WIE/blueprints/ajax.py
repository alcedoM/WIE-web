# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import render_template, jsonify, Blueprint
from flask_login import current_user

from WIE.models import User, Photo, Notification, Article
from WIE.notifications import push_collect_notification, push_follow_notification

ajax_bp = Blueprint('ajax', __name__)


@ajax_bp.route('/notifications-count')
def notifications_count():
    if not current_user.is_authenticated:
        return jsonify(message='需要登录.'), 403

    count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
    return jsonify(count=count)


@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)


@ajax_bp.route('/followers-count/<int:user_id>')
def followers_count(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1  # minus user self
    return jsonify(count=count)


@ajax_bp.route('/<int:photo_id>/followers-count')
def collectors_count(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    count = len(photo.collectors)
    return jsonify(count=count)


@ajax_bp.route('/<int:article_id>/article-followers-count')
def article_collectors_count(article_id):
    article = Article.query.get_or_404(article_id)
    count = len(article.collectors)
    return jsonify(count=count)


@ajax_bp.route('/collect/<int:photo_id>', methods=['POST'])
def collect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message='需要登陆'), 403

    if not current_user.can('COLLECT'):
        return jsonify(message='权限不足.'), 403

    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        return jsonify(message='已经被收藏.'), 400

    current_user.collect(photo)
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return jsonify(message='收藏成功.')


@ajax_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
def uncollect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message='需要登录'), 403

    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        return jsonify(message='还没收藏'), 400

    current_user.uncollect(photo)
    return jsonify(message='取消成功')


@ajax_bp.route('/article-collect/<int:article_id>', methods=['POST'])
def article_collect(article_id):
    if not current_user.is_authenticated:
        return jsonify(message='需要登录.'), 403
    if not current_user.can('COLLECT'):
        return jsonify(message='权限不足.'), 403

    article = Article.query.get_or_404(article_id)
    if current_user.article_is_collecting(article):
        return jsonify(message='已经被收藏'), 400

    current_user.article_collect(article)
    if current_user != article.author and article.author.receive_collect_notification:
        push_collect_notification(collector=current_user, article_id=article_id, receiver=article.author)
    return jsonify(message='收藏成功.')


@ajax_bp.route('/article-uncollect/<int:article_id>', methods=['POST'])
def article_uncollect(article_id):
    if not current_user.is_authenticated:
        return jsonify(message='需要登录.'), 403

    article = Article.query.get_or_404(article_id)
    if not current_user.article_is_collecting(article):
        return jsonify(message='还没收藏.'), 400

    current_user.article_uncollect(article)
    return jsonify(message='取消收藏.')


@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='需要登录'), 403
    if not current_user.can('FOLLOW'):
        return jsonify(message='没有权限.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        return jsonify(message='已经关注'), 400

    current_user.follow(user)
    if user.receive_collect_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return jsonify(message='关注成功.')


@ajax_bp.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if not current_user.is_authenticated:
        return jsonify(message='需要登录.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        return jsonify(message='还没关注.'), 400

    current_user.unfollow(user)
    return jsonify(message='取消成功.')
