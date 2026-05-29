import React, { useState, useEffect } from 'react';
import { Calendar, RefreshCw, Zap, BarChart3, GraduationCap, BookOpen } from 'lucide-react';
import { getMarketingCalendar, getMarketingStats } from '../api';

const TYPE_CONFIG = {
  product: { label: 'Product', icon: Zap, color: 'blue', bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  industry: { label: 'Industry', icon: BarChart3, color: 'green', bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30' },
  educational: { label: 'Educational', icon: GraduationCap, color: 'yellow', bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  showcase: { label: 'Showcase', icon: BookOpen, color: 'purple', bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30' },
};

export default function ContentCalendarPage() {
  const [calendar, setCalendar] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [calRes, statsRes] = await Promise.all([
        getMarketingCalendar(7),
        getMarketingStats(),
      ]);
      setCalendar(calRes.data.calendar);
      setStats(statsRes.data);
    } catch (e) {
      console.error('Failed to load calendar:', e);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const groupedByDate = calendar.reduce((acc, item) => {
    if (!acc[item.date]) acc[item.date] = [];
    acc[item.date].push(item);
    return acc;
  }, {});

  const dayName = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Content Calendar</h1>
          <p className="text-gray-400 text-sm mt-1">Weekly tweet schedule and content planning</p>
        </div>
        <button onClick={loadData} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-white">{stats.total_tweets}</p>
            <p className="text-xs text-gray-500">Total Tweets</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-green-400">{stats.posted_tweets}</p>
            <p className="text-xs text-gray-500">Posted</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-yellow-400">{stats.draft_tweets}</p>
            <p className="text-xs text-gray-500">Drafts</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-blue-400">{stats.weekly_tweets}</p>
            <p className="text-xs text-gray-500">This Week</p>
          </div>
        </div>
      )}

      {/* Schedule Legend */}
      <div className="flex gap-4 mb-4">
        {Object.entries(TYPE_CONFIG).map(([key, cfg]) => (
          <div key={key} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${cfg.bg} border ${cfg.border}`} />
            <span className="text-xs text-gray-400">{cfg.label}</span>
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="space-y-4">
          {Object.entries(groupedByDate).map(([date, slots]) => (
            <div key={date} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-gray-800/50 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <h3 className="text-sm font-semibold text-white">{dayName(date)}</h3>
                </div>
              </div>
              <div className="p-4 grid grid-cols-4 gap-3">
                {slots.map((slot, idx) => {
                  const cfg = TYPE_CONFIG[slot.content_type] || TYPE_CONFIG.product;
                  const Icon = cfg.icon;
                  return (
                    <div
                      key={idx}
                      className={`${cfg.bg} border ${cfg.border} rounded-lg p-3 flex items-center gap-3`}
                    >
                      <Icon className={`w-5 h-5 ${cfg.text}`} />
                      <div>
                        <p className={`text-sm font-medium ${cfg.text}`}>{cfg.label}</p>
                        <p className="text-xs text-gray-500">{slot.time} UTC</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
