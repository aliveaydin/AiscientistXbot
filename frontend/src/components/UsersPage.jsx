import { useState, useEffect } from 'react';
import { getAdminUsers, getAdminUserDetail, adminAddCredits, adminSetPlan } from '../api';
import { Users, Search, ChevronLeft, Mail, Calendar, Box, FlaskConical, Cpu, User, Zap, DollarSign } from 'lucide-react';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [detail, setDetail] = useState(null);
  const limit = 30;

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const { data } = await getAdminUsers(search, limit, offset);
      setUsers(data.users);
      setTotal(data.total);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchUsers(); }, [offset]);

  const handleSearch = (e) => {
    e.preventDefault();
    setOffset(0);
    fetchUsers();
  };

  const openDetail = async (userId) => {
    setSelectedUser(userId);
    try {
      const { data } = await getAdminUserDetail(userId);
      setDetail(data);
    } catch (e) { console.error(e); }
  };

  if (selectedUser && detail) {
    const u = detail.user;
    return (
      <div className="p-6 space-y-6">
        <button onClick={() => { setSelectedUser(null); setDetail(null); }} className="flex items-center gap-2 text-gray-400 hover:text-white text-sm">
          <ChevronLeft className="w-4 h-4" /> Back to Users
        </button>
        <div className="flex items-center gap-4">
          {u.avatar_url ? (
            <img src={u.avatar_url} alt="" className="w-14 h-14 rounded-full" />
          ) : (
            <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center"><User className="w-6 h-6 text-gray-400" /></div>
          )}
          <div>
            <h2 className="text-xl font-bold text-white">{u.display_name || u.username || 'No name'}</h2>
            <p className="text-sm text-gray-400">{u.email}</p>
            <p className="text-xs text-gray-500">@{u.username || '—'} · Joined {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</p>
          </div>
        </div>
        {u.bio && <p className="text-sm text-gray-400 bg-gray-800/50 rounded-lg p-3">{u.bio}</p>}

        {/* Credit & Plan Management */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium text-white">Credits & Plan</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Plan:</span>
                <span className="text-white font-medium">{u.plan || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Balance:</span>
                <span className="text-yellow-400 font-mono font-medium">${(u.credit_balance || 0).toFixed(2)}</span>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <select
                className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-white"
                defaultValue=""
                onChange={async (e) => {
                  if (e.target.value) {
                    await adminSetPlan(u.id, e.target.value);
                    const { data } = await getAdminUserDetail(u.id);
                    setDetail(data);
                  }
                }}
              >
                <option value="" disabled>Change plan</option>
                <option value="free">Free</option>
                <option value="starter">Starter</option>
                <option value="pro">Pro</option>
                <option value="lab">Lab</option>
              </select>
              <button
                className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-500"
                onClick={async () => {
                  const amt = prompt('Credits to add ($):');
                  if (amt && parseFloat(amt) > 0) {
                    await adminAddCredits(u.id, parseFloat(amt), 'Admin grant');
                    const { data } = await getAdminUserDetail(u.id);
                    setDetail(data);
                  }
                }}
              >
                + Add Credits
              </button>
            </div>
          </div>

          {/* Recent Transactions */}
          {detail.credit_transactions && detail.credit_transactions.length > 0 && (
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-white">Recent Transactions</span>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {detail.credit_transactions.map(tx => (
                  <div key={tx.id} className="flex justify-between text-xs">
                    <span className="text-gray-400 capitalize">{tx.operation.replace(/_/g, ' ')}</span>
                    <span className={tx.amount >= 0 ? 'text-green-400 font-mono' : 'text-red-400 font-mono'}>
                      {tx.amount >= 0 ? '+' : ''}{tx.amount.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <Section title="Environments" count={detail.environments.length} icon={<Box className="w-4 h-4" />}>
          {detail.environments.length === 0 ? <Empty /> : (
            <table className="w-full text-sm">
              <thead><tr className="text-gray-500 text-left text-xs">
                <th className="pb-2">Name</th><th className="pb-2">Category</th><th className="pb-2">Status</th><th className="pb-2">Ver</th><th className="pb-2">Created</th>
              </tr></thead>
              <tbody>
                {detail.environments.map(e => (
                  <tr key={e.id} className="border-t border-gray-800 text-gray-300">
                    <td className="py-2">{e.name}</td>
                    <td className="py-2"><span className="px-2 py-0.5 bg-gray-800 rounded text-xs">{e.category}</span></td>
                    <td className="py-2"><StatusBadge status={e.status} /></td>
                    <td className="py-2 text-gray-500">v{e.version}</td>
                    <td className="py-2 text-gray-500 text-xs">{e.created_at ? new Date(e.created_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        <Section title="Training Runs" count={detail.training_runs.length} icon={<Cpu className="w-4 h-4" />}>
          {detail.training_runs.length === 0 ? <Empty /> : (
            <table className="w-full text-sm">
              <thead><tr className="text-gray-500 text-left text-xs">
                <th className="pb-2">ID</th><th className="pb-2">Env</th><th className="pb-2">Algorithm</th><th className="pb-2">Status</th><th className="pb-2">Created</th>
              </tr></thead>
              <tbody>
                {detail.training_runs.map(t => (
                  <tr key={t.id} className="border-t border-gray-800 text-gray-300">
                    <td className="py-2 text-gray-500">#{t.id}</td>
                    <td className="py-2">Env #{t.env_id}</td>
                    <td className="py-2"><span className="px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded text-xs">{t.algorithm}</span></td>
                    <td className="py-2"><StatusBadge status={t.status} /></td>
                    <td className="py-2 text-gray-500 text-xs">{t.created_at ? new Date(t.created_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        <Section title="Research Projects" count={detail.research_projects.length} icon={<FlaskConical className="w-4 h-4" />}>
          {detail.research_projects.length === 0 ? <Empty /> : (
            <table className="w-full text-sm">
              <thead><tr className="text-gray-500 text-left text-xs">
                <th className="pb-2">Title</th><th className="pb-2">Phase</th><th className="pb-2">Status</th><th className="pb-2">Created</th>
              </tr></thead>
              <tbody>
                {detail.research_projects.map(p => (
                  <tr key={p.id} className="border-t border-gray-800 text-gray-300">
                    <td className="py-2">{p.title}</td>
                    <td className="py-2 text-gray-500">{p.current_phase || '—'}</td>
                    <td className="py-2"><StatusBadge status={p.status} /></td>
                    <td className="py-2 text-gray-500 text-xs">{p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>
      </div>
    );
  }

  const totalPages = Math.ceil(total / limit);
  const page = Math.floor(offset / limit) + 1;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="w-5 h-5 text-blue-400" />
          <h1 className="text-xl font-bold text-white">Registered Users</h1>
          <span className="text-sm text-gray-500">{total} total</span>
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search users..."
              className="bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 w-64"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500">Search</button>
        </form>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-left text-xs">
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Plan</th>
              <th className="px-4 py-3 text-right">Credits</th>
              <th className="px-4 py-3 text-center">Envs</th>
              <th className="px-4 py-3 text-center">Training</th>
              <th className="px-4 py-3 text-center">Research</th>
              <th className="px-4 py-3">Joined</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">No users found</td></tr>
            ) : users.map(u => (
              <tr key={u.id} onClick={() => openDetail(u.id)} className="border-t border-gray-800 hover:bg-gray-800/50 cursor-pointer transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {u.avatar_url ? (
                      <img src={u.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs text-gray-400">
                        {(u.username || u.email || '?')[0].toUpperCase()}
                      </div>
                    )}
                    <div>
                      <p className="text-white font-medium">{u.display_name || u.username || '—'}</p>
                      <p className="text-xs text-gray-500">@{u.username || '—'}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-400">{u.email || '—'}</td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-300">{u.plan || '—'}</span></td>
                <td className="px-4 py-3 text-right font-mono text-yellow-400 text-xs">${(u.credit_balance || 0).toFixed(2)}</td>
                <td className="px-4 py-3 text-center"><CountBadge n={u.env_count} color="emerald" /></td>
                <td className="px-4 py-3 text-center"><CountBadge n={u.training_count} color="blue" /></td>
                <td className="px-4 py-3 text-center"><CountBadge n={u.research_count} color="amber" /></td>
                <td className="px-4 py-3 text-gray-500 text-xs">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
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

function Section({ title, count, icon, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-gray-400">{icon}</span>
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        <span className="text-xs text-gray-500">({count})</span>
      </div>
      {children}
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-green-900/30 text-green-400', published: 'bg-green-900/30 text-green-400',
    running: 'bg-blue-900/30 text-blue-400', active: 'bg-blue-900/30 text-blue-400',
    failed: 'bg-red-900/30 text-red-400', draft: 'bg-gray-800 text-gray-400',
    pending: 'bg-yellow-900/30 text-yellow-400',
  };
  return <span className={`px-2 py-0.5 rounded text-xs ${colors[status] || 'bg-gray-800 text-gray-400'}`}>{status}</span>;
}

function CountBadge({ n, color }) {
  if (!n) return <span className="text-gray-600">0</span>;
  const cls = { emerald: 'text-emerald-400', blue: 'text-blue-400', amber: 'text-amber-400' };
  return <span className={`font-medium ${cls[color] || 'text-white'}`}>{n}</span>;
}

function Empty() {
  return <p className="text-sm text-gray-500 py-2">No data yet</p>;
}
