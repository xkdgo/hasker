from django.shortcuts import render


def about(request):
    return render(request, 'hasker/about.html', {'title': 'About'})
