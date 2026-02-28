import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Upload, FolderSearch, Trash2, Sparkles, 
  ChevronDown, ChevronUp, BookOpen, Hash
} from 'lucide-react';
import { getArticles, uploadArticle, scanArticles, summarizeArticle, deleteArticle } from '../api';

export default function ArticlesPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [summaries, setSummaries] = useState({});
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      const res = await getArticles();
      setArticles(res.data);
    } catch (err) {
      console.error('Failed to load articles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files.length) return;

    setUploading(true);
    try {
      for (const file of files) {
        await uploadArticle(file);
      }
      await loadArticles();
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await scanArticles();
      alert(res.data.message);
      await loadArticles();
    } catch (err) {
      alert('Scan failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setScanning(false);
    }
  };

  const handleSummarize = async (id) => {
    try {
      const res = await summarizeArticle(id);
      setSummaries({ ...summaries, [id]: res.data.insights });
    } catch (err) {
      alert('Summarize failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this article?')) return;
    try {
      await deleteArticle(id);
      await loadArticles();
    } catch (err) {
      alert('Delete failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getFileIcon = (type) => {
    const colors = {
      pdf: 'text-red-400',
      txt: 'text-gray-400',
      md: 'text-blue-400',
      docx: 'text-blue-500',
      doc: 'text-blue-500',
    };
    return colors[type] || 'text-gray-400';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Articles</h2>
        <p className="text-gray-400 text-sm mt-1">Manage your source articles for tweet generation</p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.md,.docx,.doc"
          onChange={handleUpload}
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="btn-primary"
        >
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploading...' : 'Upload Articles'}
        </button>
        <button onClick={handleScan} disabled={scanning} className="btn-secondary">
          <FolderSearch className="w-4 h-4" />
          {scanning ? 'Scanning...' : 'Scan Directory'}
        </button>
        <span className="text-sm text-gray-500 ml-auto">{articles.length} articles</span>
      </div>

      {/* Info Box */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <p className="text-sm text-blue-300">
          <strong>Tip:</strong> Place article files (PDF, TXT, MD, DOCX) in the <code className="bg-blue-500/20 px-1.5 py-0.5 rounded">articles/</code> folder and click "Scan Directory" to import them automatically.
        </p>
      </div>

      {/* Articles List */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : articles.length > 0 ? (
        <div className="space-y-3">
          {articles.map((article) => (
            <div key={article.id} className="card hover:border-gray-700 transition-all">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center ${getFileIcon(article.file_type)}`}>
                  <FileText className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-white font-medium truncate">{article.title || article.filename}</h4>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span className="uppercase font-mono">{article.file_type}</span>
                    <span>{new Date(article.added_at).toLocaleDateString()}</span>
                    <span className="flex items-center gap-1">
                      <Hash className="w-3 h-3" /> {article.tweet_count} tweets
                    </span>
                    {article.is_processed ? (
                      <span className="badge-success">Processed</span>
                    ) : (
                      <span className="badge-warning">Pending</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSummarize(article.id)}
                    className="btn-secondary text-sm py-1.5 px-3"
                    title="Generate AI Summary"
                  >
                    <Sparkles className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setExpandedId(expandedId === article.id ? null : article.id)}
                    className="btn-secondary text-sm py-1.5 px-3"
                  >
                    {expandedId === article.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => handleDelete(article.id)}
                    className="btn-danger text-sm py-1.5 px-3"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Expanded content */}
              {expandedId === article.id && (
                <div className="mt-4 pt-4 border-t border-gray-800">
                  {summaries[article.id] && (
                    <div className="mb-4">
                      <h5 className="text-sm font-semibold text-blue-400 mb-2 flex items-center gap-2">
                        <Sparkles className="w-4 h-4" /> AI Summary
                      </h5>
                      <ul className="space-y-1.5">
                        {summaries[article.id].map((insight, i) => (
                          <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-blue-400 mt-1">•</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <p className="text-xs text-gray-500">
                    <BookOpen className="w-3 h-3 inline mr-1" />
                    {article.filename}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="card flex items-center justify-center h-48 text-gray-500">
          <div className="text-center">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No articles yet. Upload some or scan the articles directory!</p>
          </div>
        </div>
      )}
    </div>
  );
}
