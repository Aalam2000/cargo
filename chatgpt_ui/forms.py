from django import forms

class ChatForm(forms.Form):
    message = forms.CharField(label='Ваше сообщение', max_length=500,
                              widget=forms.TextInput(attrs={
                                  'class': 'form-control',
                                  'placeholder': 'Введите ваш запрос...',
                              }))