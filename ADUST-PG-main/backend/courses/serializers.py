from rest_framework import serializers
from .models import AcademicSession, Programme, Course, CourseAllocation, Timetable, Enrollment, CourseMaterial


class AcademicSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicSession
        fields = ["id", "name", "is_current", "start_date", "end_date"]


class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = ["id", "name", "programme_type", "duration_years"]


class CourseSerializer(serializers.ModelSerializer):
    programme_name = serializers.CharField(source="programme.name", read_only=True)

    class Meta:
        model = Course
        fields = ["id", "code", "title", "credit_units", "semester", "programme",
                  "programme_name", "is_elective", "is_active"]


class CourseAllocationSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    programme_name = serializers.CharField(source="course.programme.name", read_only=True)
    credit_units = serializers.IntegerField(source="course.credit_units", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    session_name = serializers.CharField(source="session.name", read_only=True)
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseAllocation
        fields = ["id", "course", "course_code", "course_title", "credit_units",
                  "programme_name", "lecturer", "lecturer_name", "session", "session_name", "semester",
                  "enrolled_count"]

    def get_lecturer_name(self, obj):
        return obj.lecturer.user.get_full_name()

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status="APPROVED").count()


class AvailableAllocationSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    credit_units = serializers.IntegerField(source="course.credit_units", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    session_name = serializers.CharField(source="session.name", read_only=True)
    already_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = CourseAllocation
        fields = ["id", "course", "course_code", "course_title", "credit_units",
                  "lecturer", "lecturer_name", "session", "session_name", "semester",
                  "already_enrolled"]

    def get_lecturer_name(self, obj):
        return obj.lecturer.user.get_full_name()

    def get_already_enrolled(self, obj):
        return obj.id in self.context.get("enrolled_allocation_ids", set())


class TimetableSerializer(serializers.ModelSerializer):
    allocation_detail = CourseAllocationSerializer(source="allocation", read_only=True)

    class Meta:
        model = Timetable
        fields = ["id", "allocation", "allocation_detail", "day", "start_time", "end_time", "venue"]

    def validate(self, data):
        if self.instance is not None:
            instance = Timetable(
                pk=self.instance.pk,
                allocation=data.get("allocation", self.instance.allocation),
                day=data.get("day", self.instance.day),
                start_time=data.get("start_time", self.instance.start_time),
                end_time=data.get("end_time", self.instance.end_time),
                venue=data.get("venue", self.instance.venue),
            )
        else:
            instance = Timetable(**data)
        try:
            instance.clean()
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data


class EnrollmentSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="allocation.course.code", read_only=True)
    course_title = serializers.CharField(source="allocation.course.title", read_only=True)
    credit_units = serializers.IntegerField(source="allocation.course.credit_units", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    matric_number = serializers.CharField(source="student.matric_number", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_name", "matric_number", "allocation", "course_code", "course_title",
                  "credit_units", "lecturer_name", "status", "enrolled_at"]
        read_only_fields = ["id", "student", "status", "enrolled_at"]

    def get_lecturer_name(self, obj):
        return obj.allocation.lecturer.user.get_full_name()

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()


class CourseMaterialSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="allocation.course.code", read_only=True)
    course_title = serializers.CharField(source="allocation.course.title", read_only=True)

    class Meta:
        model = CourseMaterial
        fields = ["id", "allocation", "course_code", "course_title", "title", "description", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at", "course_code", "course_title"]
