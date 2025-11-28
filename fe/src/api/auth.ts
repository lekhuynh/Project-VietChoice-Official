import { API_BASE_URL } from '../config';

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export async function register(input: RegisterInput): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: input.name, email: input.email, password: input.password }),
    credentials: 'include',
  });
  if (!resp.ok) {
    const msg = await safeMessage(resp);
    throw new Error(msg || 'Đăng ký thất bại.');
  }
}

export async function login(input: LoginInput): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: input.email, password: input.password }),
    credentials: 'include',
  });
  if (!resp.ok) {
    const msg = await safeMessage(resp);
    throw new Error(msg || 'Đăng nhập thất bại.');
  }
}

export async function logout(): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!resp.ok) {
    const msg = await safeMessage(resp);
    throw new Error(msg || 'Đăng xuất thất bại.');
  }
}

async function safeMessage(resp: Response): Promise<string | undefined> {
  try {
    const data = await resp.json();
    return (data && (data.detail || data.message)) as string | undefined;
  } catch {
    return undefined;
  }
}

