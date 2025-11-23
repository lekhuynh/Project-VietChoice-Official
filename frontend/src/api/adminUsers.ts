// API helpers for admin user management
import { API_BASE_URL } from '../config';

export interface AdminUser {
  User_ID: number;
  User_Email: string;
  User_Name: string;
  Role?: string;
  Created_At?: string;
}

export async function fetchAdminUsers(): Promise<AdminUser[]> {
  const res = await fetch(`${API_BASE_URL}/admin/admin/list`, {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Fetch users failed: ${res.status}`);
  }
  return res.json();
}

export async function deleteAdminUser(userId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/admin/admin/${userId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Delete user failed: ${res.status}`);
  }
}
