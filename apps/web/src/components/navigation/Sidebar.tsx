"use client";

import React from "react";
import { 
  Database, 
  MessageSquare, 
  Layers, 
  FolderGit2, 
  ShieldCheck, 
  ChevronRight,
  LogOut,
  Search,
  Sparkles
} from "lucide-react";

interface SidebarProps {
  activeTab: "dashboard" | "chat";
  onTabChange: (tab: "dashboard" | "chat") => void;
  userEmail?: string;
  onLogout?: () => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ 
  activeTab, 
  onTabChange, 
  userEmail, 
  onLogout,
  isOpenMobile = false,
  onCloseMobile
}: SidebarProps) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div 
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-200"
        />
      )}

      {/* Sidebar Navigation */}
      <aside 
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-[#050505] border-r border-[#1C1C1C] flex flex-col justify-between shrink-0 h-screen select-none transition-transform duration-200 ease-in-out ${
          isOpenMobile ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Brand & Workspace */}
        <div className="p-4 space-y-6">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 text-white flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-white/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-base tracking-tight text-white">Mnemos</span>
                  <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                    PRO
                  </span>
                </div>
                <p className="text-[11px] text-neutral-400 font-medium">Knowledge Assistant</p>
              </div>
            </div>

            {/* Mobile Close Button */}
            {onCloseMobile && (
              <button
                onClick={onCloseMobile}
                className="md:hidden p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
              >
                ✕
              </button>
            )}
          </div>

        {/* Workspace Selector */}
        <div className="bg-[#0C0C0C] border border-[#1F1F1F] rounded-xl p-2.5 flex items-center justify-between hover:border-indigo-500/40 transition cursor-pointer group">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-7 h-7 rounded-lg bg-indigo-950/50 border border-indigo-500/30 flex items-center justify-center shrink-0 text-xs font-semibold text-indigo-300 group-hover:scale-105 transition">
              W1
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-white truncate group-hover:text-indigo-200 transition">Default Workspace</p>
              <p className="text-[10px] text-neutral-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-pulse" />
                Isolated & Protected
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-neutral-500 shrink-0 group-hover:text-indigo-400 transition" />
        </div>

        {/* Primary Navigation */}
        <nav className="space-y-1.5">
          <button
            onClick={() => {
              onTabChange("dashboard");
              onCloseMobile?.();
            }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              activeTab === "dashboard"
                ? "bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/30 font-medium"
                : "text-neutral-400 hover:text-white hover:bg-white/[0.06]"
            }`}
          >
            <Database className={`w-4 h-4 shrink-0 ${activeTab === "dashboard" ? "text-white" : "text-neutral-400"}`} />
            <span>Knowledge Corpus</span>
          </button>

          <button
            onClick={() => {
              onTabChange("chat");
              onCloseMobile?.();
            }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              activeTab === "chat"
                ? "bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/30 font-medium"
                : "text-neutral-400 hover:text-white hover:bg-white/[0.06]"
            }`}
          >
            <MessageSquare className={`w-4 h-4 shrink-0 ${activeTab === "chat" ? "text-white" : "text-neutral-400"}`} />
            <span>AI Research Chat</span>
          </button>
        </nav>
      </div>

      {/* Footer / System Status & User Profile */}
      <div className="p-4 border-t border-[#1C1C1C] space-y-4">
        <div className="bg-[#0C0C0C] rounded-xl p-3 border border-[#1F1F1F] space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-neutral-300 flex items-center gap-1.5 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
              Grounded RAG Mode
            </span>
            <span className="text-emerald-400 font-semibold text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
              Strict
            </span>
          </div>
          <p className="text-[10px] text-neutral-400 leading-relaxed">
            Zero fabricated citations. Inquiries require verified source passage overlap.
          </p>
        </div>

        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2 truncate pr-2">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-sm shadow-indigo-500/20">
              {(userEmail || "U")[0].toUpperCase()}
            </div>
            <div className="truncate">
              <p className="text-xs font-medium text-white truncate">{userEmail || "user@mnemos.ai"}</p>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-emerald-400" />
                Active Session
              </p>
            </div>
          </div>
          {onLogout && (
            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-neutral-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
    </>
  );
}
