from django.conf.urls import patterns, include, url
from django.conf import settings
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('djangosite.views',
    url(r'^$', 'home', name='home'),
    url(r'^about/', 'about', name='about'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^results/$', 'search_results', name='search_results'),
    url(r'^semester/$', 'get_semester', name='get_semester'),
    url(r'^index/$', 'index', name='index'),
    url(r'^course/add/$', 'add_course_cart', name='add_course_cart'),
    url(r'^course/remove/$', 'remove_course_cart', name='remove_course_cart'),
    url(r'^reviews/$', 'get_reviews', name='get_reviews'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

# Uncomment the next two lines if static files fail to load with DEBUG=False
# if settings.DEBUG is False:
#    urlpatterns += patterns('', url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),)