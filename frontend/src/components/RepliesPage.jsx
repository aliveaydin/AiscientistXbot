import React, { useState, useEffect } from 'react';
import { MessageCircle, User, ArrowRight, Clock, Bot } from 'lucide-react';
import { getReplies } from '../api';

export default function RepliesPage() {
  const [replies, setReplies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReplies();
    const interval = setInterval(loadReplies, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadReplies = async () => {
    try {
      const res = await getReplies();
      setReplies(res.data);
    } catch (err) {
      console.error('Failed to load replies:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'replied': return 'badge-success';
      case 'pending': return 'badge-warning';
      case 'failed': return 'badge-error';
      case 'skipped': return 'badge-info';
      default: return 'badge-info';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Auto Replies</h2>
        <p className="text-gray-400 text-sm mt-1">Monitor AI-generated replies to incoming comments</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : replies.length > 0 ? (
        <div className="space-y-4">
          {replies.map((reply) => (
            <div key={reply.id} className="card hover:border-gray-700 transition-all">
              {/* Incoming reply */}
              <div className="flex items-start gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-gray-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-white">@{reply.incoming_user}</span>
                    <span className={getStatusBadge(reply.status)}>{reply.status}</span>
                  </div>
                  <p className="text-sm text-gray-300 bg-gray-800/50 rounded-lg p-3">{reply.incoming_text}</p>
                </div>
              </div>

              {/* Bot response */}
              {reply.response_text && (
                <div className="flex items-start gap-3 ml-6 pl-5 border-l-2 border-blue-500/30">
                  <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-blue-400">Bot Reply</span>
                      {reply.ai_model_used && (
                        <span className="badge-info">{reply.ai_model_used}</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-300 bg-blue-500/10 rounded-lg p-3">{reply.response_text}</p>
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(reply.created_at).toLocaleString()}
                </span>
                {reply.replied_at && (
                  <span className="flex items-center gap-1">
                    <ArrowRight className="w-3 h-3" />
                    Replied: {new Date(reply.replied_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card flex items-center justify-center h-48 text-gray-500">
          <div className="text-center">
            <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No replies yet. When people respond to your tweets,</p>
            <p>the bot will automatically generate and post replies.</p>
          </div>
        </div>
      )}
    </div>
  );
}
