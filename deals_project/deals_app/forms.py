from django import forms
from .models import Category

categoriesExists = Category.objects.filter().exists()
categoryChoices = []

if categoriesExists:
    categories = Category.objects.filter()
    for category in categories:
        categoryChoices.append((category.pk, category.name))


class DateInput(forms.DateInput):
    input_type = 'date'

class PostForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea, max_length=200)
    category = forms.ChoiceField(choices=categoryChoices)
    address_line_1 = forms.CharField(max_length=200)
    address_line_2 = forms.CharField(max_length=200)
    postcode_code = forms.IntegerField()
    postcode_text = forms.CharField(max_length=200)
    expiration_date = forms.DateField(widget=DateInput)
    lng = forms.FloatField()
    lat = forms.FloatField()    
    region_code = forms.IntegerField()

