import { Link } from 'react-router-dom';
import Button from '../../components/Button/Button';

export default function NotFound() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        gap: 'var(--space-6)',
        padding: 'var(--space-6)',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '5rem', opacity: 0.2 }}>404</div>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-semibold)' }}>
        Page not found
      </h1>
      <p style={{ color: 'var(--color-text-secondary)', maxWidth: '400px' }}>
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/">
        <Button variant="secondary">Back to home</Button>
      </Link>
    </div>
  );
}
