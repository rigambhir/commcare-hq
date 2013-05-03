#from django.conf.urls.defaults import patterns, url
from django.conf.urls.defaults import *

urlpatterns = patterns('corehq.apps.groups.views',
    url(r'^add_group/$',
        'add_group',
        name='add_group'),
    url(r'^delete_group/(?P<group_id>[\w-]+)/$',
        'delete_group',
        name='delete_group'),
    url(r'^undo_delete_group/(?P<record_id>[\w-]+)/$',
        'undo_delete_group',
        name='undo_delete_group'),
    url(r'^edit_group/(?P<group_id>[\w-]+)/$',
        'edit_group',
        name='edit_group'),
    url(r'^update_group_data/(?P<group_id>[\w-]+)/$',
        'update_group_data',
        name='update_group_data'),
    url(r'^join_group/(?P<group_id>[\w-]+)/(?P<couch_user_id>[\w-]+)/$',
        'join_group',
        name='join_group'),
    url(r'^leave_group/(?P<group_id>[\w-]+)/(?P<couch_user_id>[\w-]+)/$',
        'leave_group',
        name='leave_group'),
)