# accounts/forms.py の完全なコード

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="メールアドレス", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# --- ✨ ここが追加された部分！ ---
class ProfileImageForm(forms.ModelForm):
    """プロフィール画像アップロード専用のフォーム"""
    class Meta:
        model = User
        fields = ['profile_image']
# --- ✨ 追加ここまで！ ---