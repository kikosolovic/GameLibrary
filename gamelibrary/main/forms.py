from django import forms
from .models import Users, GENRE_CHOICES, GENDER_CHOICES
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
        choices=GENRE_CHOICES,
        widget=forms.Select(attrs={'required': 'required'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'required': 'required'})
    )
    
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


class ProfileForm(forms.ModelForm):
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Users
        fields = [
            'username',
            'email',
            'bio',
            'favourite_genre',
            'gender',
            'favorite_game',
            'currently_playing',
            'avatar',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'bio': forms.Textarea(attrs={'placeholder': 'A short bio, 2-3 sentences', 'rows': 3}),
            'favorite_game': forms.TextInput(attrs={'placeholder': 'Favorite game title'}),
            'currently_playing': forms.TextInput(attrs={'placeholder': 'What are you currently playing?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} profile-input".strip()
        # Textarea tweaks
        if 'bio' in self.fields:
            self.fields['bio'].widget.attrs.setdefault('rows', 3)
            self.fields['bio'].widget.attrs.setdefault('class', 'profile-input profile-textarea')
        if 'avatar' in self.fields:
            self.fields['avatar'].widget.attrs.setdefault('accept', 'image/*')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = Users.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Username already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = Users.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Email already in use.")
        return email
