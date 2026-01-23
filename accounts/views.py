from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.is_superuser:
                return redirect("/admin-dashboard/")
            elif user.groups.filter(name="Manager").exists():
                return redirect("/manager-dashboard/")
            else:
                return redirect("/staff-dashboard/")

    return render(request, "login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')