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
      toast.success('Tải tài liệu lên thành công');
      navigate(`/documents/${doc.id}`);
    } catch (err: any) {
      toast.error(err?.details || err?.message || 'Không thể tải tài liệu lên');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="glass upload-card">
        <h1 className="brutalist-highlight">Tải tài liệu lên</h1>
        <p className="subtitle">Chia sẻ tệp với cộng đồng</p>

        <form onSubmit={handleSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="title">Tiêu đề *</label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ví dụ: Ghi chú thi giữa kỳ CS101"
              required
              maxLength={200}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Mô tả (Không bắt buộc)</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Thêm một số ngữ cảnh về tài liệu này..."
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="groupId">Quyền riêng tư / Nhóm</label>
            <select
              id="groupId"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="form-select"
            >
              <option value="">Công khai (Bất kỳ ai cũng có thể xem)</option>
              {myGroups.map(g => (
                <option key={g.id} value={g.id}>Nhóm: {g.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="file">Tệp *</label>
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
            <small className="help-text">Kích thước tối đa: 10MB. Cho phép: PDF, Word, Excel, PPT, Hình ảnh.</small>
          </div>

          <div className="form-actions">
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => navigate(-1)}
              disabled={uploading}
            >
              Hủy
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={uploading || !title.trim() || !file}
            >
              {uploading ? 'Đang tải lên...' : 'Tải lên'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
