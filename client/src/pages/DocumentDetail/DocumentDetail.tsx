import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { documentsApi, type DocumentResponse } from '../../api/documents';
import { interactionsApi, type CommentResponse } from '../../api/interactions';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import LikeButton from '../../components/LikeButton/LikeButton';
import CommentSection from '../../components/CommentSection/CommentSection';
import { ReportModal } from '../../components/ReportModal/ReportModal';
import './DocumentDetail.css';

const COMMENT_LIMIT = 20;

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // Interactions state
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [commentTotal, setCommentTotal] = useState(0);
  const [commentOffset, setCommentOffset] = useState(0);
  const [commentHasMore, setCommentHasMore] = useState(false);

  const fetchDocument = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const doc = await documentsApi.getDocument(id);
      setDocument(doc);
      
      // Load interactions
      const [likeStatus, commentsData] = await Promise.all([
        interactionsApi.getLikeStatus('documents', id),
        interactionsApi.listComments('documents', id, { limit: COMMENT_LIMIT, offset: 0 }),
      ]);
      setLiked(likeStatus.liked);
      setLikeCount(likeStatus.total_likes);
      
      setComments(commentsData.items);
      setCommentTotal(commentsData.total);
      setCommentHasMore(commentsData.has_more);
      setCommentOffset(0);
    } catch (err: any) {
      toast.error('Không thể tải tài liệu');
      navigate('/documents');
    } finally {
      setLoading(false);
    }
  }, [id, navigate, toast]);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  const loadMoreComments = async () => {
    if (!id) return;
    const newOffset = commentOffset + COMMENT_LIMIT;
    try {
      const data = await interactionsApi.listComments('documents', id, { limit: COMMENT_LIMIT, offset: newOffset });
      setComments(prev => [...prev, ...data.items]);
      setCommentTotal(data.total);
      setCommentHasMore(data.has_more);
      setCommentOffset(newOffset);
    } catch {
      toast.error('Không thể tải các bình luận cũ hơn');
    }
  };

  const refreshComments = async () => {
    if (!id) return;
    try {
      const data = await interactionsApi.listComments('documents', id, { limit: COMMENT_LIMIT, offset: 0 });
      setComments(data.items);
      setCommentTotal(data.total);
      setCommentHasMore(data.has_more);
      setCommentOffset(0);
    } catch {
      // silent
    }
  };

  const handleDownload = async () => {
    if (!id || downloading) return;
    setDownloading(true);
    try {
      const { url } = await documentsApi.getDownloadUrl(id);
      window.open(url, '_blank');
    } catch {
      toast.error('Không thể lấy link tải xuống');
    } finally {
      setDownloading(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !window.confirm('Bạn có chắc chắn muốn xóa tài liệu này không?')) return;
    try {
      await documentsApi.deleteDocument(id);
      toast.success('Đã xóa tài liệu');
      navigate('/documents');
    } catch {
      toast.error('Không thể xóa tài liệu');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) return <div className="loading-state">Đang tải tài liệu...</div>;
  if (!document) return null;

  const isAuthor = user?.id === document.author_id;

  return (
    <div className="document-detail-page">
      <div className="glass document-detail-card">
        <div className="document-header">
          <div className="document-title-row">
            <h1 className="brutalist-highlight">{document.title}</h1>
            {isAuthor && (
              <button onClick={handleDelete} className="btn btn-danger btn-sm">Xóa</button>
            )}
          </div>
          
          <div className="document-meta">
            <span className="doc-author">Bởi <Link to={`/profile/${document.author_id}`} style={{color: 'inherit', textDecoration: 'underline'}}>@{document.author?.username}</Link></span>
            <span className="doc-date">{new Date(document.created_at).toLocaleDateString('vi-VN')}</span>
            <span className="doc-size">{formatFileSize(document.file_size)}</span>
            <span className="doc-type">{document.file_name.split('.').pop()?.toUpperCase()}</span>
          </div>
        </div>

        {document.description && (
          <div className="document-description">
            {document.description}
          </div>
        )}

        <div className="document-actions">
          <LikeButton 
            targetType="documents" 
            targetId={id!} 
            initialLiked={liked} 
            initialCount={likeCount} 
          />
          {!isAuthor && (
            <button 
              className="btn btn-secondary" 
              onClick={() => setIsReportModalOpen(true)}
            >
              Báo cáo
            </button>
          )}
          <button 
            className="btn btn-primary" 
            onClick={handleDownload}
            disabled={downloading}
          >
            {downloading ? 'Đang chuẩn bị...' : 'Tải tài liệu xuống'}
          </button>
        </div>
      </div>

      <ReportModal 
        isOpen={isReportModalOpen} 
        onClose={() => setIsReportModalOpen(false)} 
        targetType="document" 
        targetId={id!} 
      />

      <div className="glass document-comments">
        <CommentSection
          targetType="documents"
          targetId={id!}
          comments={comments}
          total={commentTotal}
          hasMore={commentHasMore}
          onRefresh={refreshComments}
          onLoadMore={loadMoreComments}
        />
      </div>
    </div>
  );
}
