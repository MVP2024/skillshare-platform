from django.contrib import admin

from materials.models import Course, CourseSubscription, Lesson

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(CourseSubscription)
