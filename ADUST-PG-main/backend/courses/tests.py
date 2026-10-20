from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase

from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import LecturerProfile, StudentProfile
from fees.models import FeePayment
from .models import AcademicSession, Course, CourseAllocation, CourseMaterial, Enrollment, Programme, Timetable


class TimetableAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = AcademicSession.objects.create(
            name="2025/2026", is_current=True,
            start_date=date(2025, 10, 1), end_date=date(2026, 7, 31),
        )
        self.programme = Programme.objects.create(
            name="Computer Science", programme_type="MSC", duration_years=2,
        )
        self.course = Course.objects.create(
            code="CSC701", title="Advanced Computing", credit_units=3,
            semester="FIRST", programme=self.programme,
        )
        self.other_course = Course.objects.create(
            code="CSC702", title="Research Methods", credit_units=3,
            semester="FIRST", programme=self.programme,
        )
        User = get_user_model()
        self.admin = User.objects.create_user(
            email="admin@example.com", password="password123", role="ADMIN",
            first_name="Admin", last_name="User",
        )
        lecturer_user = User.objects.create_user(
            email="lecturer@example.com", password="password123", role="LECTURER",
            first_name="Ada", last_name="Lecturer",
        )
        student_user = User.objects.create_user(
            email="student@example.com", password="password123", role="STUDENT",
            first_name="Stu", last_name="Dent",
        )
        other_lecturer_user = User.objects.create_user(
            email="other@example.com", password="password123", role="LECTURER",
            first_name="Other", last_name="Lecturer",
        )
        self.lecturer = LecturerProfile.objects.create(
            user=lecturer_user, staff_id="L001", status="ACTIVE",
        )
        self.other_lecturer = LecturerProfile.objects.create(
            user=other_lecturer_user, staff_id="L002", status="ACTIVE",
        )
        self.student = StudentProfile.objects.create(
            user=student_user, programme="MSC", matric_number="M001",
            admission_year=2025, status="ACTIVE",
        )
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.lecturer, course=self.course, session=self.session,
            semester="FIRST",
        )
        self.other_allocation = CourseAllocation.objects.create(
            lecturer=self.other_lecturer, course=self.other_course, session=self.session,
            semester="FIRST",
        )
        Enrollment.objects.create(
            student=self.student, allocation=self.allocation, status="APPROVED",
        )

    def test_admin_can_create_update_list_and_delete_timetable(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/courses/admin/timetable/", {
            "allocation": self.allocation.id, "day": "MON",
            "start_time": "09:00", "end_time": "11:00", "venue": "Room 1",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        timetable_id = response.data["id"]

        listed = self.client.get("/api/courses/admin/timetable/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

        updated = self.client.patch(
            f"/api/courses/admin/timetable/{timetable_id}/",
            {"venue": "Room 2"},
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["venue"], "Room 2")

        deleted = self.client.delete(f"/api/courses/admin/timetable/{timetable_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Timetable.objects.filter(pk=timetable_id).exists())

    def test_timetable_clash_is_rejected(self):
        self.client.force_authenticate(self.admin)
        payload = {
            "allocation": self.allocation.id, "day": "TUE",
            "start_time": "09:00", "end_time": "11:00", "venue": "Room 1",
        }
        self.assertEqual(
            self.client.post("/api/courses/admin/timetable/", payload).status_code,
            status.HTTP_201_CREATED,
        )
        payload["allocation"] = self.other_allocation.id
        payload["start_time"] = "10:00"
        self.assertEqual(
            self.client.post("/api/courses/admin/timetable/", payload).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_student_and_lecturer_receive_only_relevant_entries(self):
        Timetable.objects.create(
            allocation=self.allocation, day="MON",
            start_time="09:00", end_time="11:00", venue="Room 1",
        )
        Timetable.objects.create(
            allocation=self.other_allocation, day="TUE",
            start_time="09:00", end_time="11:00", venue="Room 2",
        )

        self.client.force_authenticate(self.student.user)
        student_response = self.client.get("/api/courses/timetable/")
        self.assertEqual([item["allocation"] for item in student_response.data], [self.allocation.id])

        self.client.force_authenticate(self.lecturer.user)
        lecturer_response = self.client.get("/api/courses/timetable/")
        self.assertEqual([item["allocation"] for item in lecturer_response.data], [self.allocation.id])

    def test_unauthenticated_user_cannot_view_or_manage_timetable(self):
        self.assertEqual(
            self.client.get("/api/courses/timetable/").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.post("/api/courses/admin/timetable/", {}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_non_admin_cannot_manage_timetable(self):
        self.client.force_authenticate(self.lecturer.user)
        self.assertEqual(
            self.client.get("/api/courses/admin/timetable/").status_code,
            status.HTTP_403_FORBIDDEN,
        )


class CourseMaterialAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = AcademicSession.objects.create(
            name="2025/2026", is_current=True,
            start_date=date(2025, 10, 1), end_date=date(2026, 7, 31),
        )
        self.programme = Programme.objects.create(
            name="Computer Science", programme_type="MSC", duration_years=2,
        )
        self.course = Course.objects.create(
            code="CSC803", title="Distributed Systems", credit_units=3,
            semester="FIRST", programme=self.programme,
        )
        User = get_user_model()
        lecturer_user = User.objects.create_user(
            email="lecturer2@example.com", password="testpass123", role="LECTURER",
            first_name="Ada", last_name="Lecturer",
        )
        enrolled_user = User.objects.create_user(
            email="enrolled@example.com", password="testpass123", role="STUDENT",
            first_name="Enrolled", last_name="Student",
        )
        unenrolled_user = User.objects.create_user(
            email="unenrolled@example.com", password="testpass123", role="STUDENT",
            first_name="Unenrolled", last_name="Student",
        )
        self.lecturer = LecturerProfile.objects.create(
            user=lecturer_user, staff_id="L010", status="ACTIVE",
        )
        self.enrolled_student = StudentProfile.objects.create(
            user=enrolled_user, programme="MSC", matric_number="M010",
            admission_year=2025, status="ACTIVE",
        )
        self.unenrolled_student = StudentProfile.objects.create(
            user=unenrolled_user, programme="MSC", matric_number="M011",
            admission_year=2025, status="ACTIVE",
        )
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.lecturer, course=self.course, session=self.session,
            semester="FIRST",
        )
        Enrollment.objects.create(
            student=self.enrolled_student, allocation=self.allocation, status="APPROVED",
        )
        # Deliberately NO FeePayment is created for the enrolled student — this
        # proves materials access no longer depends on fee/session registration.
        self.material = CourseMaterial.objects.create(
            allocation=self.allocation, title="Lecture Notes 1",
            file=SimpleUploadedFile("notes.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
        )

    def test_enrolled_student_sees_material_without_fee_payment(self):
        """Approved enrollment alone must grant access — no FeePayment exists."""
        self.assertFalse(
            FeePayment.objects.filter(student=self.enrolled_student).exists()
        )
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Lecture Notes 1")
        self.assertEqual(response.data[0]["course_code"], "CSC803")

    def test_unenrolled_student_cannot_see_material(self):
        self.client.force_authenticate(self.unenrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "You are not enrolled in this course.")

    def test_rejected_fee_payment_does_not_block_access(self):
        """A REJECTED (or any) FeePayment must have no bearing on materials access."""
        FeePayment.objects.create(
            student=self.enrolled_student, academic_year=self.session.name,
            amount=1000, payment_method="MANUAL", status="REJECTED",
        )
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_access_materials(self):
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_lecturer_can_still_upload_material(self):
        self.client.force_authenticate(self.lecturer.user)
        upload = SimpleUploadedFile(
            "slides.pdf", b"%PDF-1.4 more test content", content_type="application/pdf"
        )
        response = self.client.post(
            f"/api/courses/materials/{self.allocation.id}/upload/",
            {"title": "Week 2 Slides", "file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Week 2 Slides")
        self.assertTrue(
            CourseMaterial.objects.filter(
                allocation=self.allocation, title="Week 2 Slides"
            ).exists()
        )

    def test_recent_materials_only_includes_allowed_allocations(self):
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get("/api/courses/materials/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.material.id)

        self.client.force_authenticate(self.unenrolled_student.user)
        response = self.client.get("/api/courses/materials/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_lecturer_can_see_own_allocation_material(self):
        self.client.force_authenticate(self.lecturer.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
