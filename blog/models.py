import datetime

# Model
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.forms import ModelForm
# ckeditor
from ckeditor.fields import RichTextField

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=10, null=True, blank=True)
    
    def __str__(self):
        return self.nickname

class Post(models.Model):
    title=models.CharField(max_length=100)
    abstract=models.TextField(max_length=280) # as Twitter
    body = RichTextField(blank=True, null=True)
    last_edition=models.DateTimeField(auto_now_add=True)
    author=models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return ' Titulo: {title} /|\ Autor: {author}'.format(
            author=self.author.nickname,
            title=self.title
        )
    
    def get_absolute_url(self):
        return reverse('article', args=(str(self.id)) )


    class Meta:
        ordering = ['last_edition']

class ArticleForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'abstract', 'body']

