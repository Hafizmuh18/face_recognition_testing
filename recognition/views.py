from django.shortcuts import redirect, render
from django.http import JsonResponse
from datetime import datetime
from recognition.forms import EmployeeForm
from .models import Attendance, Employee
import face_recognition
import numpy as np
import cv2
import io
from PIL import Image
from django.views.decorators.csrf import csrf_exempt
import threading

# Global cache for known face encodings
cached_encodings = None
lock = threading.Lock()


def load_known_faces():
    """Load known face encodings once and cache them for performance."""
    global cached_encodings

    with lock:  # Thread-safe access
        if cached_encodings is None:  # Load only once
            employees = Employee.objects.all()
            known_encodings = []
            known_names = []

            for emp in employees:
                image_path = emp.photo.path
                image = face_recognition.load_image_file(image_path)
                encoding = face_recognition.face_encodings(image)

                if encoding:
                    known_encodings.append(encoding[0])
                    known_names.append(emp.name)

            cached_encodings = (known_encodings, known_names)

    return cached_encodings


@csrf_exempt
def recognize_face(request):
    """Recognizes faces from an uploaded image and sends a redirect URL in JSON."""
    if request.method != 'POST' or 'image' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    # Read image from request
    image_file = request.FILES['image']
    image = Image.open(image_file).convert('RGB')  # Ensure RGB format
    image = np.array(image)

    # Convert image to RGB (if not already in RGB format)
    rgb_frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Load known faces (cached)
    known_encodings, known_names = load_known_faces()

    # Resize image before face detection for speed
    scale_factor = 0.5  # Adjust to speed up processing
    small_rgb_frame = cv2.resize(rgb_frame, (0, 0), fx=scale_factor, fy=scale_factor)

    # Detect faces in the smaller image (faster processing)
    face_locations = face_recognition.face_locations(small_rgb_frame, model="hog")

    # Adjust face coordinates back to original size
    face_locations = [(int(top / scale_factor), int(right / scale_factor), int(bottom / scale_factor), int(left / scale_factor))
                      for (top, right, bottom, left) in face_locations]

    # Encode faces
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return JsonResponse({'status': 'error', 'message': 'No face detected'})

    for face_encoding in face_encodings:
        # Use face distance instead of compare_faces (more efficient)
        distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(distances)

        if distances[best_match_index] < 0.5:  # Lower threshold = stricter match
            name = known_names[best_match_index]

            try:
                employee = Employee.objects.get(name=name)
                Attendance.objects.create(employee=employee)
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Store in session
                request.session['recognized_name'] = name
                request.session['recognized_time'] = current_time

                return JsonResponse({'status': 'success', 'redirect_url': '/recognized_face/'})

            except Employee.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Employee record not found'})

    return JsonResponse({'status': 'error', 'message': 'Face not recognized'})


def recognized_face(request):
    """Display the recognized face information."""
    name = request.session.get('recognized_name', 'Unknown')
    time = request.session.get('recognized_time', 'N/A')

    return render(request, 'recognized_face.html', {'name': name, 'time': time})


def index(request):
    """Render the page with the camera view and real-time recognition."""
    return render(request, 'index.html')


def submit_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('recognition:submit_employee')
    else:
        form = EmployeeForm()

    return render(request, 'submit_employee.html', {'form': form})
