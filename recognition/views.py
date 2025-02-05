from django.shortcuts import render

# Create your views here.
import os
import cv2
import numpy as np
import face_recognition
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import path
from django.db import models
from .models import Attendance, Employee
from django.shortcuts import render, redirect
from .models import Employee
from .forms import EmployeeForm

def submit_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('recognition:submit_employee')  # Redirect to the same page after submission
    else:
        form = EmployeeForm()
    
    return render(request, 'submit_employee.html', {'form': form})

def load_known_faces():
    """Loads known faces from the database."""
    employees = Employee.objects.all()
    known_encodings = []
    known_names = []
    
    for emp in employees:
        image_path = emp.photo.path  # Assuming photo is an ImageField
        image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(image)
        
        if encoding:
            known_encodings.append(encoding[0])
            known_names.append(emp.name)
    
    return known_encodings, known_names

def recognize_face(request):
    """Capture and recognize face, then log attendance."""
    known_encodings, known_names = load_known_faces()
    
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return JsonResponse({'status': 'error', 'message': 'Camera error'})
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"
        
        if True in matches:
            match_index = np.where(matches)[0][0]
            name = known_names[match_index]
            
            # Log attendance
            employee = Employee.objects.get(name=name)
            Attendance.objects.create(employee=employee)
            
            return JsonResponse({'status': 'success', 'message': f'Attendance recorded for {name}'})
    
    return JsonResponse({'status': 'error', 'message': 'Face not recognized'})