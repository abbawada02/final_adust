import { useState, useEffect, useCallback } from "react";
import { getAllStudents, updateStudent } from "../../api/auth";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { StudentProfile, ProgrammeType } from "../../types";

interface EditForm {
  first_name: string;
  last_name: string;
  matric_number: string;
  programme: ProgrammeType;
  admission_year: number;
}

export default function AdminAllStudentsPage() {
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await getAllStudents(statusFilter || undefined);
      setStudents(data);
    } catch {
      setError("Could not load students.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { void load(); }, [load]);

  const startEdit = (s: StudentProfile) => {
    setEditingId(s.id);
    setEditForm({
      first_name: s.first_name,
      last_name: s.last_name,
      matric_number: s.matric_number,
      programme: s.programme,
      admission_year: s.admission_year,
    });
    setError("");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm(null);
  };

  const saveEdit = async (pk: number) => {
    if (!editForm) return;
    setSaving(true);
    setError("");
    try {
      const { data } = await updateStudent(pk, editForm);
      setStudents((prev) => prev.map((s) => (s.id === pk ? data : s)));
      cancelEdit();
    } catch {
      setError("Could not save changes. Check the fields and try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1">All Students</h4>
      <p className="text-muted">View and edit all registered students, regardless of status</p>
      <Alert message={error} />

      <div className="mb-3" style={{ maxWidth: 220 }}>
        <select
          className="form-select form-select-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="ACTIVE">Active</option>
          <option value="SUSPENDED">Suspended</option>
          <option value="GRADUATED">Graduated</option>
        </select>
      </div>

      {students.length === 0 ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body text-center text-muted py-5">No students found.</div>
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Matric No.</th>
                  <th>Programme</th>
                  <th>Admission Year</th>
                  <th>Status</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => {
                  const isEditing = editingId === s.id;
                  return (
                    <tr key={s.id}>
                      {isEditing && editForm ? (
                        <>
                          <td className="d-flex gap-1">
                            <input className="form-control form-control-sm" style={{ width: 100 }}
                              value={editForm.first_name}
                              onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })} />
                            <input className="form-control form-control-sm" style={{ width: 100 }}
                              value={editForm.last_name}
                              onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })} />
                          </td>
                          <td>{s.email}</td>
                          <td>
                            <input className="form-control form-control-sm"
                              value={editForm.matric_number}
                              onChange={(e) => setEditForm({ ...editForm, matric_number: e.target.value })} />
                          </td>
                          <td>
                            <select className="form-select form-select-sm"
                              value={editForm.programme}
                              onChange={(e) => setEditForm({ ...editForm, programme: e.target.value as ProgrammeType })}>
                              <option value="MSC">MSc</option>
                              <option value="PHD">PhD</option>
                            </select>
                          </td>
                          <td>
                            <input type="number" className="form-control form-control-sm" style={{ width: 90 }}
                              value={editForm.admission_year}
                              onChange={(e) => setEditForm({ ...editForm, admission_year: Number(e.target.value) })} />
                          </td>
                          <td>{s.status}</td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-primary me-2" disabled={saving}
                              onClick={() => void saveEdit(s.id)}>
                              {saving ? "…" : "Save"}
                            </button>
                            <button className="btn btn-sm btn-outline-secondary" disabled={saving} onClick={cancelEdit}>
                              Cancel
                            </button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{s.full_name}</td>
                          <td>{s.email}</td>
                          <td>{s.matric_number}</td>
                          <td>{s.programme}</td>
                          <td>{s.admission_year}</td>
                          <td>
                            <span className={`badge ${s.status === "ACTIVE" ? "bg-success" : "bg-secondary"}`}>
                              {s.status}
                            </span>
                          </td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-outline-secondary" onClick={() => startEdit(s)}>
                              Edit
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
