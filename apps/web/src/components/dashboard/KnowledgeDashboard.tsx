"use client";

import React, { useRef, useState } from "react";
import { 
  UploadCloud, 
  FileText, 
  FileCheck2, 
  AlertCircle, 
  Trash2, 
  HardDrive, 
  Layers, 
  Clock, 
  ExternalLink,
  Loader2,
  FileSpreadsheet
} from "lucide-react";
import { Document } from "@/types";

interface KnowledgeDashboardProps {
  documents: Document[];
  onUpload: (file: File) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onInspectDocument: (doc: Document) => void;
  isLoading?: boolean;
}

export function KnowledgeDashboard({
  documents,
  onUpload,
  onDelete,
  onInspectDocument,
  isLoading,
}: KnowledgeDashboardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Compute metrics
  const totalDocs = documents.length;
  const indexedDocs = documents.filter((d) => d.status === "INDEXED").length;
  const totalBytes = documents.reduce((acc, d) => acc + (d.file_size_bytes || 0), 0);
  const totalPages = documents.reduce((acc, d) => acc + (d.page_count || 0), 0);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setError(null);
    setUploading(true);
    try {
      await onUpload(file);
    } catch (err: any) {
      setError(err.message || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-black bg-grid-pattern">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-[#1C1C1C] pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Knowledge Corpus</h1>
          <p className="text-xs text-neutral-400 mt-1">
            Ingest, inspect, and verify internal documents. All vectors are strictly multi-tenant isolated.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-300 border border-indigo-500/30 shadow-sm shadow-indigo-500/10">
            Google Gemini + pgvector (768-dim)
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0A0A0A] border border-sky-500/20 hover:border-sky-500/40 hover:shadow-lg hover:shadow-sky-500/5 transition-all rounded-2xl p-5 space-y-2 group">
          <div className="flex items-center justify-between text-neutral-400">
            <span className="text-xs font-semibold text-sky-400">Total Documents</span>
            <div className="w-8 h-8 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 group-hover:scale-105 transition">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white tabular-nums">{totalDocs}</p>
          <p className="text-[11px] text-neutral-400 font-medium">Active in workspace</p>
        </div>

        <div className="bg-[#0A0A0A] border border-indigo-500/20 hover:border-indigo-500/40 hover:shadow-lg hover:shadow-indigo-500/5 transition-all rounded-2xl p-5 space-y-2 group">
          <div className="flex items-center justify-between text-neutral-400">
            <span className="text-xs font-semibold text-indigo-400">Indexed Chunks</span>
            <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white tabular-nums">
            {indexedDocs} / {totalDocs}
          </p>
          <p className="text-[11px] text-neutral-400 font-medium">Ready for RAG retrieval</p>
        </div>

        <div className="bg-[#0A0A0A] border border-emerald-500/20 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/5 transition-all rounded-2xl p-5 space-y-2 group">
          <div className="flex items-center justify-between text-neutral-400">
            <span className="text-xs font-semibold text-emerald-400">Paginated Corpus</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white tabular-nums">{totalPages}</p>
          <p className="text-[11px] text-neutral-400 font-medium">Extracted PDF pages</p>
        </div>

        <div className="bg-[#0A0A0A] border border-purple-500/20 hover:border-purple-500/40 hover:shadow-lg hover:shadow-purple-500/5 transition-all rounded-2xl p-5 space-y-2 group">
          <div className="flex items-center justify-between text-neutral-400">
            <span className="text-xs font-semibold text-purple-400">Storage Allocated</span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-105 transition">
              <HardDrive className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white tabular-nums">{formatBytes(totalBytes)}</p>
          <p className="text-[11px] text-neutral-400 font-medium">Private disk storage</p>
        </div>
      </div>

      {/* Upload Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-9 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 group ${
          isDragging
            ? "border-indigo-500 bg-indigo-950/20 scale-[0.99]"
            : "border-[#262626] bg-[#0A0A0A]/60 hover:border-indigo-500/50 hover:bg-indigo-950/10"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 text-white flex items-center justify-center mb-3 shadow-lg shadow-indigo-500/25 group-hover:scale-110 transition duration-200">
          {uploading ? (
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          ) : (
            <UploadCloud className="w-6 h-6 text-white" />
          )}
        </div>
        <p className="text-sm font-semibold text-white group-hover:text-indigo-200 transition">
          {uploading ? "Ingesting & chunking document..." : "Click or drag documents to upload"}
        </p>
        <p className="text-xs text-neutral-400 mt-1 max-w-sm">
          Supports <span className="text-rose-400 font-semibold">PDF</span>,{" "}
          <span className="text-sky-400 font-semibold">DOCX</span>, and{" "}
          <span className="text-indigo-300 font-semibold">TXT</span> up to 50 MB.
        </p>
      </div>

      {error && (
        <div className="bg-rose-950/30 border border-rose-500/40 rounded-xl p-3.5 flex items-center gap-3 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Documents Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-neutral-200">Document Inventory</h2>
          <span className="text-xs text-indigo-400 font-medium px-2 py-0.5 rounded-full bg-indigo-950/40 border border-indigo-500/30">
            {documents.length} files cataloged
          </span>
        </div>

        <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#121212] border-b border-[#1F1F1F] text-neutral-400 font-medium uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-5 py-3.5">Document Title</th>
                  <th className="px-4 py-3.5">Format</th>
                  <th className="px-4 py-3.5">Size</th>
                  <th className="px-4 py-3.5">Pages</th>
                  <th className="px-4 py-3.5">Ingestion Status</th>
                  <th className="px-4 py-3.5">Added Date</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F1F1F] text-neutral-300">
                {documents.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-neutral-500">
                      No documents ingested yet. Upload files above to begin.
                    </td>
                  </tr>
                ) : (
                  documents.map((doc) => {
                    const isPdf = doc.mime_type.includes("pdf");
                    const isDocx = doc.mime_type.includes("word");

                    return (
                      <tr key={doc.id} className="hover:bg-white/[0.03] transition">
                        <td className="px-5 py-3.5 font-medium text-white flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-indigo-950/30 border border-indigo-500/30 flex items-center justify-center shrink-0">
                            <FileText className="w-4 h-4 text-indigo-400" />
                          </div>
                          <span className="truncate max-w-xs">{doc.original_filename}</span>
                        </td>
                        <td className="px-4 py-3.5">
                          {isPdf ? (
                            <span className="px-2 py-0.5 rounded-md font-mono text-[10px] font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                              PDF
                            </span>
                          ) : isDocx ? (
                            <span className="px-2 py-0.5 rounded-md font-mono text-[10px] font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30">
                              DOCX
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-md font-mono text-[10px] font-semibold bg-neutral-500/15 text-neutral-300 border border-neutral-500/30">
                              TXT
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-neutral-400 tabular-nums">
                          {formatBytes(doc.file_size_bytes)}
                        </td>
                        <td className="px-4 py-3.5 text-neutral-400 tabular-nums">
                          {doc.page_count !== null ? `${doc.page_count} pgs` : "—"}
                        </td>
                        <td className="px-4 py-3.5">
                          {doc.status === "INDEXED" ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.9)]" />
                              INDEXED
                            </span>
                          ) : doc.status === "FAILED" ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                              <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                              FAILED
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                              <Loader2 className="w-2.5 h-2.5 animate-spin text-amber-400" />
                              {doc.status}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-neutral-400 tabular-nums text-[11px]">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-5 py-3.5 text-right space-x-2">
                          <button
                            onClick={() => onInspectDocument(doc)}
                            className="p-1.5 text-neutral-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition"
                            title="Inspect Chunks & Source"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => onDelete(doc.id)}
                            className="p-1.5 text-neutral-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                            title="Delete Document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
