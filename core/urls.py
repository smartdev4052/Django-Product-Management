from django.conf.urls import handler400, handler403, handler404, handler500
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from account.views import Register, RegisterInvite, login_page
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import i18n_patterns

# for private
import private_storage.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    # Media file
    path('private-media/', include(private_storage.urls)),


]

urlpatterns += i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),
    # AUTH
    path('register', Register, name='register'),
    path('login', login_page, name='login'),
    path('logout/', auth_views.LogoutView.as_view(),
         {'next_page': 'main:start'}, name='logout'),

    # PW reset
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='password_reset/password_change_done.html'), name='password_change_done'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='password_reset/password_change.html'), name='password_change'),
    path('password_reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset/password_reset_form.html'), name='password_reset'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset/password_reset_complete.html'), name='password_reset_complete'),


    # Invite
    path('register/invite/<token>', RegisterInvite, name='register_invite'),

    path('shop/', include('shop.urls')),
    path('account/', include('account.urls')),
    path('order/', include('order.urls')),
    path('client/', include('client.urls')),
    path('project/', include('project.urls')),
    path('notification/', include('notification.urls')),
    path('', include('main.urls')),
    prefix_default_language=False
)


# Error Handling
handler400 = 'main.views.handler_400_view'
handler403 = 'main.views.handler_403_view'
handler404 = 'main.views.handler_404_view'
handler500 = 'main.views.handler_500_view'

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
