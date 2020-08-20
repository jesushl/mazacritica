from django.urls import path

from . import views
# Views
from blog.views import new_article
from blog.views import article
# class view
from blog.views import ArticleListView
from blog.views import AddPostView
from blog.views import EditArticle
from blog.views import DeleteArticle

urlpatterns = [
    path('', views.articles, name='articles'),
    path('new_article', new_article, name='new_article'),
    path('article/<int:pk>', article, name='article'),
    path('artilcelist/',ArticleListView.as_view(), name='artilces_list'),
    path('new_article_2', AddPostView.as_view(),  name='new_article_2' ),
    path('edit_article/<int:pk>', EditArticle.as_view(), name='edit_article' ),
    path('article/<int:pk>/remove', DeleteArticle.as_view(), name='delete_article' ),
]
