import React, { useState, useEffect } from 'react';
import { 
  Send, Heart, Repeat2, Eye, MessageCircle, FileText,
  TrendingUp, Clock, Zap, Activity
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { getDashboardStats, getActivityLogs, getChartData } from '../api';

function StatCard({ icon: Icon, label, value, color, subtext }) {
  return (
    <div className="stat-card group hover:border-gray-700 transition-all">
      <div className="flex items-center justify-between">
        <div className={`w-10 h-10 rounded-lg bg-${color}-500/20 flex items-center justify-center`}>
          <Icon className={`w-5 h-5 text-${color}-400`} />
        </div>
        <span className="text-2xl font-bold text-white">{value?.toLocaleString() ?? 0}</span>
      </div>
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        {subtext && <p className="text-xs text-gray-500 mt-0.5">{subtext}</p>}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    success: 'badge-success',
    error: 'badge-error',
    warning: 'badge-warning',
    info: 'badge-info',
  };
  return <span className={styles[status] || 'badge-info'}>{status}</span>;
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, activityRes, chartRes] = await Promise.all([
        getDashboardStats(),
        getActivityLogs(20),
        getChartData(7),
      ]);
      setStats(statsRes.data);
      setActivity(activityRes.data);
      setChartData(chartRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Dashboard</h2>
          <p className="text-gray-400 text-sm mt-1">Overview of your bot's performance</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-sm text-emerald-400">Live</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Send} label="Total Tweets" value={stats?.total_tweets} color="blue" subtext={`${stats?.tweets_today || 0} today`} />
        <StatCard icon={Heart} label="Total Likes" value={stats?.total_likes} color="rose" />
        <StatCard icon={Repeat2} label="Total Retweets" value={stats?.total_retweets} color="emerald" />
        <StatCard icon={Eye} label="Impressions" value={stats?.total_impressions} color="purple" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={MessageCircle} label="Auto Replies" value={stats?.total_replies} color="cyan" subtext={`${stats?.replies_today || 0} today`} />
        <StatCard icon={FileText} label="Articles" value={stats?.total_articles} color="amber" />
        <StatCard icon={TrendingUp} label="Engagement Rate" value={`${stats?.avg_engagement_rate || 0}%`} color="green" />
        <StatCard icon={Activity} label="Active" value={stats?.tweets_today || 0} color="indigo" subtext="tweets today" />
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Engagement Over Time</h3>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorLikes" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorRetweets" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorImpressions" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 12 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111827',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Area type="monotone" dataKey="likes" stroke="#f43f5e" fillOpacity={1} fill="url(#colorLikes)" />
              <Area type="monotone" dataKey="retweets" stroke="#10b981" fillOpacity={1} fill="url(#colorRetweets)" />
              <Area type="monotone" dataKey="impressions" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorImpressions)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No chart data yet. Post some tweets to see engagement!</p>
            </div>
          </div>
        )}
      </div>

      {/* Activity Log */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        {activity.length > 0 ? (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {activity.map((log) => (
              <div key={log.id} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
                <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                  log.status === 'success' ? 'bg-emerald-400' :
                  log.status === 'error' ? 'bg-red-400' :
                  log.status === 'warning' ? 'bg-yellow-400' : 'bg-blue-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{log.action.replace(/_/g, ' ')}</span>
                    <StatusBadge status={log.status} />
                  </div>
                  {log.details && (
                    <p className="text-xs text-gray-400 mt-1 truncate">{log.details}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(log.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-32 text-gray-500">
            <div className="text-center">
              <Clock className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No activity yet. Start the bot to see logs!</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
