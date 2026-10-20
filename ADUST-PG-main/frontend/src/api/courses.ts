import api from "./client";
import type {
  AcademicSession, Course, CourseAllocation, TimetableEntry,
  Enrollment, CourseMaterial, AvailableAllocation,
} from "../types";

export const getCurrentSession = () => api.get<AcademicSession>("/courses/session/current/");
export const getCourses = (params?: Record<string, string>) =>
  api.get<Course[]>("/courses/list/", { params });
export const getTimetable = () => api.get<TimetableEntry[]>("/courses/timetable/");
export const enroll = (allocation: number) =>
  api.post<Enrollment>("/courses/enroll/", { allocation });
export const getMyEnrollments = () => api.get<Enrollment[]>("/courses/enrollments/");
export const getAvailableAllocations = () =>
  api.get<AvailableAllocation[]>("/courses/available/");
export const getMyAllocations = () => api.get<CourseAllocation[]>("/courses/allocations/");
export const getMaterials = (allocationPk: number) =>
  api.get<CourseMaterial[]>(`/courses/materials/${allocationPk}/`);
export const getRecentMaterials = (limit = 5) =>
  api.get<CourseMaterial[]>("/courses/materials/recent/", { params: { limit } });
export const uploadMaterial = (allocationPk: number, formData: FormData) =>
  api.post<CourseMaterial>(`/courses/materials/${allocationPk}/upload/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// Admin
export const adminAllocateCourse = (data: Record<string, unknown>) =>
  api.post<CourseAllocation>("/courses/admin/allocate/", data);
export const adminGetAllocations = () =>
  api.get<CourseAllocation[]>("/courses/admin/allocations/");
export const adminCreateTimetable = (data: Record<string, unknown>) =>
  api.post<TimetableEntry>("/courses/admin/timetable/", data);
export const adminGetTimetable = () =>
  api.get<TimetableEntry[]>("/courses/admin/timetable/");
export const adminUpdateTimetable = (pk: number, data: Record<string, unknown>) =>
  api.patch<TimetableEntry>(`/courses/admin/timetable/${pk}/`, data);
export const adminDeleteTimetable = (pk: number) =>
  api.delete(`/courses/admin/timetable/${pk}/`);
export const adminPendingEnrollments = () =>
  api.get<Enrollment[]>("/courses/admin/enrollments/pending/");
export const adminApproveEnrollment = (pk: number, action: "approve" | "reject") =>
  api.post(`/courses/admin/enrollments/${pk}/approve/`, { action });
