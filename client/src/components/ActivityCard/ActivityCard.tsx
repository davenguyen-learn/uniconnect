import { type ActivityResponse } from '../../api/activities';
import './ActivityCard.css';

interface ActivityCardProps {
  activity: ActivityResponse;
  onClick?: () => void;
}

export default function ActivityCard({ activity, onClick }: ActivityCardProps) {
  return (
    <div className="activity-card-ui" onClick={onClick}>
      <div className="activity-card-header">
        <span className="activity-card-category">{activity.category || 'General'}</span>
        {typeof activity.distance_meters === 'number' && (
          <span className="activity-card-distance">
            {(activity.distance_meters / 1000).toFixed(1)} km
          </span>
        )}
      </div>
      <h4 className="activity-card-title">{activity.title}</h4>
      <div className="activity-card-footer">
        <span>{new Date(activity.start_time).toLocaleDateString()}</span>
        <span>{activity.current_participants}/{activity.max_participants} joined</span>
      </div>
    </div>
  );
}
