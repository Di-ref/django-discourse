import json

from django.conf.urls import url
from django.core.serializers.json import DjangoJSONEncoder

# tastypie
from tastypie import fields, utils
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.paginator import Paginator
from tastypie.serializers import Serializer
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

# import models
from discussion.models import Categories, Topics, Posts

# import resources
from account.api.resources import UserResource

# import services
from discussion.services.category import CategoryService
from discussion.services.topic import TopicService
from discussion.services.post import PostService


# CategoryResource
class CategoryResource(ModelResource):

    class Meta:
        queryset = Categories.objects.all()
        resource_name = 'category'
        excludes = ['']
        serializer = Serializer(formats=['json'])
        allowed_methods = ['get', 'post', 'put', 'patch', 'delete']

        filtering = {
            'slug': ['exact']
        }

        authorization = Authorization()

    # POST - create category
    def obj_create(self, bundle, request=None, **kwargs):

        # get or create category
        listObj, created = CategoryService.getOrCreateCategory(bundle.data['title'])
        bundle.obj = listObj

        return bundle

    # DELETE - delete category
    def obj_delete(self, request=None, **kwargs):
        return None

    # PATCH - update category
    def obj_update(self, bundle, request=None, **kwargs):
        return None

    # get lists by slug or id
    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>[\d]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d-]+)/(?P<pk>[\d]+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


# Topic List
class TopicResource(ModelResource):
    category = fields.ToOneField(CategoryResource, 'category', full=False, null=True)
    user = fields.ToOneField(UserResource, 'user', full=True, null=True)
    last_post_user = fields.ToOneField(UserResource, 'last_post_user', full=True, null=True)
    highest_post = fields.ToOneField('discussion.api.resources.PostResource', 'highest_post', full=False, null=True)

    class Meta:
        queryset = Topics.objects.all()
        resource_name = 'topic'
        excludes = ['']
        serializer = Serializer(formats=['json'])
        allowed_methods = ['get', 'post', 'put', 'patch', 'delete']

        filtering = {
            'slug': ['exact'],
            'category': ALL_WITH_RELATIONS
        }

        authorization = Authorization()

    # POST - create topic
    def obj_create(self, bundle, request=None, **kwargs):

        # create topic
        topicObj = TopicService.createTopic(bundle.data['title'], bundle.data['category'], request.user)
        bundle.obj = topicObj

        return bundle

    # DELETE - delete topic
    def obj_delete(self, request=None, **kwargs):
        return None

    # PATCH - update topic
    def obj_update(self, bundle, request=None, **kwargs):
        return None

    # get lists by slug or id
    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>[\d]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d-]+)/(?P<pk>[\d]+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class PostSerializer(Serializer):
    def to_json(self, data, options=None):
        options = options or {}

        data = self.to_simple(data, options)

        if 'objects' in data:
            # change reply_to_post to plain id
            for post in data['objects']:

                if post['reply_to_post'] != None:
                    post['reply_to_post'] = int(post['reply_to_post'].split('/')[4])

        return json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True)

    def from_json(self, content):
        data = json.loads(content)

        if 'requested_time' in data:
            # Log the request here...
            pass

        return data


# Post Resource - Get posts by Topic ID
class PostResource(ModelResource):
    topic = fields.ToOneField(TopicResource, 'topic', full=False, null=True)
    user = fields.ToOneField(UserResource, 'user', full=True, null=True)
    reply_to_post = fields.ToOneField('self', 'reply_to_post', full=False, null=True)
    reply_to_user = fields.ToOneField(UserResource, 'reply_to_user', full=True, null=True)
    reply_below_post = fields.ToOneField('self', 'reply_below_post', full=False, null=True)
    last_editor = fields.ToOneField(UserResource, 'last_editor', full=True, null=True)

    class Meta:
        queryset = Posts.objects.all()
        resource_name = 'post'
        excludes = ['raw', 'spam_count', 'topic', 'inappropriate_count']
        serializer = PostSerializer(formats=['json'])
        allowed_methods = ['get', 'post', 'put', 'patch', 'delete']
        paginator_class = Paginator

        filtering = {
            'topic': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS,
            'reply_to_post': ALL_WITH_RELATIONS
        }

        authorization = Authorization()

    # POST - create post
    def obj_create(self, bundle, request=None, **kwargs):

        topic = bundle.data['topic']
        message = bundle.data['message']
        reply_to_post = bundle.data['reply_to_post']

        # create post
        postObj = PostService.createPost(topic, request.user, message, reply_to_post)
        bundle.obj = postObj

        return bundle

    # DELETE - delete post
    def obj_delete(self, request=None, **kwargs):
        return None

    # PATCH - update post
    def obj_update(self, bundle, request=None, **kwargs):
        return None
