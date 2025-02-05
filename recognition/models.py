from django.db import models

# Create your models here.
# models.py
class Employee(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='employees/')

    def __str__(self):
        return self.name

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.employee.name} - {self.timestamp}'