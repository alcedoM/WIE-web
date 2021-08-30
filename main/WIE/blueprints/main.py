# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import os

from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import func

from WIE.decorators import confirm_required, permission_required
from WIE.extensions import db
from WIE.forms.main import DescriptionForm, TagForm, CommentForm, ArticleForm
from WIE.models import User, Photo, Tag, Follow, Collect, Comment, Notification, Article
from WIE.notifications import push_comment_notification, push_collect_notification, push_art_comment_notification
from WIE.utils import rename_image, resize_image, redirect_back, flash_errors

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
        pagination_article = Article.query \
            .order_by(Article.timestamp.desc()) \
            .paginate(page, per_page)
        articles = pagination_article.items
    else:
        pagination_article = None
        articles = None
    tags = Tag.query.join(Tag.articles).group_by(Tag.id).order_by(func.count(Article.id).desc()).limit(10)
    return render_template('main/index.html', pagination_article=pagination_article, articles=articles, tags=tags,
                           Collect=Collect)


@main_bp.route('/showpic')
def pic_list():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
        pagination = Photo.query \
            .join(Follow, Follow.followed_id == Photo.author_id) \
            .filter(Follow.follower_id == current_user.id) \
            .order_by(Photo.timestamp.desc()) \
            .paginate(page, per_page)
        photos = pagination.items

    else:
        pagination = None
        photos = None
    tags = Tag.query.join(Tag.photos).group_by(Tag.id).order_by(func.count(Photo.id).desc()).limit(10)
    return render_template('main/showpic.html', pagination=pagination, photos=photos, tags=tags, Collect=Collect)


@main_bp.route('/explore')
@login_required
def explore():
    photos = Photo.query.order_by(func.random()).limit(12)
    return render_template('main/explore.html', photos=photos)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        flash('Enter keyword about photo, user or tag.', 'warning')
        return redirect_back()

    category = request.args.get('category', 'photo')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_SEARCH_RESULT_PER_PAGE']
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Photo.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template('main/search.html', q=q, results=results, pagination=pagination, category=category)


@main_bp.route('/rank')
@login_required
def rank():
    sql1 = """select username, score_acm, score_datascience, score_web ,score_hardware,
       (score_acm+score_datascience+score_web+score_hardware) as 'sumscore' from User;
    """
    data1 = db.session.execute(sql1)
    rank_list = []
    score = []
    for i in data1:
        if i[-1] != 0:
            rank_list.append(list(i))
            score.append(i[-1])
    c_index = 0
    c_score = 999999999
    score_rank = []
    for j in score:
        if j < c_score:
            c_index += 1
            c_score = j
        score_rank.append(c_index)
    for i in range(len(rank_list)):
        rank_list[i].insert(0, score_rank[i])

    # print(rank_data)
    # rank_data=[[1,2,3,4,5,6,7],[1,2,3,4,5,6,7]]
    return render_template('main/rank.html', data=rank_list)


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('Notification archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
# @confirm_required
@permission_required('MODERATE')
@permission_required('UPLOAD')
def upload():
    return render_template('main/upload.html')


@main_bp.route('/upload/photo', methods=['GET', 'POST'])
@login_required
# @confirm_required
@permission_required('MODERATE')
@permission_required('UPLOAD')
def upload_photo():
    if request.method == 'POST' and 'file' in request.files:
        f = request.files.get('file')
        filename = rename_image(f.filename)
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))
        filename_s = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small'])
        filename_m = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium'])

        photo = Photo(
            filename=filename,
            filename_s=filename_s,
            filename_m=filename_m,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()

    return render_template('main/uploadPic.html')


@main_bp.route('/upload/article', methods=['GET', 'POST'])
@login_required
# @confirm_required
@permission_required('MODERATE')
@permission_required('UPLOAD')
def upload_article():
    form = ArticleForm()
    if form.validate_on_submit():
        title = form.title.data
        main_text = form.main_text.data
        author = current_user._get_current_object()
        article = Article(title=title, main_text=main_text, author=author)

        db.session.add(article)
        db.session.commit()
        flash('发布成功', 'success')
        return redirect(url_for('main.index'))
    return render_template('main/uploadText.html', form=form)



@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    description_form.description.data = photo.description
    return render_template('main/photo.html', photo=photo, comment_form=comment_form,
                           description_form=description_form, tag_form=tag_form,
                           pagination=pagination, comments=comments)


@main_bp.route('/article/<int:article_id>')
def show_article(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(article).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items
    comment_form = CommentForm()
    tag_form = TagForm()
    main_text = article.main_text
    title = article.title

    return render_template('main/article.html', article=article, tag_form=tag_form, comment_form=comment_form,
                           main_text=main_text, title=title, pagination=pagination, comments=comments)


@main_bp.route('/photo/n/<int:photo_id>')
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()

    if photo_n is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/photo/p/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()

    if photo_p is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_p.id))


@main_bp.route('/article/p/<int:article_id>')
def article_previous(article_id):
    article = Article.query.get_or_404(article_id)
    article_p = Article.query.with_parent(article.author).filter(article.id > article_id).order_by(
        Article.id.asc()).first()

    if article_p is None:
        flash('前面没有了', 'info')
        return redirect(url_for('.show_article', article_id=article_id))
    return redirect(url_for('.show_article', article_id=article_p.id))


@main_bp.route('/article/n/<int:article_id>')
def article_next(article_id):
    article = Article.query.get_or_404(article_id)
    article_n = Article.query.with_parent(article.author).filter(article.id < article_id).order_by(
        Article.id.desc()).first()

    if article_n is None:
        flash('后面没有了', 'info')
        return redirect(url_for('.show_article', article_id=article_id))
    return redirect(url_for('.show_article', article_id=article_n.id))


@main_bp.route('/collect/<int:photo_id>', methods=['POST'])
@login_required
@permission_required('COLLECT')
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.collect(photo)
    flash('Photo collected.', 'success')
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/art-collect/<int:article_id>', methods=['POST'])
@login_required
@permission_required('COLLECT')
def art_collect(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user.article_is_collecting(article):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))

    current_user.article_collect(article)
    flash('收藏成功.', 'success')

    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/art-uncollect/<int:article_id>', methods=['POST'])
@login_required
def art_uncollect(article_id):
    article = Article.query.get_or_404(article_id)
    if not current_user.article_is_collecting(article):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))

    current_user.article_uncollect(article)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/art-comment/<int:comment_id>', methods=['POST'])
@login_required
def report_art_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_article', article_id=comment.article_id))


@main_bp.route('/report/photo/<int:photo_id>', methods=['POST'])
@login_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash('Photo reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=photo.id))


@main_bp.route('/photo/<int:photo_id>/collectors')
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', collects=collects, photo=photo, pagination=pagination)


@main_bp.route('/article/<int:article_id>/collectors')
def show_art_collectors(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect.query.with_parent(article).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', collects=collects, article=article, pagination=pagination)


@main_bp.route('/photo/<int:photo_id>/description', methods=['POST'])
@login_required
def edit_description(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('Description updated.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.author.receive_comment_notification:
                push_comment_notification(photo_id=photo.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if current_user != photo.author and photo.author.receive_comment_notification:
            push_comment_notification(photo_id, receiver=photo.author, page=page)

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id, page=page))


@main_bp.route('/article/<int:article_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_article_comment(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, article=article)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.author.receive_comment_notification:
                push_art_comment_notification(article_id=article.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if current_user != article.author and article.author.receive_comment_notification:
            push_art_comment_notification(article_id, receiver=article.author, page=page)

    flash_errors(form)
    return redirect(url_for('.show_article', article_id=article_id, page=page))


@main_bp.route('/photo/<int:photo_id>/tag/new', methods=['POST'])
@login_required
def new_tag(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/article/<int:article_id>/tag/new', methods=['POST'])
@login_required
def new_art_tag(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user != article.author and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in article.tags:
                article.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/set-comment/<int:photo_id>', methods=['POST'])
@login_required
def set_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    if photo.can_comment:
        photo.can_comment = False
        flash('Comment disabled', 'info')
    else:
        photo.can_comment = True
        flash('Comment enabled.', 'info')
    db.session.commit()
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_photo', photo_id=comment.photo_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


@main_bp.route('/set-article-comment/<int:article_id>', methods=['POST'])
@login_required
def set_article_comment(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user != article.author:
        abort(403)

    if article.can_comment:
        article.can_comment = False
        flash('Comment disabled', 'info')
    else:
        article.can_comment = True
        flash('Comment enabled.', 'info')
    db.session.commit()
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/reply/article-comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_article_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_article', article_id=comment.article_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


@main_bp.route('/delete/photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted.', 'info')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()
        if photo_p is None:
            return redirect(url_for('user.index', username=photo.author.username))
        return redirect(url_for('.show_photo', photo_id=photo_p.id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/delete/article/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user != article.author and not current_user.can('MODERATE'):
        abort(403)

    db.session.delete(article)
    db.session.commit()
    flash('article deleted.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author \
            and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/delete/article-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_article_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.article.author \
            and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('.show_article', article_id=comment.article_id))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items

    if order == 'by_collects':
        photos.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route('/art-tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/art-tag/<int:tag_id>/<order>')
def show_art_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Article.query.with_parent(tag).order_by(Article.timestamp.desc()).paginate(page, per_page)
    articles = pagination.items

    if order == 'by_collects':
        articles.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/art-tag.html', tag=tag, pagination=pagination, articles=articles, order_rule=order_rule)


@main_bp.route('/delete/tag/<int:photo_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(photo_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/delete/art-tag/<int:article_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_art_tag(article_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    article = Article.query.get_or_404(article_id)
    if current_user != article.author and not current_user.can('MODERATE'):
        abort(403)
    article.tags.remove(tag)
    db.session.commit()

    if not tag.articles:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_article', article_id=article_id))
