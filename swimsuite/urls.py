from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'pool.views.home', name='index'),
    url(r'^log$', 'pool.views.log', name='index'),
    url(r'^today$', 'pool.views.todayfig', name='index'),
    url(r'^todayfig$', 'pool.views.todayfig', name='index'),
    url(r'^week$', 'pool.views.weekfig', name='week'),
    url(r'^weekfig$', 'pool.views.weekfig', name='week'),
    url(r'^status$', 'pool.views.status', name='index'),
    url(r'^control$', 'pool.views.control', name='control'),
    url(r'^stats$', 'pool.views.stats', name='stats'),
    url(r'^apple.*$', 'pool.views.icon', name='icon'),

    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),

)
