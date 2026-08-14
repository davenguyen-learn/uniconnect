import { Link } from 'react-router-dom';
import Button from '../../components/Button/Button';
import './NotFound.css';

export default function NotFound() {
  return (
    <div className="not-found-page">
      <div className="not-found-code">404</div>
      <h1 className="not-found-title">
        Page not found
      </h1>
      <p className="not-found-message">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/">
        <Button variant="secondary">Back to home</Button>
      </Link>
    </div>
  );
}
