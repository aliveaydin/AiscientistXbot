import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Upload, FolderSearch, Trash2, Sparkles, 
  ChevronDown, ChevronUp, BookOpen, Hash, RefreshCw,
  ExternalLink, Star, Globe
} from 'lucide-react';
import { getArticles, getArticleCount, uploadArticle, scanArticles, summarizeArticle, deleteArticle, fetchArxiv } from '../api';

export default function ArticlesPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [fetchingArxiv, setFetchingArxiv] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [summaries, setSummaries] = useState({});
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const PAGE_SIZE = 20;
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadArticles();
  }, [page]);

  const loadArticles = async () => {
    try {
      const [res, countRes] = await Promise.all([
        getArticles(PAGE_SIZE, page * PAGE_SIZE),
        getArticleCount(),
      ]);
      setArticles(res.data);
      setTotalCount(countRes.data.count);
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

  const handleFetchArxiv = async () => {
    setFetchingArxiv(true);
    try {
      const res = await fetchArxiv();
      const papers = res.data.papers || [];
      if (papers.length > 0) {
        alert(`Imported ${papers.length} papers from ArXiv:\n${papers.map(p => `${p.title.substring(0, 60)}... (score: ${p.score})`).join('\n')}`);
      } else {
        alert('No new papers found on ArXiv (all recent ones already imported).');
      }
      await loadArticles();
    } catch (err) {
      alert('ArXiv fetch failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setFetchingArxiv(false);
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
        <button onClick={handleFetchArxiv} disabled={fetchingArxiv} className="btn-secondary">
          {fetchingArxiv ? (
            <><RefreshCw className="w-4 h-4 animate-spin" /> Fetching ArXiv...</>
          ) : (
            <><Globe className="w-4 h-4" /> Fetch ArXiv Papers</>
          )}
        </button>
        <span className="text-sm text-gray-500 ml-auto">
          {totalCount} articles ({articles.filter(a => a.source === 'arxiv').length} from ArXiv on this page)
        </span>
      </div>

      {/* Info Box */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 space-y-2">
        <p className="text-sm text-blue-300">
          <strong>Manual:</strong> Upload article files (PDF, TXT, MD, DOCX) or place them in the <code className="bg-blue-500/20 px-1.5 py-0.5 rounded">articles/</code> folder and click "Scan Directory".
        </p>
        <p className="text-sm text-orange-300">
          <strong>ArXiv Auto-Fetch:</strong> Click "Fetch ArXiv Papers" to grab the latest AI/ML papers, or let the bot fetch them automatically every 12 hours. Papers are scored by AI for relevance; only the best ones are imported.
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
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 flex-wrap">
                    {article.source === 'arxiv' ? (
                      <span className="bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded font-medium">ArXiv</span>
                    ) : (
                      <span className="bg-gray-700/50 text-gray-400 px-1.5 py-0.5 rounded">Manual</span>
                    )}
                    <span className="uppercase font-mono">{article.file_type}</span>
                    <span>{new Date(article.added_at).toLocaleDateString()}</span>
                    <span className="flex items-center gap-1">
                      <Hash className="w-3 h-3" /> {article.tweet_count} tweets
                    </span>
                    {article.relevance_score && (
                      <span className="flex items-center gap-1 text-yellow-400">
                        <Star className="w-3 h-3" /> {article.relevance_score.toFixed(1)}
                      </span>
                    )}
                    {article.arxiv_url && (
                      <a href={article.arxiv_url} target="_blank" rel="noopener noreferrer"
                         className="flex items-center gap-1 text-blue-400 hover:text-blue-300">
                        <ExternalLink className="w-3 h-3" /> ArXiv
                      </a>
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

      {totalCount > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="btn-secondary text-sm py-1.5 px-4 disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-sm text-gray-400">
            Page {page + 1} of {Math.ceil(totalCount / PAGE_SIZE)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * PAGE_SIZE >= totalCount}
            className="btn-secondary text-sm py-1.5 px-4 disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
