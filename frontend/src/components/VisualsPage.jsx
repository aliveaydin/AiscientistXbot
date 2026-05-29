import React, { useState, useEffect } from 'react';
import { Image as ImageIcon, RefreshCw, Download, Eye, Trash2, Copy, X } from 'lucide-react';
import { listVisuals, getVisualUrl } from '../api';

export default function VisualsPage() {
  const [visuals, setVisuals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await listVisuals();
      setVisuals(res.data.visuals || []);
    } catch (e) {
      console.error('Failed to load visuals:', e);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const getUrl = (v) => `/api/marketing/visuals/${v.filename}`;

  const copyUrl = (v) => {
    navigator.clipboard.writeText(window.location.origin + getUrl(v));
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ImageIcon className="w-6 h-6 text-purple-400" /> Visual Gallery
          </h1>
          <p className="text-gray-400 text-sm mt-1">All generated marketing visuals — {visuals.length} images</p>
        </div>
        <button onClick={load} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading visuals...</div>
      ) : visuals.length === 0 ? (
        <div className="text-center py-20">
          <ImageIcon className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">No visuals generated yet.</p>
          <p className="text-gray-600 text-sm mt-1">Generate visual tweets from the GTM Tweets page to see them here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {visuals.map((v, i) => {
            const templateName = v.filename.replace(/_\d{8}_\d{6}\.png$/, '').replace(/_/g, ' ');
            return (
              <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden group hover:border-gray-600 transition-all">
                <div className="relative aspect-video bg-gray-800">
                  <img
                    src={getUrl(v)}
                    alt={v.filename}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextElementSibling.style.display = 'flex';
                    }}
                  />
                  <div className="hidden items-center justify-center w-full h-full text-gray-600">
                    <ImageIcon className="w-8 h-8" />
                  </div>
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <button onClick={() => setPreview(getUrl(v))}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white backdrop-blur-sm">
                      <Eye className="w-5 h-5" />
                    </button>
                    <a href={getUrl(v)} download={v.filename}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white backdrop-blur-sm">
                      <Download className="w-5 h-5" />
                    </a>
                    <button onClick={() => copyUrl(v)}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white backdrop-blur-sm">
                      <Copy className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <div className="p-3">
                  <p className="text-sm text-white font-medium capitalize truncate">{templateName}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-gray-500">{formatSize(v.size_bytes)}</span>
                    <span className="text-xs text-gray-600">
                      {v.created_at ? new Date(v.created_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Preview Modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={() => setPreview(null)}>
          <div className="relative max-w-4xl w-full mx-4">
            <button onClick={() => setPreview(null)}
              className="absolute -top-12 right-0 p-2 text-gray-400 hover:text-white">
              <X className="w-6 h-6" />
            </button>
            <img src={preview} alt="Preview" className="w-full rounded-xl shadow-2xl" />
          </div>
        </div>
      )}
    </div>
  );
}
