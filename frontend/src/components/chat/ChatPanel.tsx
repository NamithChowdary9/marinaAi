"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { chatApi } from "@/services/api";
import { useStore } from "@/store/useStore";
import { Send, X, Bot, User, Sparkles, Copy, Check, RefreshCw } from "lucide-react";
import { cn } from "@/utils/cn";
import type { ChatMessage } from "@/types";

export function ChatPanel() {
  const { setChatOpen } = useStore();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi! I'm **MarineAI** — your AI assistant. I can answer questions about ocean conditions, vessel safety, routes, maritime regulations, or anything else you'd like to know. What's on your mind?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesRef = useRef<ChatMessage[]>(messages);
  messagesRef.current = messages;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = useCallback(async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    const userMsg: ChatMessage = { role: "user", content: msg, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = "44px";
    }

    try {
      const history = messagesRef.current
        .slice(-12)
        .map(m => ({ role: m.role, content: m.content }));

      const result = await chatApi.send({ message: msg, history, use_agents: true });

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          timestamp: new Date(),
          agents_used: result.agents_used,
        },
      ]);
    } catch {
      try {
        const fallback = await chatApi.quick(msg);
        setMessages(prev => [
          ...prev,
          { role: "assistant", content: fallback.answer, timestamp: new Date() },
        ]);
      } catch {
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            content: "I'm having trouble connecting to the backend right now. Please check that the server is running on port 2000.",
            timestamp: new Date(),
          },
        ]);
      }
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, loading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyMessage = (content: string, idx: number) => {
    navigator.clipboard.writeText(content);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const clearChat = () => {
    setMessages([{
      role: "assistant",
      content: "Hi! I'm **MarineAI** — your AI assistant. I can answer questions about ocean conditions, vessel safety, routes, maritime regulations, or anything else you'd like to know. What's on your mind?",
      timestamp: new Date(),
    }]);
  };

  return (
    <div
      className="h-full flex flex-col min-h-0"
      style={{
        background: "linear-gradient(180deg, #060f22 0%, #040d1c 100%)",
        borderLeft: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div
        className="shrink-0 flex items-center gap-3 px-4 py-3.5"
        style={{
          background: "rgba(10,20,40,0.8)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          backdropFilter: "blur(12px)",
        }}
      >
        {/* Avatar */}
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
          style={{
            background: "linear-gradient(135deg, #1a6ec2 0%, #7c3aed 100%)",
            boxShadow: "0 0 16px rgba(26,110,194,0.4)",
          }}
        >
          <Sparkles className="w-4 h-4 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-white leading-tight">MarineAI Assistant</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span
              className="w-1.5 h-1.5 rounded-full bg-emerald-400"
              style={{ boxShadow: "0 0 6px #10b981", animation: "pulse 2s infinite" }}
            />
            <span className="text-[10px] text-white/35 font-medium tracking-wide">
              Powered by Gemini AI
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={clearChat}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white/30 hover:text-white/70 hover:bg-white/[0.07] transition-all"
            title="Clear chat"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setChatOpen(false)}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white/30 hover:text-white/70 hover:bg-white/[0.07] transition-all"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── Messages ───────────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-5 space-y-5">
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            onCopy={() => copyMessage(msg.content, i)}
            copied={copiedIdx === i}
          />
        ))}

        {loading && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>

      {/* ── Input ──────────────────────────────────────────────────────── */}
      <div
        className="shrink-0 px-4 pt-3 pb-4"
        style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div
          className="flex gap-2 items-end rounded-2xl px-3 py-2.5"
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.09)",
            transition: "border-color 0.15s",
          }}
          onFocusCapture={e => (e.currentTarget.style.borderColor = "rgba(26,110,194,0.5)")}
          onBlurCapture={e => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.09)")}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything…"
            rows={1}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/25 resize-none outline-none leading-relaxed"
            style={{ minHeight: "22px", maxHeight: "120px", scrollbarWidth: "none" }}
            onInput={e => {
              const t = e.target as HTMLTextAreaElement;
              t.style.height = "auto";
              t.style.height = Math.min(t.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className={cn(
              "shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all",
              input.trim() && !loading
                ? "text-white"
                : "text-white/20 cursor-not-allowed"
            )}
            style={input.trim() && !loading ? {
              background: "linear-gradient(135deg, #1a6ec2, #7c3aed)",
              boxShadow: "0 0 12px rgba(26,110,194,0.4)",
            } : { background: "rgba(255,255,255,0.05)" }}
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-[10px] text-white/18 text-center mt-2 tracking-wide">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

// ─── Message bubble ───────────────────────────────────────────────────────────

function MessageBubble({
  message, onCopy, copied,
}: {
  message: ChatMessage;
  onCopy: () => void;
  copied: boolean;
}) {
  const isUser = message.role === "user";

  return (
    <div className={cn("group flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
        style={isUser ? {
          background: "rgba(26,110,194,0.3)",
          border: "1px solid rgba(26,110,194,0.4)",
        } : {
          background: "linear-gradient(135deg, #1a6ec2 0%, #7c3aed 100%)",
        }}
      >
        {isUser
          ? <User className="w-3.5 h-3.5 text-sky-300" />
          : <Sparkles className="w-3.5 h-3.5 text-white" />}
      </div>

      {/* Content */}
      <div className={cn("max-w-[85%] space-y-1", isUser && "items-end flex flex-col")}>
        <div
          className="relative px-4 py-3 rounded-2xl text-sm leading-relaxed"
          style={isUser ? {
            background: "linear-gradient(135deg, rgba(26,110,194,0.35), rgba(26,110,194,0.2))",
            border: "1px solid rgba(26,110,194,0.25)",
            color: "#e2e8f0",
            borderTopRightRadius: "4px",
          } : {
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.07)",
            color: "#cbd5e1",
            borderTopLeftRadius: "4px",
          }}
        >
          <FormattedMessage content={message.content} />

          {/* Copy button — show on hover for AI messages */}
          {!isUser && (
            <button
              onClick={onCopy}
              className="absolute top-2 right-2 w-6 h-6 rounded-md flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all text-white/30 hover:text-white/70 hover:bg-white/10"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          )}
        </div>

        {/* Agents used */}
        {message.agents_used && message.agents_used.length > 0 && !isUser && (
          <div className="flex flex-wrap gap-1 px-1">
            {message.agents_used.slice(0, 3).map(a => (
              <span
                key={a}
                className="text-[9px] px-1.5 py-0.5 rounded-full font-medium tracking-wide"
                style={{
                  background: "rgba(124,58,237,0.12)",
                  border: "1px solid rgba(124,58,237,0.2)",
                  color: "rgba(196,181,253,0.8)",
                }}
              >
                {a}
              </span>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className={cn(
          "text-[9px] px-1 tracking-wide",
          isUser ? "text-right" : "text-left"
        )}
          style={{ color: "rgba(255,255,255,0.18)" }}
        >
          {message.timestamp?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}

// ─── Formatted message renderer ──────────────────────────────────────────────

function FormattedMessage({ content }: { content: string }) {
  const lines = content.split("\n");
  let inCode = false;
  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    // Code block fence
    if (line.trim().startsWith("```")) {
      inCode = !inCode;
      return;
    }

    if (inCode) {
      elements.push(
        <code
          key={i}
          className="block text-xs font-mono px-3 py-1 rounded my-1"
          style={{
            background: "rgba(0,0,0,0.3)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "#93c5fd",
          }}
        >
          {line || "\u00A0"}
        </code>
      );
      return;
    }

    if (!line.trim()) {
      elements.push(<div key={i} className="h-1.5" />);
      return;
    }

    // Inline bold + italic
    const parse = (text: string): React.ReactNode => {
      const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
      return parts.map((p, j) => {
        if (p.startsWith("**") && p.endsWith("**"))
          return <strong key={j} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
        if (p.startsWith("*") && p.endsWith("*"))
          return <em key={j} className="text-sky-300">{p.slice(1, -1)}</em>;
        return p;
      });
    };

    // Horizontal rule
    if (line.trim() === "---") {
      elements.push(<hr key={i} className="my-2 border-white/10" />);
      return;
    }

    // Table row
    if (line.includes("|")) {
      const cells = line.split("|").filter(c => c.trim());
      const isSep = cells.every(c => /^[-: ]+$/.test(c));
      if (isSep) return;
      elements.push(
        <div key={i} className="flex gap-2 text-xs py-0.5 border-b border-white/[0.05]">
          {cells.map((c, j) => (
            <span key={j} className="flex-1 truncate" style={{ color: j === 0 ? "#94a3b8" : "#cbd5e1" }}>
              {parse(c.trim())}
            </span>
          ))}
        </div>
      );
      return;
    }

    // Heading (##)
    if (line.startsWith("## ")) {
      elements.push(
        <p key={i} className="text-sm font-bold text-white mt-2 mb-0.5">
          {parse(line.slice(3))}
        </p>
      );
      return;
    }

    // Bullet
    if (/^[-•*]\s/.test(line.trim())) {
      elements.push(
        <div key={i} className="flex gap-2 text-sm leading-relaxed pl-1">
          <span className="mt-1.5 w-1 h-1 rounded-full bg-ocean-400/60 shrink-0" />
          <span style={{ color: "#94a3b8" }}>{parse(line.trim().replace(/^[-•*]\s/, ""))}</span>
        </div>
      );
      return;
    }

    // Numbered list
    const numMatch = line.trim().match(/^(\d+)\.\s(.+)/);
    if (numMatch) {
      elements.push(
        <div key={i} className="flex gap-2 text-sm leading-relaxed pl-1">
          <span className="text-ocean-400/60 shrink-0 font-mono text-xs mt-0.5">{numMatch[1]}.</span>
          <span style={{ color: "#94a3b8" }}>{parse(numMatch[2])}</span>
        </div>
      );
      return;
    }

    elements.push(
      <p key={i} className="text-sm leading-relaxed" style={{ color: "#94a3b8" }}>
        {parse(line)}
      </p>
    );
  });

  return <div className="space-y-0.5">{elements}</div>;
}

// ─── Typing indicator ─────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div
        className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
        style={{ background: "linear-gradient(135deg, #1a6ec2, #7c3aed)" }}
      >
        <Sparkles className="w-3.5 h-3.5 text-white" />
      </div>
      <div
        className="px-4 py-3 rounded-2xl rounded-tl-[4px]"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.07)",
        }}
      >
        <div className="flex items-center gap-2">
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-ocean-400"
              style={{ animation: `blink 1.4s ${i * 0.2}s ease-in-out infinite` }}
            />
          ))}
          <span className="text-xs ml-1" style={{ color: "rgba(255,255,255,0.3)" }}>
            Thinking…
          </span>
        </div>
      </div>
    </div>
  );
}
