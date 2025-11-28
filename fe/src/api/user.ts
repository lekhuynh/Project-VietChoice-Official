// frontend/src/api/user.ts
import { API_BASE_URL } from '../config';

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  role?: 'user' | 'admin' | 'manager' | string;
  created_at?: string;
  last_login?: string;
}

export interface UserUpdateData {
  name: string;
}

// Hàm lấy thông tin profile (Module 1)
export const fetchUserProfile = async (): Promise<UserProfile> => {
  // Backend: GET /users_profile/me
  const response = await fetch(`${API_BASE_URL}/users_profile/me`, { credentials: 'include' });
  if (!response.ok) {
    if (response.status === 401) throw new Error('Unauthenticated');
    throw new Error('Lỗi khi tải thông tin hồ sơ.');
  }
  const data = await response.json();
  const profile: UserProfile = {
    id: data.User_ID ?? data.id,
    email: data.User_Email ?? data.email,
    name: data.User_Name ?? data.name,
    role: data.Role ?? data.role,
    created_at: data.Created_At ?? data.created_at,
  };
  return profile;
};

// Hàm cập nhật thông tin profile (Module 1)
export const updateUserProfile = async (updateData: UserUpdateData): Promise<UserProfile> => {
  // Backend: PUT /users_profile/update
  const response = await fetch(`${API_BASE_URL}/users_profile/update`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_name: updateData.name }),
    credentials: 'include'
  });
  
  if (!response.ok) {
    if (response.status === 401) throw new Error('Unauthenticated');
    throw new Error('Cập nhật hồ sơ thất bại.');
  }
  const data = await response.json();
  const profile: UserProfile = {
    id: data.User_ID ?? data.id,
    email: data.User_Email ?? data.email,
    name: data.User_Name ?? data.name,
    role: data.Role ?? data.role,
    created_at: data.Created_At ?? data.created_at,
  };
  return profile;
};

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export const changePassword = async (payload: ChangePasswordPayload): Promise<void> => {
  const res = await fetch(`${API_BASE_URL}/users_profile/change-password`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    if (res.status === 401) throw new Error('Unauthenticated');
    const msg = await res.text();
    throw new Error(msg || 'Đổi mật khẩu thất bại');
  }
};
