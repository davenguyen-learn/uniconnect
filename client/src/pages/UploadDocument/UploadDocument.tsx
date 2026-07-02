import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { documentsApi } from '../../api/documents';
import { groupsApi, type GroupResponse } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import './UploadDocument.css';

export default function UploadDocument() {
  const navigate = useNavigate();
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const initialGroupId = searchParams.get('groupId') || '';
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [groupId, setGroupId] = useState(initialGroupId);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [myGroups, setMyGroups] = useState<GroupResponse[]>([]);

  useEffect(() => {
    async function fetchGroups() {
      try {
        const groups = await groupsApi.getMyGroups();
        setMyGroups(groups);
      } catch (err) {
        console.error("Failed to fetch groups", err);
      }
    }
    fetchGroups();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('title', title.trim());
      if (description.trim()) {
        formData.append('description', description.trim());
      }
      if (groupId) {
        formData.append('group_id', groupId);
      }
      formData.append('file', file);
      
      const doc = await documentsApi.uploadDocument(formData);
      toast.success('Document uploaded successfully');
      navigate(`/documents/${doc.id}`);
    } catch (err: any) {
      toast.error(err?.details || err?.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="glass upload-card">
        <h1 className="gradient-text">Upload Document</h1>
        <p className="subtitle">Share files with the community</p>

        <form onSubmit={handleSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="title">Title *</label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="E.g., CS101 Midterm Notes"
              required
              maxLength={200}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description (Optional)</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add some context about this document..."
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="groupId">Visibility / Group</label>
            <select
              id="groupId"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="form-select"
            >
              <option value="">Public (Anyone can view)</option>
              {myGroups.map(g => (
                <option key={g.id} value={g.id}>Group: {g.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="file">File *</label>
            <input
              id="file"
              type="file"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setFile(e.target.files[0]);
                }
              }}
              required
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.ppt,.pptx,.xls,.xlsx"
            />
            <small className="help-text">Max size: 10MB. Allowed: PDF, Word, Excel, PPT, Images.</small>
          </div>

          <div className="form-actions">
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => navigate(-1)}
              disabled={uploading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={uploading || !title.trim() || !file}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
