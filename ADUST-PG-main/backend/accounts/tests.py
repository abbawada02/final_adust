from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser, LecturerProfile, StudentProfile


class AdminAccountListTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email='admin-list@example.com',
            password='test-password',
            role=CustomUser.Role.ADMIN,
        )
        self.student_user = CustomUser.objects.create_user(
            email='student-list@example.com',
            password='test-password',
            first_name='Amina',
            last_name='Pending',
            role=CustomUser.Role.STUDENT,
        )
        self.active_student_user = CustomUser.objects.create_user(
            email='active-student@example.com',
            password='test-password',
            first_name='Bala',
            last_name='Active',
            role=CustomUser.Role.STUDENT,
        )
        self.suspended_student_user = CustomUser.objects.create_user(
            email='suspended-student@example.com',
            password='test-password',
            first_name='Chika',
            last_name='Suspended',
            role=CustomUser.Role.STUDENT,
        )
        StudentProfile.objects.create(
            user=self.student_user,
            programme=StudentProfile.Programme.MSC,
            matric_number='MSC-PENDING-1',
            admission_year=2025,
            status=StudentProfile.Status.PENDING,
        )
        StudentProfile.objects.create(
            user=self.active_student_user,
            programme=StudentProfile.Programme.PHD,
            matric_number='PHD-ACTIVE-1',
            admission_year=2024,
            status=StudentProfile.Status.ACTIVE,
        )
        StudentProfile.objects.create(
            user=self.suspended_student_user,
            programme=StudentProfile.Programme.MSC,
            matric_number='MSC-SUSPENDED-1',
            admission_year=2023,
            status=StudentProfile.Status.SUSPENDED,
        )
        self.lecturer_user = CustomUser.objects.create_user(
            email='pending-lecturer@example.com',
            password='test-password',
            first_name='Danjuma',
            last_name='Pending',
            role=CustomUser.Role.LECTURER,
        )
        self.active_lecturer_user = CustomUser.objects.create_user(
            email='active-lecturer@example.com',
            password='test-password',
            first_name='Ene',
            last_name='Active',
            role=CustomUser.Role.LECTURER,
        )
        LecturerProfile.objects.create(
            user=self.lecturer_user,
            staff_id='STAFF-PENDING-1',
            status=LecturerProfile.Status.PENDING,
        )
        LecturerProfile.objects.create(
            user=self.active_lecturer_user,
            staff_id='STAFF-ACTIVE-1',
            specialization='Systems',
            is_supervisor=True,
            status=LecturerProfile.Status.ACTIVE,
        )
        self.students_url = reverse('accounts:all_students')
        self.pending_students_url = reverse('accounts:pending_students')
        self.lecturers_url = reverse('accounts:all_lecturers')
        self.pending_lecturers_url = reverse('accounts:pending_lecturers')

    def test_admin_all_lists_include_every_profile_status_without_private_data(self):
        self.client.force_authenticate(self.admin)

        students = self.client.get(self.students_url)
        self.assertEqual(students.status_code, status.HTTP_200_OK)
        self.assertEqual({item['status'] for item in students.data},
                         {'PENDING', 'ACTIVE', 'SUSPENDED'})
        self.assertEqual(len(students.data), 3)
        self.assertTrue({
            'email', 'first_name', 'last_name', 'full_name', 'matric_number',
            'programme', 'admission_year', 'status',
        }.issubset(students.data[0]))

        lecturers = self.client.get(self.lecturers_url)
        self.assertEqual(lecturers.status_code, status.HTTP_200_OK)
        self.assertEqual({item['status'] for item in lecturers.data}, {'PENDING', 'ACTIVE'})
        self.assertEqual(len(lecturers.data), 2)
        self.assertTrue({
            'email', 'first_name', 'last_name', 'full_name', 'staff_id',
            'specialization', 'is_supervisor', 'status',
        }.issubset(lecturers.data[0]))
        for item in [*students.data, *lecturers.data]:
            self.assertNotIn('password', item)
            self.assertNotIn('username', item)
            self.assertNotIn('is_superuser', item)
            self.assertNotIn('user_permissions', item)

    def test_pending_endpoints_remain_limited_to_pending_profiles(self):
        self.client.force_authenticate(self.admin)
        students = self.client.get(self.pending_students_url)
        lecturers = self.client.get(self.pending_lecturers_url)
        self.assertEqual([item['status'] for item in students.data], ['PENDING'])
        self.assertEqual([item['status'] for item in lecturers.data], ['PENDING'])

    def test_all_lists_support_status_filter_and_identifier_name_search(self):
        self.client.force_authenticate(self.admin)

        students = self.client.get(self.students_url, {'status': 'suspended'})
        self.assertEqual(students.status_code, status.HTTP_200_OK)
        self.assertEqual([item['matric_number'] for item in students.data], ['MSC-SUSPENDED-1'])
        self.assertEqual(
            self.client.get(self.students_url, {'search': 'active-student@'}).data[0]['full_name'],
            'Bala Active',
        )
        self.assertEqual(
            self.client.get(self.students_url, {'search': 'PHD-ACTIVE'}).data[0]['programme'],
            StudentProfile.Programme.PHD,
        )

        lecturers = self.client.get(self.lecturers_url, {'status': 'active'})
        self.assertEqual(lecturers.status_code, status.HTTP_200_OK)
        self.assertEqual([item['staff_id'] for item in lecturers.data], ['STAFF-ACTIVE-1'])
        self.assertEqual(
            self.client.get(self.lecturers_url, {'search': 'STAFF-PENDING'}).data[0]['full_name'],
            'Danjuma Pending',
        )
        self.assertEqual(
            self.client.get(self.lecturers_url, {'search': 'Ene Active'}).data[0]['staff_id'],
            'STAFF-ACTIVE-1',
        )

    def test_invalid_status_is_rejected_and_non_admins_cannot_list_all_profiles(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get(self.students_url, {'status': 'UNKNOWN'}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.get(self.lecturers_url, {'status': 'SUSPENDED'}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        for user in (self.student_user, self.active_lecturer_user):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.students_url).status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(self.client.get(self.lecturers_url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.students_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.lecturers_url).status_code, status.HTTP_401_UNAUTHORIZED)
