from django import forms
from django.contrib.auth import  get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UsernameField, capfirst

class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set their password without entering the old
    password
    """

    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True}))

    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username_field = get_user_model()._meta.get_field(get_user_model().USERNAME_FIELD)
        username_max_length = self.username_field.max_length or 254
        self.fields["username"].max_length = username_max_length
        self.fields["username"].widget.attrs["maxlength"] = username_max_length
        if self.fields["username"].label is None:
            self.fields["username"].label = _(capfirst(self.username_field.verbose_name))
        self.user = None
        
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if get_user_model().objects.filter(**{get_user_model().USERNAME_FIELD: username}).exists():
            self.user = get_user_model().objects.get(**{get_user_model().USERNAME_FIELD: username})
        else:
            raise ValidationError(
                _('User does not exist')
            )
        return username

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    self.error_messages["password_mismatch"],
                    code="password_mismatch",
                )
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class RegistrationForm(forms.Form):

    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }

    email = forms.EmailField(
            label=_("Email"),
            widget=forms.EmailInput(attrs={"autocomplete": "email"}),
            help_text=_("Enter your email."),
    )
    phone_number = forms.CharField(
            label=_("Phone number"),
            widget=forms.TextInput(attrs={"autocomplete": "phone"}),
            help_text=_("Enter your phone number."),
    )
    name = forms.CharField(
            label=_("Name"),
            widget=forms.TextInput(attrs={"autocomplete": "name"}),
            help_text=_("Enter your first and second name."),
    )
    new_password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Repeat password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "password"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != '':
            if get_user_model().objects.filter(email=email).exists():
                raise ValidationError(_('Email is busy'))
            
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if get_user_model().objects.filter(phone_number=phone_number).exists():
            raise ValidationError(_('Phone number is busy'))
            
        return phone_number

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def save(self, commit=True):
        phone_number = self.cleaned_data["phone_number"]
        email = self.cleaned_data["email"]
        name = self.cleaned_data["name"]
        password = self.cleaned_data["new_password1"]
        
        user = get_user_model().objects.create(phone_number=phone_number, email=email, name=name)
        user.set_password(password)

        if commit:
            user.save()
        return user
    

class DashboardUserForm(forms.Form):
    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }
        
    email = forms.EmailField(
            label=_("Email"),
            widget=forms.EmailInput(attrs={"autocomplete": "email"}),
            required=False
    )   
    phone_number = forms.CharField(
            label=_("Phone number"),
            widget=forms.TextInput(attrs={"autocomplete": "phone"}),
    )
    name = forms.CharField(
            label=_("Name"),
            widget=forms.TextInput(attrs={"autocomplete": "name"}),
            required=False
    )
    new_password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
        required=False,
    )
    note = forms.CharField(
        label=_('Note'),
        widget=forms.Textarea(),
        required=False
    )
    is_staff = forms.BooleanField(
        label=_('Staff'),
        widget=forms.CheckboxInput(),
        required=False
    )
    allow_credit = forms.BooleanField(
        label=_('Allow credit'),
        widget=forms.CheckboxInput(),
        required=False
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user is not None:
            self.fields['email'].initial = self.user.email if self.user.email is not None else ''
            self.fields['phone_number'].initial = self.user.phone_number
            self.fields['name'].initial = self.user.name
            self.fields['note'].initial = self.user.note
            self.fields['is_staff'].initial = self.user.is_staff
            self.fields['allow_credit'].initial = self.user.allow_credit

            self.fields['new_password'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            if self.user is not None and self.user.email != email:
                raise ValidationError(_('Email is busy'))
        return email.strip()

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise ValidationError(_('Phone number must contain only numbers'))
        if get_user_model().objects.filter(phone_number=phone_number).exists():
            if self.user is None or self.user.phone_number != phone_number:
                raise ValidationError(_('Phone number is busy'))
            
        return phone_number

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        if self.user is None and len(password) < 8:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password

    def save(self, commit=True):
        phone_number = self.cleaned_data["phone_number"]
        email = self.cleaned_data["email"]
        name = self.cleaned_data["name"]
        password = self.cleaned_data["new_password"]
        note = self.cleaned_data['note']
        is_staff = self.cleaned_data['is_staff']
        allow_credit = self.cleaned_data['allow_credit']

        if email == '':
            email = None

        if self.user is None:
            self.user = get_user_model().objects.create(phone_number=phone_number, email=email, name=name, note=note, is_staff=is_staff, allow_credit=allow_credit)
            self.user.set_password(password)
        else:
            self.user.phone_number = phone_number
            self.user.email = email
            self.user.name = name
            self.user.note = note
            self.user.is_staff = is_staff
            self.user.allow_credit = allow_credit

        if commit:
            self.user.save()
        return self.user
