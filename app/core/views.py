from django.shortcuts import render, redirect
from core import forms


def set_password(request):
    if request.method == 'POST':
        form = forms.SetPasswordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')

        return render(request, template_name='registration/set_password.html', context={'form': form})
    else:
        return render(request, template_name='registration/set_password.html', context={'form': forms.SetPasswordForm()})


def registration(request):
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')

        return render(request, template_name='registration/registration.html', context={'form': form})
    else:
        return render(request, template_name='registration/registration.html', context={'form': forms.RegistrationForm()})
