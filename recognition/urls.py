from django.urls import path

from recognition.views import *

app_name = "recognition"
# urls.py
urlpatterns = [
    path('recognize/', recognize_face, name='recognize_face'),
    path('submit-employee/', submit_employee, name='submit_employee'),
]