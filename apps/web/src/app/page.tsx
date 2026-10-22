"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/navigation/Sidebar";
import { KnowledgeDashboard } from "@/components/dashboard/KnowledgeDashboard";
import { ChatWorkspace } from "@/components/chat/ChatWorkspace";
import { SourceDrawer } from "@/components/chat/SourceDrawer";
import { api } from "@/lib/api";
import { Document, ChatMessage, Citation } from "@/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "chat">("dashboard");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [userEmail, setUserEmail] = useState<string>("analyst@mnemos.ai");
  const [selectedDocumentScope, setSelectedDocumentScope] = useState<string | null>(null);

  // Load initial documents & ensure user session
  useEffect(() => {
    async function init() {
      try {
        // Attempt login with default demo account or register if fresh
        try {
          await api.login({ email: "analyst@mnemos.ai", password: "Password123!" });
        } catch {
          await api.register({ email: "analyst@mnemos.ai", password: "Password123!" });
          await api.login({ email: "analyst@mnemos.ai", password: "Password123!" });
        }

        const me = await api.getMe();
        setUserEmail(me.email);

        const docs = await api.getDocuments();
        setDocuments(docs);

        const convs = await api.getConversations();
        setConversations(convs);

        if (convs.length > 0) {
          setActiveConversationId(convs[0].id);
          const fullConv = await api.getConversation(convs[0].id);
          setMessages(fullConv.messages || []);
        }
      } catch (err) {
        console.warn("API initialization fallback in local demo mode:", err);
      }
    }
    init();
  }, []);

  const handleUpload = async (file: File) => {
    const uploaded = await api.uploadDocument(file);
    // Refresh documents list
    const docs = await api.getDocuments();
    setDocuments(docs);
  };

  const handleDelete = async (id: string) => {
    await api.deleteDocument(id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  const handleInspectDocument = (doc: Document) => {
    // Open source drawer showing sample document preview
    setSelectedCitation({
      id: doc.id,
      citation_index: 1,
      document_id: doc.id,
      document_title: doc.original_filename,
      page_number: doc.page_count ? 1 : null,
      excerpt: `Document '${doc.original_filename}' is verified and indexed in your workspace. (Size: ${(doc.file_size_bytes / 1024).toFixed(1)} KB, Status: ${doc.status})`,
      chunk_id: null,
      similarity_score: 1.0,
    });
    setIsDrawerOpen(true);
  };

  const handleSendMessage = async (content: string) => {
    setIsSending(true);

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      let convId = activeConversationId;
      if (!convId) {
        const scope = selectedDocumentScope ? "DOCUMENT" : "WORKSPACE";
        const newConv = await api.createConversation(
          content.slice(0, 40),
          scope,
          selectedDocumentScope || undefined
        );
        convId = newConv.id;
        setActiveConversationId(newConv.id);
      }

      if (!convId) {
        throw new Error("Unable to establish conversation session.");
      }

      const res = await api.sendMessage(convId, content);

      // Map response citations
      const mappedCitations: Citation[] = (res.citations || []).map((c: any, idx: number) => ({
        id: c.id,
        citation_index: idx + 1,
        document_id: c.document_id,
        document_title: c.document_title,
        page_number: c.page_number,
        excerpt: c.excerpt,
        chunk_id: c.chunk_id,
        similarity_score: c.similarity_score,
      }));

      const assistantMsg: ChatMessage = {
        id: res.id,
        role: "assistant",
        content: res.content,
        citations: mappedCitations,
        insufficient_evidence: res.insufficient_evidence,
        created_at: res.created_at,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: "err-" + Date.now(),
        role: "assistant",
        content: `Error generating response: ${err.message || "Failed to reach backend."}`,
        insufficient_evidence: true,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSelectCitation = (citation: Citation) => {
    setSelectedCitation(citation);
    setIsDrawerOpen(true);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-black text-white">
      {/* Primary Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        userEmail={userEmail}
      />

      {/* Main Workspace Body */}
      <main className="flex-1 flex overflow-hidden relative">
        {activeTab === "dashboard" ? (
          <KnowledgeDashboard
            documents={documents}
            onUpload={handleUpload}
            onDelete={handleDelete}
            onInspectDocument={handleInspectDocument}
          />
        ) : (
          <ChatWorkspace
            messages={messages}
            documents={documents}
            selectedDocumentId={selectedDocumentScope}
            onSelectDocumentScope={(docId) => {
              setSelectedDocumentScope(docId);
              setActiveConversationId(null);
              setMessages([]);
            }}
            onSendMessage={handleSendMessage}
            onSelectCitation={handleSelectCitation}
            isSending={isSending}
          />
        )}

        {/* Verifiable Source Inspection Drawer */}
        <SourceDrawer
          citation={selectedCitation}
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
        />
      </main>
    </div>
  );
}
