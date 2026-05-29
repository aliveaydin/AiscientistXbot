import { useState, useEffect } from 'react';
import { getAdminEnvironments } from '../api';
import { Box, Search, ChevronDown } from 'lucide-react';

export default function PlatformEnvsPage() {
  const [envs, setEnvs] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const limit = 30;

  const fetchEnvs = async () => {
    setLoading(true);
    try {
      const { data } = await getAdminEnvironments(search, category, status, limit, offset);
      setEnvs(data.environments);
      setTotal(data.total);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchEnvs(); }, [offset]);

  const handleFilter = (e) => {
    e?.preventDefault?.();
    setOffset(0);
    fetchEnvs();
  };

  const totalPages = Math.ceil(total / limit);
  const page = Math.floor(offset / limit) + 1;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Box className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-bold text-white">Platform Environments</h1>
          <span className="text-sm text-gray-500">{total} total</span>
        </div>
      </div>

      <form onSubmit={handleFilter} className="flex gap-2 flex-wrap">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search environments..."
            className="bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 w-64"
          />
        </div>
        <select value={category} onChange={e => { setCategory(e.target.value); }} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none">
          <option value="">All Categories</option>
          {['game','finance','control','optimization','robotics','healthcare','energy','custom'].map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select value={status} onChange={e => { setStatus(e.target.value); }} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none">
          <option value="">All Status</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
          <option value="ready">Ready</option>
        </select>
        <button type="submit" className="px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-500">Filter</button>
      </form>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-left text-xs">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Domain</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-center">Ver</th>
              <th className="px-4 py-3 text-center">Runs</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={10} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : envs.length === 0 ? (
              <tr><td colSpan={10} className="px-4 py-8 text-center text-gray-500">No environments found</td></tr>
            ) : envs.map(e => (
              <tr key={e.id} className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors">
                <td className="px-4 py-3 text-gray-500 font-mono text-xs">#{e.id}</td>
                <td className="px-4 py-3">
                  <p className="text-white font-medium">{e.name}</p>
                  {e.slug && <p className="text-xs text-gray-500">{e.slug}</p>}
                </td>
                <td className="px-4 py-3">
                  {e.owner ? (
                    <span className="text-blue-400 text-xs">@{e.owner}</span>
                  ) : (
                    <span className="text-gray-600 text-xs">admin</span>
                  )}
                </td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-300">{e.category}</span></td>
                <td className="px-4 py-3 text-gray-500 text-xs">{e.domain || '—'}</td>
                <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                <td className="px-4 py-3 text-center text-gray-400">v{e.version}</td>
                <td className="px-4 py-3 text-center">
                  {e.training_count > 0 ? <span className="text-blue-400 font-medium">{e.training_count}</span> : <span className="text-gray-600">0</span>}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500 font-mono">{e.ai_model_used || '—'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{e.created_at ? new Date(e.created_at).toLocaleDateString() : '—'}</td>
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
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    published: 'bg-green-900/30 text-green-400',
    ready: 'bg-blue-900/30 text-blue-400',
    draft: 'bg-gray-800 text-gray-400',
    failed: 'bg-red-900/30 text-red-400',
  };
  return <span className={`px-2 py-0.5 rounded text-xs ${colors[status] || 'bg-gray-800 text-gray-400'}`}>{status}</span>;
}
