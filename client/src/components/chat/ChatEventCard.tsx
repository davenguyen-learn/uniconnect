import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, MapPin, Award, AlertTriangle, ArrowRight, Navigation } from 'lucide-react';
import type { ChatEventCardViewModel } from '../../types/chat-mapper';

interface ChatEventCardProps {
  card: ChatEventCardViewModel;
}

export const ChatEventCard: React.FC<ChatEventCardProps> = ({ card }) => {
  const navigate = useNavigate();

  return (
    <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-indigo-300 transition duration-200 text-left">
      {/* Header with Title & Conflict Warning */}
      <div className="flex items-start justify-between gap-2">
        <h4 
          onClick={() => navigate(`/activities/${card.activityId}`)}
          className="font-bold text-slate-900 text-sm line-clamp-1 hover:text-indigo-600 cursor-pointer transition-colors"
          title={card.title}
        >
          {card.title}
        </h4>
        {card.conflictBadge.variant !== 'none' && (
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold shrink-0 ${
              card.conflictBadge.variant === 'danger'
                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}
          >
            <AlertTriangle className="w-3 h-3" />
            {card.conflictBadge.label}
          </span>
        )}
      </div>

      {/* Organizing Group Link if any */}
      {card.groupName && card.groupId && (
        <div className="mt-1">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/groups/${card.groupId}`);
            }}
            className="inline-flex items-center gap-1 text-[11px] font-medium text-indigo-600 hover:underline"
          >
            Nhóm: {card.groupName}
          </button>
        </div>
      )}

      {/* Meta: Time & Location */}
      <div className="mt-1.5 space-y-1 text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>{card.dateTimeFormatted}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="line-clamp-1">{card.locationName}</span>
        </div>
      </div>

      {/* Badges strip: CTXH + Distance */}
      <div className="mt-2.5 flex items-center gap-2 flex-wrap">
        {card.ctxhFormatted && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
            <Award className="w-3 h-3 text-amber-600" />
            {card.ctxhFormatted}
          </span>
        )}

        {card.distanceFormatted && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600">
            <Navigation className="w-3 h-3 text-slate-400" />
            {card.distanceFormatted}
          </span>
        )}
      </div>

      {/* Action Footer */}
      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between">
        <span
          className={`text-[11px] font-semibold ${
            card.statusBadge.variant === 'available'
              ? 'text-emerald-600'
              : card.statusBadge.variant === 'registered'
              ? 'text-blue-600'
              : 'text-slate-400'
          }`}
        >
          {card.statusBadge.label}
        </span>

        <button
          onClick={() => navigate(`/activities/${card.activityId}`)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
        >
          {card.ctaLabel}
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
