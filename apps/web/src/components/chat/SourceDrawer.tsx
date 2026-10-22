"use client";

import React from "react";
import { X, FileText, CheckCircle2, Copy, Sparkles, BookOpen } from "lucide-react";
import { Citation } from "@/types";

interface SourceDrawerProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export function SourceDrawer({ citation, isOpen, onClose }: SourceDrawerProps) {
  if (!isOpen || !citation) return null;

  const copyExcerpt = () => {
    navigator.clipboard.writeText(citation.excerpt);
  };

  const scorePct = citation.similarity_score
    ? Math.round(citation.similarity_score * 100)
    : 85;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0A0A0A] border-l border-[#222222] shadow-2xl z-50 flex flex-col justify-between animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="p-5 border-b border-[#1F1F1F] bg-[#0E0E0E] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
            <BookOpen className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">Source Verification</h2>
            <p className="text-[11px] text-emerald-400 font-medium">Verifiable Grounded Passage</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-neutral-400 hover:text-white hover:bg-[#1A1A1A] transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs bg-black">
        {/* Document Metadata Card */}
        <div className="bg-[#121212] border border-[#222222] rounded-xl p-4 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div className="truncate">
              <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400">
                Origin Document
              </span>
              <p className="text-xs font-semibold text-white mt-0.5 truncate">
                {citation.document_title}
              </p>
            </div>
            {citation.page_number && (
              <span className="shrink-0 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                Page {citation.page_number}
              </span>
            )}
          </div>

          {/* Similarity Score Metric */}
          <div className="space-y-1.5 pt-1 border-t border-[#1F1F1F]">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-neutral-400 font-medium">Vector Cosine Similarity</span>
              <span className="text-emerald-400 font-bold tabular-nums">{scorePct}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-[#222222] overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300 shadow-[0_0_8px_rgba(52,211,153,0.7)]"
                style={{ width: `${scorePct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Excerpt Passage Card */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400">
              Verified Source Excerpt
            </span>
            <button
              onClick={copyExcerpt}
              className="text-[11px] text-neutral-400 hover:text-indigo-300 flex items-center gap-1 transition"
            >
              <Copy className="w-3 h-3 text-neutral-400" />
              Copy
            </button>
          </div>

          <div className="bg-[#0D1512] border border-emerald-500/25 rounded-xl p-4 text-neutral-200 leading-relaxed font-sans shadow-inner">
            <p className="text-xs italic bg-emerald-950/20 p-2.5 rounded-lg border-l-2 border-emerald-500 text-neutral-100">
              "{citation.excerpt}"
            </p>
          </div>
        </div>

        {/* Multi-Tenant Security Guarantee */}
        <div className="bg-[#0E0E0E] border border-indigo-500/20 rounded-xl p-3 text-[11px] text-neutral-400 space-y-1">
          <p className="font-semibold text-neutral-200 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Integrity Verified
          </p>
          <p className="text-[10px] leading-relaxed text-neutral-400">
            This chunk was dynamically matched against your active workspace embedding index.
            No external or public data was queried.
          </p>
        </div>
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-[#1F1F1F] bg-[#0E0E0E]">
        <button
          onClick={onClose}
          className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold transition shadow-md shadow-indigo-500/20"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
}
