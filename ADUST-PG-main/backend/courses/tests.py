from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser, LecturerProfile, StudentProfile
from fees.models import FeePayment
from results.models import SemesterResultBatch
from .models import AcademicSession, Course, CourseAllocation, Programme, Enrollment


class AdminAcademicCrudTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="academic-admin@example.com",
            password="test-password",
            role=CustomUser.Role.ADMIN,
        )
        self.student_user = CustomUser.objects.create_user(
            email="academic-student@example.com",
            password="test-password",
            role=CustomUser.Role.STUDENT,
        )
        self.lecturer_user = CustomUser.objects.create_user(
            email="academic-lecturer@example.com",
            password="test-password",
            role=CustomUser.Role.LECTURER,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            programme=StudentProfile.Programme.MSC,
            matric_number="ADUST/PG/TEST/001",
            admission_year=2026,
            status=StudentProfile.Status.ACTIVE,
        )
        self.lecturer = LecturerProfile.objects.create(
            user=self.lecturer_user,
            staff_id="STAFF-TEST-001",
            status=LecturerProfile.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.admin)
        self.sessions_url = reverse("courses:admin_session_list")
        self.programmes_url = reverse("courses:admin_programme_list")
        self.courses_url = reverse("courses:admin_course_list")

    def create_session(self, **overrides):
        data = {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
            "is_current": False,
        }
        data.update(overrides)
        return AcademicSession.objects.create(**data)

    def create_programme(self, **overrides):
        data = {
            "name": "Computer Science",
            "programme_type": Programme.ProgrammeType.MSC,
            "duration_years": 2,
        }
        data.update(overrides)
        return Programme.objects.create(**data)

    def test_admin_can_create_read_update_and_delete_all_academic_records(self):
        session_response = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
            "is_current": True,
        }, format="json")
        self.assertEqual(session_response.status_code, status.HTTP_201_CREATED)
        session_id = session_response.data["id"]
        self.assertEqual(self.client.get(self.sessions_url).data[0]["name"], "2026/2027")
        self.assertEqual(
            self.client.get(reverse("courses:admin_session_detail", args=[session_id])).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(self.client.patch(
            reverse("courses:admin_session_detail", args=[session_id]),
            {"name": "2026/2028"},
            format="json",
        ).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(
            reverse("courses:admin_session_detail", args=[session_id])
        ).status_code, status.HTTP_204_NO_CONTENT)

        programme_response = self.client.post(self.programmes_url, {
            "name": "Computer Science",
            "programme_type": "MSC",
            "duration_years": 2,
            "description": "Postgraduate computing programme",
        }, format="json")
        self.assertEqual(programme_response.status_code, status.HTTP_201_CREATED)
        programme_id = programme_response.data["id"]
        self.assertEqual(self.client.get(self.programmes_url).data[0]["description"],
                         "Postgraduate computing programme")
        self.assertEqual(self.client.patch(
            reverse("courses:admin_programme_detail", args=[programme_id]),
            {"duration_years": 3},
            format="json",
        ).status_code, status.HTTP_200_OK)

        course_response = self.client.post(self.courses_url, {
            "code": "csc801",
            "title": "Advanced Computing",
            "credit_units": 3,
            "semester": "FIRST",
            "programme": programme_id,
            "is_elective": False,
            "is_active": True,
            "description": "Graduate-level course",
        }, format="json")
        self.assertEqual(course_response.status_code, status.HTTP_201_CREATED)
        course_id = course_response.data["id"]
        self.assertEqual(course_response.data["code"], "CSC801")
        self.assertEqual(course_response.data["programme_name"], "Computer Science")
        self.assertEqual(self.client.get(self.courses_url).data[0]["title"], "Advanced Computing")
        self.assertEqual(self.client.patch(
            reverse("courses:admin_course_detail", args=[course_id]),
            {"title": "Advanced Computing II"},
            format="json",
        ).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(
            reverse("courses:admin_course_detail", args=[course_id])
        ).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(
            reverse("courses:admin_programme_detail", args=[programme_id])
        ).status_code, status.HTTP_204_NO_CONTENT)

    def test_students_and_lecturers_cannot_access_any_admin_crud_operation(self):
        session = self.create_session()
        programme = self.create_programme()
        course = Course.objects.create(
            code="CSC801",
            title="Advanced Computing",
            credit_units=3,
            semester=Course.Semester.FIRST,
            programme=programme,
        )
        routes = (
            (self.sessions_url, reverse("courses:admin_session_detail", args=[session.pk])),
            (self.programmes_url, reverse("courses:admin_programme_detail", args=[programme.pk])),
            (self.courses_url, reverse("courses:admin_course_detail", args=[course.pk])),
        )
        for user in (self.student_user, self.lecturer_user):
            self.client.force_authenticate(user=user)
            for collection_url, detail_url in routes:
                self.assertEqual(self.client.get(collection_url).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.post(collection_url, {}, format="json").status_code,
                                 status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.patch(detail_url, {}, format="json").status_code,
                                 status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_required_duplicate_and_non_positive_inputs_are_rejected(self):
        self.assertEqual(self.client.post(self.sessions_url, {}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        invalid_dates = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2027-01-01",
            "end_date": "2026-12-31",
        }, format="json")
        self.assertEqual(invalid_dates.status_code, status.HTTP_400_BAD_REQUEST)
        self.create_session()
        duplicate_session = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
        }, format="json")
        self.assertEqual(duplicate_session.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(self.client.post(self.programmes_url, {
            "name": "Invalid Duration",
            "programme_type": "MSC",
            "duration_years": 0,
        }, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.create_programme()
        duplicate_programme = self.client.post(self.programmes_url, {
            "name": "computer science",
            "programme_type": "MSC",
            "duration_years": 2,
        }, format="json")
        self.assertEqual(duplicate_programme.status_code, status.HTTP_400_BAD_REQUEST)

        programme = Programme.objects.get(name="Computer Science")
        invalid_course = self.client.post(self.courses_url, {
            "code": "CSC801",
            "title": "Advanced Computing",
            "credit_units": 0,
            "semester": "FIRST",
            "programme": programme.pk,
        }, format="json")
        self.assertEqual(invalid_course.status_code, status.HTTP_400_BAD_REQUEST)
        Course.objects.create(
            code="CSC801",
            title="Advanced Computing",
            credit_units=3,
            semester=Course.Semester.FIRST,
            programme=programme,
        )
        duplicate_course = self.client.post(self.courses_url, {
            "code": "csc801",
            "title": "Different title",
            "credit_units": 3,
            "semester": "FIRST",
            "programme": programme.pk,
        }, format="json")
        self.assertEqual(duplicate_course.status_code, status.HTTP_400_BAD_REQUEST)

    def test_referenced_records_cannot_be_deleted_or_cascade_academic_history(self):
        session = self.create_session(is_current=True)
        programme = self.create_programme()
        course = Course.objects.create(
            code="CSC801",
            title="Advanced Computing",
            credit_units=3,
            semester=Course.Semester.FIRST,
            programme=programme,
        )
        allocation = CourseAllocation.objects.create(
            lecturer=self.lecturer,
            course=course,
            session=session,
            semester=Course.Semester.FIRST,
        )
        enrollment = Enrollment.objects.create(
            student=self.student,
            allocation=allocation,
            status=Enrollment.Status.APPROVED,
        )
        result_batch = SemesterResultBatch.objects.create(
            session=session,
            semester=Course.Semester.FIRST,
            programme_type=Programme.ProgrammeType.MSC,
        )

        session_delete = self.client.delete(reverse("courses:admin_session_detail", args=[session.pk]))
        self.assertEqual(session_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("referenced", session_delete.data["detail"])
        self.assertTrue(AcademicSession.objects.filter(pk=session.pk).exists())
        self.assertTrue(SemesterResultBatch.objects.filter(pk=result_batch.pk).exists())
        self.assertTrue(Enrollment.objects.filter(pk=enrollment.pk).exists())

        FeePayment.objects.create(
            student=self.student,
            academic_year=session.name,
            amount="100.00",
            payment_method=FeePayment.PaymentMethod.MANUAL,
        )
        rename_response = self.client.patch(
            reverse("courses:admin_session_detail", args=[session.pk]),
            {"name": "2026/2028"},
            format="json",
        )
        self.assertEqual(rename_response.status_code, status.HTTP_200_OK)
        self.assertTrue(FeePayment.objects.filter(academic_year="2026/2028").exists())
        session_delete = self.client.delete(reverse("courses:admin_session_detail", args=[session.pk]))
        self.assertEqual(session_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("fee payments", session_delete.data["detail"])

        programme_delete = self.client.delete(reverse("courses:admin_programme_detail", args=[programme.pk]))
        self.assertEqual(programme_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Programme.objects.filter(pk=programme.pk).exists())
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())

        course_delete = self.client.delete(reverse("courses:admin_course_detail", args=[course.pk]))
        self.assertEqual(course_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())
        self.assertTrue(CourseAllocation.objects.filter(pk=allocation.pk).exists())
