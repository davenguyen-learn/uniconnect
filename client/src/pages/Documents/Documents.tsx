import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { documentsApi, type DocumentResponse } from '../../api/documents';
import { useToast } from '../../components/Toast/ToastContext';
import './Documents.css';

export default function Documents() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const toast = useToast();

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 500);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const data = await documentsApi.listDocuments({ 
        limit: 50, 
        offset: 0,
        search: debouncedSearch || undefined,
        sort_by: sortBy
      });
      setDocuments(data.items);
    } catch (err) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, sortBy, toast]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="documents-page">
      <div className="documents-header">
        <div>
          <h1 className="gradient-text">Documents</h1>
          <p className="subtitle">Discover shared files and resources</p>
        </div>
        <Link to="/documents/upload" className="btn btn-primary">
          Upload Document
        </Link>
      </div>

      <div className="documents-controls glass">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search documents by title or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="sort-box">
          <label htmlFor="sort-select">Sort by:</label>
          <select 
            id="sort-select" 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="newest">Newest first</option>
            <option value="most_interactions">Most interactions</option>
            <option value="oldest">Oldest first</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Loading documents...</div>
      ) : documents.length === 0 ? (
        <div className="empty-state glass">
          <div className="empty-icon">📁</div>
          <h3>No documents yet</h3>
          <p>Be the first to share a document with the community.</p>
          <Link to="/documents/upload" className="btn btn-primary">
            Upload Document
          </Link>
        </div>
      ) : (
        <div className="documents-grid">
          {documents.map((doc) => (
            <Link to={`/documents/${doc.id}`} key={doc.id} className="document-card glass">
              <div className="document-icon">
                {doc.file_type.includes('pdf') ? '📄' :
                 doc.file_type.includes('image') ? '🖼️' :
                 doc.file_type.includes('word') ? '📝' : '📁'}
              </div>
              <div className="document-content">
                <h3 className="document-title">{doc.title}</h3>
                {doc.description && <p className="document-desc">{doc.description}</p>}
                <div className="document-meta">
                  <span className="doc-author">By {doc.author?.full_name || doc.author?.username}</span>
                  <span className="doc-size">{formatFileSize(doc.file_size)}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
