from django.http import HttpResponse
from django.shortcuts import render

from judge.forms import EditorForm


# Create your views here.

def index(request):
    return HttpResponse('Hello World You fucking gay.')


def submit(request, task_id):
    if request.method == "POST":
        form = EditorForm(request.POST)
        if form.is_valid():
            return HttpResponse(form.data.get('source'), headers={
                'Content-Type': 'text/plain',
            })
    else:
        form = EditorForm()
    return render(request, 'judge/submit.html', {'form': form})
