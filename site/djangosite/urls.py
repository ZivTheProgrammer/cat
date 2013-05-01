from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('djangosite.views',
    url(r'^$', 'home', name='home'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^results/$', 'search_results', name='search_results'),
    url(r'^semester/$', 'get_semester', name='get_semester'),
    url(r'^index/$', 'index', name='index'),
    url(r'^course/add/$', 'add_course_cart', name='add_course_cart'),
    url(r'^course/remove/$', 'remove_course_cart', name='remove_course_cart'),
    url(r'^reviews/$', 'get_reviews', name='get_reviews'),

    
    # Examples:
    # url(r'^djangosite/', include('djangosite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
