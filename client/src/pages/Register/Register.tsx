import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { authApi } from '../../api/auth';
import { ApiRequestError } from '../../api/client';
import Button from '../../components/Button/Button';
import Input from '../../components/Input/Input';
import '../Auth.css';

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    university: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!form.email) errs.email = 'Vui lòng nhập Email';
    if (!form.username) errs.username = 'Vui lòng nhập tên người dùng';
    else if (form.username.length < 3) errs.username = 'Ít nhất 3 ký tự';
    else if (!/^[a-zA-Z0-9_]+$/.test(form.username))
      errs.username = 'Chỉ bao gồm chữ cái, số, và dấu gạch dưới';
    if (!form.password) errs.password = 'Vui lòng nhập mật khẩu';
    else if (form.password.length < 8) errs.password = 'Ít nhất 8 ký tự';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError('');
    if (!validate()) return;

    setLoading(true);
    try {
      const response = await authApi.register(form);
      await login(response.access_token);
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setServerError(err.message);
      } else {
        setServerError('Đã xảy ra lỗi. Vui lòng thử lại.');
      }
    } finally {
      setLoading(false);
    }
  }

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <Link to="/" className="auth-logo">
            <span className="auth-logo-icon">U</span>
            UniConnect
          </Link>
          <h1 className="auth-title">Tạo tài khoản</h1>
          <p className="auth-subtitle">Tham gia cộng đồng trường học của bạn</p>
        </div>

        {serverError && <div className="auth-error">{serverError}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            placeholder="you@university.edu"
            value={form.email}
            onChange={(e) => update('email', e.target.value)}
            error={errors.email}
            autoFocus
          />
          <Input
            label="Tên người dùng (Username)"
            placeholder="johndoe"
            value={form.username}
            onChange={(e) => update('username', e.target.value)}
            error={errors.username}
          />
          <Input
            label="Mật khẩu"
            type="password"
            placeholder="Ít nhất 8 ký tự"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
            error={errors.password}
          />
          <Input
            label="Họ và tên"
            placeholder="John Doe (không bắt buộc)"
            value={form.full_name}
            onChange={(e) => update('full_name', e.target.value)}
          />
          <Input
            label="Trường đại học"
            placeholder="Trường đại học của bạn (không bắt buộc)"
            value={form.university}
            onChange={(e) => update('university', e.target.value)}
          />
          <Button type="submit" fullWidth loading={loading} size="lg">
            Tạo tài khoản
          </Button>
        </form>

        <div className="auth-footer">
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </div>
      </div>
    </div>
  );
}
