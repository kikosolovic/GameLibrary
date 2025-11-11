from django import forms
from .models import Users
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder':'Email', 'required':'required'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username', 'required':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password', 'required':'required'}))
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder':'Repeat Password', 'required':'required'})
    )
    favourite_genre = forms.ChoiceField(
    choices=[('action', 'Action'),
    ('adventure', 'Adventure'),
    ('rpg', 'RPG'),
    ('strategy', 'Strategy'),
    ('simulation', 'Simulation'),
    ('sports', 'Sports'),
    ('racing', 'Racing'),
    ('horror', 'Horror'),
    ('indie', 'Indie'),],
    widget=forms.Select(attrs={'required':'required'}))
    gender = forms.ChoiceField(choices=[('M','Male'),('F','Female')],
                               widget=forms.Select(attrs={'required':'required'}))
    
    class Meta:
        model = Users
        fields = ['email', 'username', 'password', 'favourite_genre', 'gender']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise ValidationError("Passwords do not match.")

        return cleaned_data
    
    def save(self, commit = True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username', 'required':'required', 'autocomplete':'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password', 'required':'required', 'autocomplete':'current-password'}))    