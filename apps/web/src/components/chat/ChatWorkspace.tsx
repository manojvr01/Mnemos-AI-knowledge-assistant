"use client";

import React, { useState, useRef, useEffect } from "react";
import { 
  Send, 
  Sparkles, 
  BookOpen, 
  AlertTriangle, 
  ShieldCheck, 
  User, 
  Bot, 
  Loader2,
  FileText
} from "lucide-react";
import { ChatMessage, Citation, Document } from "@/types";

interface ChatWorkspaceProps {
  conversationId?: string;
  messages: ChatMessage[];
  documents?: Document[];
  selectedDocumentId?: string | null;
  onSelectDocumentScope?: (docId: string | null) => void;
  onSendMessage: (content: string) => Promise<void>;
  onSelectCitation: (citation: Citation) => void;
  isSending?: boolean;
}

export function ChatWorkspace({
  conversationId,
  messages,
  documents = [],
  selectedDocumentId = null,
  onSelectDocumentScope,
  onSendMessage,
  onSelectCitation,
  isSending,
}: ChatWorkspaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;
    const content = input;
    setInput("");
    await onSendMessage(content);
  };

  // Helper to parse [citation:N] markers into clickable citation pills
  const renderMessageContent = (msg: ChatMessage) => {
    if (msg.role !== "assistant" || !msg.citations || msg.citations.length === 0) {
      return <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>;
    }

    // Split on [citation:N]
    const parts = msg.content.split(/(\[citation:\d+\])/g);

    return (
      <div className="leading-relaxed space-y-2">
        <p className="whitespace-pre-wrap">
          {parts.map((part, i) => {
            const match = part.match(/\[citation:(\d+)\]/);
            if (match) {
              const citationIdx = parseInt(match[1]);
              const citation = msg.citations?.find((c) => c.citation_index === citationIdx) || msg.citations?.[citationIdx - 1];
              return (
                <button
                  key={i}
                  onClick={() => citation && onSelectCitation(citation)}
                  className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-full bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/35 hover:shadow-[0_0_10px_rgba(16,185,129,0.35)] text-[11px] font-semibold transition cursor-pointer"
                  title={citation ? `View source excerpt from ${citation.document_title}` : "Citation"}
                >
                  <BookOpen className="w-3 h-3 inline text-emerald-400" />
                  <span>[{citationIdx}]</span>
                </button>
              );
            }
            return part;
          })}
        </p>

        {/* Citations Footer Row */}
        <div className="pt-2 border-t border-[#1F1F1F] flex flex-wrap gap-2">
          {msg.citations.map((c, idx) => (
            <button
              key={c.id || idx}
              onClick={() => onSelectCitation(c)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0E1713] hover:bg-[#14231D] border border-emerald-500/25 hover:border-emerald-500/40 text-[11px] text-emerald-300 transition"
            >
              <FileText className="w-3 h-3 text-emerald-400" />
              <span className="font-medium truncate max-w-[140px] text-neutral-200">{c.document_title}</span>
              {c.page_number && <span className="text-emerald-400/80 font-mono text-[10px]">p.{c.page_number}</span>}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-black overflow-hidden bg-grid-pattern">
      {/* Top Banner / Mode Bar */}
      <div className="px-6 py-3.5 border-b border-[#1C1C1C] bg-[#050505]/90 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-pulse" />
            <span className="text-xs font-semibold text-white">AI Research Chat</span>
            <span className="text-neutral-600 text-xs">•</span>
            <span className="text-xs text-indigo-400 font-medium">Strictly Grounded</span>
          </div>

          {/* Scope Selector: All Documents vs Single Document */}
          <div className="flex items-center gap-1.5 ml-4 px-2.5 py-1 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs">
            <span className="text-[11px] text-indigo-300 font-medium">Scope:</span>
            <select
              value={selectedDocumentId || "ALL"}
              onChange={(e) => {
                const val = e.target.value;
                onSelectDocumentScope?.(val === "ALL" ? null : val);
              }}
              className="bg-transparent text-xs text-white font-medium focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-[#0A0A0A] text-white">
                All Documents ({documents.filter((d) => d.status === "INDEXED").length} indexed)
              </option>
              {documents
                .filter((d) => d.status === "INDEXED")
                .map((d) => (
                  <option key={d.id} value={d.id} className="bg-[#0A0A0A] text-white">
                    Single: {d.original_filename}
                  </option>
                ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-neutral-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-emerald-400 font-medium">Anti-Hallucination Active</span>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-pink-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-lg shadow-indigo-500/10">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Ask Anything About Your Documents</h3>
              <p className="text-xs text-neutral-400 mt-1">
                Every answer is synthesized strictly from your uploaded files and verified with inline citation links.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === "user";

            return (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-3xl ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-semibold ${
                    isUser
                      ? "bg-gradient-to-tr from-neutral-800 to-neutral-700 text-white border border-neutral-600 shadow-sm"
                      : "bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 text-white shadow-md shadow-indigo-500/20"
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble */}
                <div
                  className={`rounded-2xl p-4 text-xs transition-all ${
                    isUser
                      ? "bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-medium rounded-tr-none shadow-md shadow-indigo-500/15"
                      : "bg-[#0A0A0A] border border-[#1F1F1F] hover:border-[#2D2D2D] text-neutral-200 rounded-tl-none space-y-3"
                  }`}
                >
                  {msg.insufficient_evidence && (
                    <div className="bg-amber-950/30 border border-amber-500/40 rounded-xl p-3 flex items-start gap-2.5 text-amber-200">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
                      <div>
                        <p className="font-semibold text-xs text-amber-400">Insufficient Evidence in Corpus</p>
                        <p className="text-[11px] text-amber-200/80 mt-0.5">
                          The system transparently declined to speculate because no matching document passages met the confidence threshold.
                        </p>
                      </div>
                    </div>
                  )}

                  {renderMessageContent(msg)}
                </div>
              </div>
            );
          })
        )}

        {isSending && (
          <div className="flex gap-3 max-w-xl mr-auto">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shrink-0 shadow-sm shadow-indigo-500/20">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-[#0A0A0A] border border-indigo-500/30 rounded-2xl rounded-tl-none p-4 text-xs text-indigo-300 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Searching vector index & validating citations...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 border-t border-[#1C1C1C] bg-[#050505]">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your knowledge corpus..."
            disabled={isSending}
            className="w-full bg-[#0A0A0A] border border-[#222222] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-2xl px-4 py-3.5 pr-12 text-xs text-white placeholder-neutral-500 outline-none transition"
          />
          <button
            type="submit"
            disabled={!input.trim() || isSending}
            className="absolute right-2 p-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white disabled:opacity-20 transition shadow-md shadow-indigo-500/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[10px] text-neutral-500 text-center mt-2">
          Responses are strictly grounded in your active workspace documents. Click <span className="text-emerald-400 font-semibold">[citation:N]</span> pills to verify source excerpts.
        </p>
      </div>
    </div>
  );
}
