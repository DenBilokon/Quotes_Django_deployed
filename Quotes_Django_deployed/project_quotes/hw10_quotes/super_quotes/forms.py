from django.forms import ModelForm, CharField, TextInput, DateField, SelectMultiple, \
    ModelChoiceField, Select, ModelMultipleChoiceField
from .models import Author, Quote, Tag


class AuthorForm(ModelForm):
    fullname = CharField(max_length=50, required=True, widget=TextInput(attrs={"class": "form-control"}))
    date_born = DateField(widget=TextInput(attrs={"class": "form-control"}))
    born_location = CharField(max_length=200, required=True, widget=TextInput(attrs={"class": "form-control"}))
    bio = CharField(required=True, widget=TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = Author
        fields = ['fullname', 'date_born', 'born_location', 'bio']


class QuoteForm(ModelForm):
    quote = CharField(required=True, widget=TextInput(attrs={"class": "form-control"}))
    tags = ModelMultipleChoiceField(queryset=Tag.objects.all().order_by('name'),
                                    widget=SelectMultiple(attrs={'class': 'form_control', 'size': 10}))
    author = ModelChoiceField(queryset=Author.objects.all().order_by('fullname'),
                              widget=Select(attrs={"class": "form-select"}))

    class Meta:
        model = Quote
        fields = ['author', 'tags', 'quote']


class TagForm(ModelForm):
    name = CharField(max_length=50, required=True, widget=TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = Tag
        fields = ['name']
