import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { activitiesApi, type ActivityCreate } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import LocationPicker from '../../components/Map/LocationPicker';
import './CreateActivity.css';

export default function CreateActivity() {
  const navigate = useNavigate();
  const toast = useToast();
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    location_name: '',
    start_time: '',
    end_time: '',
    max_participants: 10,
    privacy: 'public' as 'public' | 'private',
    require_approval: true,
  });
  
  const [location, setLocation] = useState<[number, number] | null>(null);
  
  // Custom Form Builder state
  const [customFormFields, setCustomFormFields] = useState<Array<{ id: string, label: string, field_type: string, is_required: boolean }>>([]);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const { checked } = e.target as HTMLInputElement;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!location) {
      toast.error('Please select a location on the map');
      return;
    }

    const start = new Date(formData.start_time);
    const end = new Date(formData.end_time);

    if (end <= start) {
      toast.error('End time must be after start time');
      return;
    }

    try {
      setLoading(true);
      const data: ActivityCreate = {
        title: formData.title,
        description: formData.description,
        category: formData.category || undefined,
        location_name: formData.location_name || undefined,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        max_participants: Number(formData.max_participants),
        privacy: formData.privacy,
        require_approval: formData.require_approval,
        latitude: location[0],
        longitude: location[1],
      };

      if (customFormFields.length > 0) {
        data.custom_form = {
          title: "Join Application Form",
          description: "Please fill out this form to join.",
          fields: customFormFields.map((f, idx) => ({
            label: f.label,
            field_type: f.field_type as any,
            is_required: f.is_required,
            order: idx
          }))
        };
      }

      const newActivity = await activitiesApi.create(data);
      toast.success('Activity created successfully!');
      navigate(`/activities/${newActivity.id}`);
    } catch (error) {
      toast.error('Failed to create activity');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-activity-page">
      <div className="create-activity-container glass">
        <h1 className="create-activity-title">Host an Activity</h1>
        <p className="create-activity-subtitle">Create a new event and invite others to join.</p>

        <form onSubmit={handleSubmit} className="create-activity-form">
          <div className="form-group">
            <label htmlFor="title">Title <span className="required">*</span></label>
            <input
              type="text"
              id="title"
              name="title"
              className="form-input"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="e.g., Weekend Hackathon or Basketball Pickup"
              maxLength={100}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description <span className="required">*</span></label>
            <textarea
              id="description"
              name="description"
              className="form-input"
              value={formData.description}
              onChange={handleChange}
              required
              placeholder="Tell people what this is about..."
              rows={4}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">Category</label>
              <input
                list="categories"
                id="category"
                name="category"
                className="form-input"
                value={formData.category}
                onChange={handleChange}
                placeholder="Select or type a category"
                maxLength={50}
              />
              <datalist id="categories">
                <option value="Study" />
                <option value="Sports" />
                <option value="Social" />
                <option value="Gaming" />
                <option value="Music" />
              </datalist>
            </div>

            <div className="form-group">
              <label htmlFor="max_participants">Max Participants <span className="required">*</span></label>
              <input
                type="number"
                id="max_participants"
                name="max_participants"
                className="form-input"
                value={formData.max_participants}
                onChange={handleChange}
                required
                min={2}
                max={1000}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start_time">Start Time <span className="required">*</span></label>
              <input
                type="datetime-local"
                id="start_time"
                name="start_time"
                className="form-input"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="end_time">End Time <span className="required">*</span></label>
              <input
                type="datetime-local"
                id="end_time"
                name="end_time"
                className="form-input"
                value={formData.end_time}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="privacy">Privacy</label>
            <select
              id="privacy"
              name="privacy"
              className="form-input"
              value={formData.privacy}
              onChange={handleChange}
            >
              <option value="public">Public (Visible to everyone)</option>
              <option value="private">Private (Invite only or hidden)</option>
            </select>
          </div>

          <div className="form-group checkbox-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="checkbox"
              id="require_approval"
              name="require_approval"
              checked={formData.require_approval}
              onChange={handleChange}
            />
            <label htmlFor="require_approval" style={{ margin: 0 }}>Require approval to join (Request to Join)</label>
          </div>

          <div className="form-group">
            <label htmlFor="location_name">Location Name</label>
            <input
              type="text"
              id="location_name"
              name="location_name"
              className="form-input"
              value={formData.location_name}
              onChange={handleChange}
              placeholder="e.g., KTX Khu A, Sân bóng, etc."
              maxLength={100}
            />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ margin: 0 }}>Custom Join Form</label>
              <Button type="button" size="sm" variant="secondary" onClick={() => setShowFormBuilder(!showFormBuilder)}>
                {showFormBuilder ? 'Hide Builder' : 'Add Form Fields'}
              </Button>
            </div>
            {showFormBuilder && (
              <div className="form-builder" style={{ padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', marginTop: '12px' }}>
                <p style={{ fontSize: '0.9rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>
                  Require users to fill out specific fields when joining.
                </p>
                {customFormFields.map((field, index) => (
                  <div key={field.id} style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: '0.8rem' }}>Field Label</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        value={field.label} 
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].label = e.target.value;
                          setCustomFormFields(newFields);
                        }} 
                      />
                    </div>
                    <div style={{ width: '120px' }}>
                      <label style={{ fontSize: '0.8rem' }}>Type</label>
                      <select 
                        className="form-input" 
                        value={field.field_type}
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].field_type = e.target.value;
                          setCustomFormFields(newFields);
                        }}
                      >
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="boolean">Checkbox</option>
                      </select>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', height: '40px', paddingBottom: '8px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', cursor: 'pointer' }}>
                        <input 
                          type="checkbox" 
                          checked={field.is_required}
                          onChange={(e) => {
                            const newFields = [...customFormFields];
                            newFields[index].is_required = e.target.checked;
                            setCustomFormFields(newFields);
                          }}
                        /> Req
                      </label>
                    </div>
                    <Button 
                      type="button" 
                      variant="secondary" 
                      onClick={() => setCustomFormFields(customFormFields.filter((_, i) => i !== index))}
                      style={{ height: '40px' }}
                    >
                      X
                    </Button>
                  </div>
                ))}
                <Button 
                  type="button" 
                  size="sm" 
                  onClick={() => setCustomFormFields([...customFormFields, { id: Math.random().toString(), label: '', field_type: 'text', is_required: true }])}
                >
                  + Add Field
                </Button>
              </div>
            )}
          </div>

          <div className="form-group map-group">
            <label>Map Location <span className="required">*</span></label>
            <LocationPicker 
              position={location} 
              onChange={(lat, lng) => setLocation([lat, lng])} 
            />
            {!location && <span className="error-text mt-1 text-sm block">Please click on the map to set a location.</span>}
          </div>

          <div className="form-actions">
            <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !location}>
              {loading ? 'Creating...' : 'Create Activity'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
