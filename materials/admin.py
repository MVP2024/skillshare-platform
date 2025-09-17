from django.contrib import admin

from materials.models import Course, CourseSubscription, Lesson


class CourseAdmin(admin.ModelAdmin):
    """
    Класс для настройки отображения модели Course в админ-панели.
    Добавляет отображение общей стоимости курса.
    """

    list_display = (
        "title",
        "course_user",
        "fixed_price",
        "calculated_price_display",
        "actual_price_display",
    )
    # Добавим 'fields' для контроля порядка и включения полей на странице изменения
    fields = (
        "title",
        "preview",
        "description",
        "course_user",
        "fixed_price",
        "calculated_price_display",
        "actual_price_display",
    )
    readonly_fields = (
        "calculated_price_display",
        "actual_price_display",
    )

    def calculated_price_display(self, obj):
        """Метод для отображения расчетной стоимости курса по урокам в админ-панели."""
        return f"{obj.calculated_price_from_lessons:.2f} руб."

    calculated_price_display.short_description = "Стоимость по урокам"

    def actual_price_display(self, obj):
        """Метод для отображения общей стоимости курса в админ-панели."""
        return f"{obj.actual_price:.2f} руб."  # Форматируем как валюту

    actual_price_display.short_description = "Стоимость курса (фактическая)"


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson)
admin.site.register(CourseSubscription)
