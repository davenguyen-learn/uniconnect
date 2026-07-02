import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { groupsApi } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import Input from '../../components/Input/Input';
import { Textarea } from '../../components/Input/Input';

export default function CreateGroup() {
  const navigate = useNavigate();
  const toast = useToast();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [allowActivities, setAllowActivities] = useState(true);
  const [allowDocuments, setAllowDocuments] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      const response = await groupsApi.createGroup({ 
        name, 
        description,
        allow_member_activities: allowActivities,
        allow_member_documents: allowDocuments
      });
      toast.success('Group created successfully!');
      navigate(`/groups/${response.id}`);
    } catch (err) {
      toast.error('Failed to create group');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: 'var(--space-8)', maxWidth: '600px' }}>
      <div className="glass" style={{ padding: 'var(--space-8)' }}>
        <h1 style={{ margin: '0 0 var(--space-6) 0' }}>Create Group</h1>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <Input 
            label="Group Name" 
            placeholder="e.g., Computer Science Club" 
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={100}
          />
          
          <Textarea 
            label="Description" 
            placeholder="What is this group about?" 
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={allowActivities}
                onChange={(e) => setAllowActivities(e.target.checked)}
              />
              <span>Allow members to create activities</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={allowDocuments}
                onChange={(e) => setAllowDocuments(e.target.checked)}
              />
              <span>Allow members to upload documents</span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '16px', marginTop: '16px', justifyContent: 'flex-end' }}>
            <Button variant="ghost" type="button" onClick={() => navigate('/groups')}>
              Cancel
            </Button>
            <Button type="submit" loading={loading} disabled={!name.trim()}>
              Create Group
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
