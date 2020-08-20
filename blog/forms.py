from django import forms
from blog.models import Post

class PostForm(forms.Form):
    title = forms.CharField(label='title', max_length=100)
    abstract = forms.CharField(label='abstract', max_length=280)
    body = forms.CharField(widget=forms.Textarea)
    
    def clean(self):
        cleaded_data = super().clean()
        return cleaded_data

class singUp(forms.Form):
    user_name = forms.CharField(label='Name', max_length=20)
    last_name = forms.CharField(label='Last Name', max_length=20)
    contact_phone_or_email = forms.CharField(label='Password or phone')
    birth_day = forms.DateTimeField(label='Birthday')


class  PostFormBase(forms.ModelForm):
    class Meta:
        model=Post
        fields=('title', 'abstract', 'body')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titulo de tu Articulo'}),
            'abstract': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resumen para redes sociales'}),
           
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contenido del articulo'}),        
        }

class PostFormModel(PostFormBase):
    class Meta:
        model=Post
        fields=('title', 'abstract', 'author', 'body')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titulo de tu Articulo'}),
            'abstract': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resumen para redes sociales'}),
            'author': forms.Select(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contenido del articulo'}),        
        }

class PostFormEditModel(PostFormBase):
    class Meta:
        model=Post
        fields=('title', 'abstract', 'body')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titulo de tu Articulo'}),
            'abstract': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resumen para redes sociales'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contenido del articulo'}),        
        }