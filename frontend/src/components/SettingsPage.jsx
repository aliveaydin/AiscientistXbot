import React, { useState, useEffect } from 'react';
import { 
  Settings, Save, Play, Square, CheckCircle, XCircle, 
  Loader2, Wifi, Brain, Clock, MessageCircle, Zap
} from 'lucide-react';
import { 
  getSettings, updateSettings, startScheduler, stopScheduler, 
  getSchedulerStatus, testTwitter, testAI 
} from '../api';

export default function SettingsPage() {
  const [settings, setSettingsState] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testResults, setTestResults] = useState({});
  const [testing, setTesting] = useState({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [settingsRes, statusRes] = await Promise.all([
        getSettings(),
        getSchedulerStatus(),
      ]);
      setSettingsState(settingsRes.data);
      setSchedulerStatus(statusRes.data);
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSettings(settings);
      alert('Settings saved successfully!');
    } catch (err) {
      alert('Failed to save: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleStartScheduler = async () => {
    try {
      await startScheduler();
      await loadSettings();
    } catch (err) {
      alert('Failed to start scheduler: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleStopScheduler = async () => {
    try {
      await stopScheduler();
      await loadSettings();
    } catch (err) {
      alert('Failed to stop scheduler: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleTestTwitter = async () => {
    setTesting({ ...testing, twitter: true });
    try {
      const res = await testTwitter();
      setTestResults({ ...testResults, twitter: res.data });
    } catch (err) {
      setTestResults({ ...testResults, twitter: { success: false, error: err.message } });
    } finally {
      setTesting({ ...testing, twitter: false });
    }
  };

  const handleTestAI = async (model) => {
    setTesting({ ...testing, [model]: true });
    try {
      const res = await testAI(model);
      setTestResults({ ...testResults, [model]: res.data });
    } catch (err) {
      setTestResults({ ...testResults, [model]: { success: false, error: err.message } });
    } finally {
      setTesting({ ...testing, [model]: false });
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
      <div>
        <h2 className="text-2xl font-bold text-white">Settings</h2>
        <p className="text-gray-400 text-sm mt-1">Configure your AI bot preferences and connections</p>
      </div>

      {/* Scheduler Control */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          Bot Scheduler
        </h3>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            schedulerStatus?.is_running 
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
              : 'bg-gray-800 text-gray-400 border border-gray-700'
          }`}>
            <div className={`w-2.5 h-2.5 rounded-full ${schedulerStatus?.is_running ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'}`} />
            <span className="text-sm font-medium">{schedulerStatus?.is_running ? 'Running' : 'Stopped'}</span>
          </div>
          
          {schedulerStatus?.is_running ? (
            <button onClick={handleStopScheduler} className="btn-danger">
              <Square className="w-4 h-4" /> Stop Bot
            </button>
          ) : (
            <button onClick={handleStartScheduler} className="btn-success">
              <Play className="w-4 h-4" /> Start Bot
            </button>
          )}
        </div>

        {schedulerStatus?.jobs?.length > 0 && (
          <div className="mt-4 space-y-2">
            {schedulerStatus.jobs.map((job) => (
              <div key={job.id} className="flex items-center gap-3 text-sm text-gray-400 bg-gray-800/50 rounded-lg px-3 py-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="font-medium text-gray-300">{job.name}</span>
                {job.next_run && (
                  <span className="text-xs text-gray-500">Next: {new Date(job.next_run).toLocaleString()}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Model Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          AI Model Configuration
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Default AI Model</label>
            <select
              value={settings?.default_ai_model || 'claude-sonnet-4-20250514'}
              onChange={(e) => setSettingsState({ ...settings, default_ai_model: e.target.value })}
              className="select-field"
            >
              <optgroup label="Anthropic (Recommended)">
                <option value="claude-sonnet-4-20250514">Claude Sonnet 4 ⭐</option>
                <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku (Fast)</option>
                <option value="claude-3-opus-20240229">Claude 3 Opus</option>
              </optgroup>
              <optgroup label="OpenAI">
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4o-mini">GPT-4o Mini (Cheap)</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-4">GPT-4</option>
              </optgroup>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Tweet Interval (minutes)</label>
            <input
              type="number"
              value={settings?.tweet_interval_minutes || 120}
              onChange={(e) => setSettingsState({ ...settings, tweet_interval_minutes: parseInt(e.target.value) })}
              className="input-field"
              min={5}
              max={1440}
            />
          </div>
        </div>
      </div>

      {/* Auto Reply Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-cyan-400" />
          Auto Reply
        </h3>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.auto_reply_enabled || false}
                onChange={(e) => setSettingsState({ ...settings, auto_reply_enabled: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
            </label>
            <span className="text-sm text-gray-300">Enable automatic replies to mentions</span>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Tweet Style</label>
            <input
              type="text"
              value={settings?.tweet_style || ''}
              onChange={(e) => setSettingsState({ ...settings, tweet_style: e.target.value })}
              className="input-field"
              placeholder="e.g., popular science, engaging, humorous"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Reply Style</label>
            <input
              type="text"
              value={settings?.reply_style || ''}
              onChange={(e) => setSettingsState({ ...settings, reply_style: e.target.value })}
              className="input-field"
              placeholder="e.g., friendly, informative, conversational"
            />
          </div>
        </div>
      </div>

      {/* Connection Tests */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Wifi className="w-5 h-5 text-green-400" />
          Connection Tests
        </h3>
        <div className="space-y-3">
          {/* Twitter Test */}
          <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
            <button
              onClick={handleTestTwitter}
              disabled={testing.twitter}
              className="btn-secondary text-sm py-1.5 px-4"
            >
              {testing.twitter ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
              Test Twitter
            </button>
            {testResults.twitter && (
              <div className="flex items-center gap-2">
                {testResults.twitter.success ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm text-emerald-400">Connected as @{testResults.twitter.username}</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-red-400" />
                    <span className="text-sm text-red-400">{testResults.twitter.error}</span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* OpenAI Test */}
          <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
            <button
              onClick={() => handleTestAI('gpt-4')}
              disabled={testing['gpt-4']}
              className="btn-secondary text-sm py-1.5 px-4"
            >
              {testing['gpt-4'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
              Test OpenAI
            </button>
            {testResults['gpt-4'] && (
              <div className="flex items-center gap-2">
                {testResults['gpt-4'].success ? (
                  <><CheckCircle className="w-4 h-4 text-emerald-400" /><span className="text-sm text-emerald-400">Connected</span></>
                ) : (
                  <><XCircle className="w-4 h-4 text-red-400" /><span className="text-sm text-red-400">{testResults['gpt-4'].error}</span></>
                )}
              </div>
            )}
          </div>

          {/* Claude Test */}
          <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
            <button
              onClick={() => handleTestAI('claude-sonnet-4-20250514')}
              disabled={testing['claude-sonnet-4-20250514']}
              className="btn-secondary text-sm py-1.5 px-4"
            >
              {testing['claude-sonnet-4-20250514'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
              Test Claude
            </button>
            {testResults['claude-sonnet-4-20250514'] && (
              <div className="flex items-center gap-2">
                {testResults['claude-sonnet-4-20250514'].success ? (
                  <><CheckCircle className="w-4 h-4 text-emerald-400" /><span className="text-sm text-emerald-400">Connected</span></>
                ) : (
                  <><XCircle className="w-4 h-4 text-red-400" /><span className="text-sm text-red-400">{testResults['claude-sonnet-4-20250514'].error}</span></>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button onClick={handleSave} disabled={saving} className="btn-primary px-6">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save Settings
        </button>
      </div>
    </div>
  );
}
