import { useState, useEffect } from 'react';
import { getAdminPapers } from '../api';
import { FileText, Search, Download, Eye, X } from 'lucide-react';

export default function PapersPage() {
  const [papers, setPapers] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState(null);
  const limit = 30;

  const fetchPapers = async () => {
    setLoading(true);
    try {
      const { data } = await getAdminPapers(search, status, limit, offset);
      setPapers(data.papers);
      setTotal(data.total);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchPapers(); }, [offset]);

  const handleFilter = (e) => {
    e?.preventDefault?.();
    setOffset(0);
    fetchPapers();
  };

  const totalPages = Math.ceil(total / limit);
  const page = Math.floor(offset / limit) + 1;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-amber-400" />
          <h1 className="text-xl font-bold text-white">Research Papers</h1>
          <span className="text-sm text-gray-500">{total} total</span>
        </div>
      </div>

      <form onSubmit={handleFilter} className="flex gap-2 flex-wrap">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search papers..."
            className="bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-amber-500 w-64"
          />
        </div>
        <select value={status} onChange={e => setStatus(e.target.value)} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none">
          <option value="">All Status</option>
          <option value="draft">Draft</option>
          <option value="final">Final</option>
          <option value="under_review">Under Review</option>
          <option value="revision">Revision</option>
        </select>
        <button type="submit" className="px-4 py-2 bg-amber-600 text-white text-sm rounded-lg hover:bg-amber-500">Filter</button>
      </form>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-left text-xs">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Project</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-center">Ver</th>
              <th className="px-4 py-3">Published</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : papers.length === 0 ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-500">No papers found</td></tr>
            ) : papers.map(p => (
              <tr key={p.id} className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors">
                <td className="px-4 py-3 text-gray-500 font-mono text-xs">#{p.id}</td>
                <td className="px-4 py-3">
                  <p className="text-white font-medium leading-tight">{p.title}</p>
                  {p.abstract && <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{p.abstract}</p>}
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{p.project_title || `Project #${p.project_id}`}</td>
                <td className="px-4 py-3">
                  {p.owner ? (
                    <span className="text-blue-400 text-xs">@{p.owner}</span>
                  ) : (
                    <span className="text-gray-600 text-xs">admin</span>
                  )}
                </td>
                <td className="px-4 py-3"><StatusBadge status={p.status} /></td>
                <td className="px-4 py-3 text-center text-gray-400">v{p.version}</td>
                <td className="px-4 py-3">
                  {p.published ? (
                    <span className="px-2 py-0.5 bg-green-900/30 text-green-400 rounded text-xs">Yes</span>
                  ) : (
                    <span className="text-gray-600 text-xs">No</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button onClick={() => setPreview(p)} className="text-gray-500 hover:text-white" title="Preview">
                      <Eye className="w-4 h-4" />
                    </button>
                    <a href={`/api/lab/projects/${p.project_id}/paper/download`} target="_blank" rel="noreferrer" className="text-gray-500 hover:text-amber-400" title="Download PDF">
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))} className="px-3 py-1.5 bg-gray-800 text-gray-400 rounded hover:text-white disabled:opacity-30">Prev</button>
            <button disabled={page >= totalPages} onClick={() => setOffset(offset + limit)} className="px-3 py-1.5 bg-gray-800 text-gray-400 rounded hover:text-white disabled:opacity-30">Next</button>
          </div>
        </div>
      )}

      {preview && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={() => setPreview(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-white">{preview.title}</h2>
                <p className="text-sm text-gray-500 mt-1">Project: {preview.project_title || `#${preview.project_id}`} · {preview.owner ? `@${preview.owner}` : 'admin'}</p>
              </div>
              <button onClick={() => setPreview(null)} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex gap-3 mb-4">
              <StatusBadge status={preview.status} />
              <span className="text-xs text-gray-500">v{preview.version}</span>
              {preview.published && <span className="px-2 py-0.5 bg-green-900/30 text-green-400 rounded text-xs">Published</span>}
            </div>
            {preview.abstract && (
              <div className="bg-gray-800/50 rounded-lg p-4 text-sm text-gray-300 leading-relaxed">
                <p className="text-xs text-gray-500 mb-1 font-medium">Abstract</p>
                {preview.abstract}
              </div>
            )}
            <div className="mt-4 flex gap-2">
              <a href={`/api/lab/projects/${preview.project_id}/paper/download`} target="_blank" rel="noreferrer"
                className="px-4 py-2 bg-amber-600 text-white text-sm rounded-lg hover:bg-amber-500 inline-flex items-center gap-2">
                <Download className="w-4 h-4" /> Download PDF
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    draft: 'bg-gray-800 text-gray-400',
    final: 'bg-green-900/30 text-green-400',
    under_review: 'bg-blue-900/30 text-blue-400',
    revision: 'bg-yellow-900/30 text-yellow-400',
  };
  return <span className={`px-2 py-0.5 rounded text-xs ${colors[status] || 'bg-gray-800 text-gray-400'}`}>{status}</span>;
}
