from django import forms
from django_summernote.widgets import SummernoteWidget

class EmailForm(forms.Form):
    emailcontent = forms.CharField(widget=SummernoteWidget())
