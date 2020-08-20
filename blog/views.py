from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.http import HttpResponseRedirect
#404#
from django.shortcuts import get_object_or_404, render
# models
from blog.models import Post
from blog.models import Author
# generic views
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.base import logging
# forms
from blog.forms import PostForm
from blog.forms import PostFormModel
from blog.forms import PostFormEditModel
# generic
from django.views.generic import ListView
# URLS
from django.urls import reverse_lazy
# Authentication
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


def articles(request):
    latest_articles_list = Post.objects.order_by("-last_edition")[:10]
    context = {'articles': latest_articles_list}
    return render(request, 'blog/articles.html', context)

@login_required(login_url='members/login')
def new_article(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            default_author = Author.objects.filter(nikname='Anonymous')[0]
            article_title = form.cleaned_data['title']
            article_content = form.cleaned_data['content']
            article_abstract = form.cleaned_data['abstract']
            _ = Post(
                title=article_title,
                content=article_content,
                abstract=article_abstract,
                author=default_author
            ).save() 
            return redirect('articles')
        else:
            print('Article is not valid')
    else:
        form = PostForm()
    return render(request, 'blog/new_article.html', {'form': form})

def article(request, pk):
    article = get_object_or_404(Post,pk=pk)
    return render(request, 'blog/article.html', {'article': article})


# Views object based

class NewArticleView(LoginRequiredMixin, FormView):
    template_name = 'blog/new_article.html'
    form_class = PostForm
    login_url = '/members/login/'
    redirect_field_name = 'redirect_to'


class ArticleListView(ListView):
    model  = Post
    template_name = 'blog/articles_list.html'

class AddPostView(LoginRequiredMixin,CreateView):
    model = Post
    form_class = PostFormModel
    template_name = 'blog/new_article2.html'
    login_url = '/members/login/'
    redirect_field_name = 'redirect_to'

class EditArticle(LoginRequiredMixin, UpdateView):
    model = Post 
    template_name = 'blog/update_article.html'
    form_class = PostFormEditModel
    login_url = '/members/login/'
    redirect_field_name = 'redirect_to'

class DeleteArticle(LoginRequiredMixin, DeleteView):
    model = Post
    template_name='blog/delete_article.html'
    success_url = reverse_lazy('articles')
    login_url = '/members/login/'
    redirect_field_name = 'redirect_to'