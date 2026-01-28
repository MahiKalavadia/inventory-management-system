from django import forms
from django.contrib.auth.models import User, Group


class AddUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(
        choices=(('Manager', 'Manager'), ('Staff', 'Staff')))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            group = Group.objects.get(name=self.cleaned_data['role'])
            user.groups.add(group)
        return user


class UpdateUserForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=(('Manager', 'Manager'), ('Staff', 'Staff')))

    class Meta:
        model = User
        fields = ['username', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Remove old groups and assign new
            user.groups.clear()
            group = Group.objects.get(name=self.cleaned_data['role'])
            user.groups.add(group)
        return user


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput, label="New Password")
