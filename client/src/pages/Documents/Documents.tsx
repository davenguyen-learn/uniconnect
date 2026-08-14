import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { documentsApi, type DocumentResponse } from '../../api/documents';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import CollectionLayout from '../../components/Layout/CollectionLayout';
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
    } catch {
      toast.error('Không thể tải tài liệu');
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

  const sortOptions = [
    { label: 'Mới nhất', value: 'newest' },
    { label: 'Nhiều tương tác nhất', value: 'most_interactions' },
    { label: 'Cũ nhất', value: 'oldest' },
  ];

  return (
    <CollectionLayout
      title="Tài liệu"
      action={
        <Link to="/documents/upload">
          <Button>Tải tài liệu lên</Button>
        </Link>
      }
      searchPlaceholder="Tìm kiếm tài liệu theo tiêu đề hoặc mô tả..."
      searchValue={search}
      onSearchChange={setSearch}
      sortOptions={sortOptions}
      sortValue={sortBy}
      onSortChange={setSortBy}
      loading={loading}
      loadingMessage="Đang tải tài liệu..."
      isEmpty={documents.length === 0}
      emptyTitle="Chưa có tài liệu nào"
      emptyMessage="Hãy là người đầu tiên chia sẻ tài liệu với cộng đồng."
      emptyAction={
        <Link to="/documents/upload">
          <Button>Tải tài liệu lên</Button>
        </Link>
      }
    >
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
              <span className="doc-author">Bởi {doc.author?.full_name || doc.author?.username}</span>
              <span className="doc-size">{formatFileSize(doc.file_size)}</span>
            </div>
          </div>
        </Link>
      ))}
    </CollectionLayout>
  );
}
