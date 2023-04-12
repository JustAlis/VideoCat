from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Channel, Video, Playlist, Comment
from datetime import date

#date widget as sugested django documentation
class DateSelectorWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        days = [(day, day) for day in range(1, 32)]
        months = [(month, month) for month in range(1, 13)]
        years = [(year, year) for year in range(1900, 2024)]
        widgets = [
            forms.Select(attrs=attrs, choices=days),
            forms.Select(attrs=attrs, choices=months),
            forms.Select(attrs=attrs, choices=years),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        elif isinstance(value, str):
            year, month, day = value.split('-')
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        day, month, year = super().value_from_datadict(data, files, name)
        # DateField expects a single string that it can parse into a date.
        return '{}-{}-{}'.format(year, month, day)

#I do really think, that there is nothing to talk about here.
#Just forms and fields, nothing special
sex_choises = (
('M', 'Male'),
('F', 'Female'),
('O', 'Other'),
('N', 'Not staded')
)

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'register_form'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'register_form'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'register_form'}))
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'register_form'}))


    sex = forms.CharField(label='Пол', widget=forms.Select(choices=sex_choises, attrs={'class': 'register_form'}))
    date_of_birth = forms.DateField(label='Дата рождения',widget=DateSelectorWidget)

    class Meta:
        model = Channel
        fields = ('username', 'email', 'password1', 'password2', 'sex', 'date_of_birth')

class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'login_form'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'login_form'}))



class AddVideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['cat', 'video_title', 'content', 'preview', 'description', 'published']

class AddPlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['playlist_name', 'playlist_picture']


class ChangeChannel(forms.ModelForm):
    date_of_birth = forms.DateField(label='Дата рождения',widget=DateSelectorWidget)
    description = forms.CharField(label='Описание', widget=forms.Textarea(attrs={'cols': 60, 'rows': 10}), required=False)
    sex = forms.CharField(label='Пол', widget=forms.Select(choices=sex_choises, attrs={'class': 'register_form'}))
    avatar = forms.ImageField(label='Аватар', required=False)
    hat = forms.ImageField(label='Шапка', required=False)
    class Meta:
        model = Channel
        fields = ['date_of_birth', 'description', 'hat', 'avatar', 'description', 'sex']

class ChangePlaylist(forms.ModelForm):
    playlist_picture = forms.ImageField(label='Фотография плейлиста', required=False)
    playlist_name = forms.CharField(label='Имя плейлиста', widget=forms.TextInput(attrs={'class': 'register_form'}))
    hidden = forms.BooleanField(label='Скрытый плейлист', required=False)
    class Meta:
        model = Playlist
        fields = ['playlist_picture', 'playlist_name', 'hidden']

class ChangeVideo(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['cat', 'video_title', 'preview', 'description', 'published']