'use client'

import React, { useState } from 'react'
import {
  ArrowRight,
  BrainCircuit,
  Calculator,
  RotateCcw,
  Sparkles,
  User,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Pill } from '@/components/ui/Pill'
import { AIResponseRenderer, type AICategory } from '@/components/ai/AIResponseRenderer'
import type { AiChatMessage } from '@/types/sustainability'

export interface ModuleAiAdvisorProps {
  title: string
  subtitle: string
  badgeText?: string
  suggestedQuestions?: string[]
  onQuery: (question: string) => Promise<AiChatMessage>
  emptyStateDescription?: string
  category?: AICategory
}

export function ModuleAiAdvisor({
  title,
  subtitle,
  badgeText = 'DATA-GROUNDED ADVISOR',
  suggestedQuestions = [],
  onQuery,
  emptyStateDescription,
  category,
}: ModuleAiAdvisorProps) {
  const [messages, setMessages] = useState<AiChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  const resolvedCategory: AICategory =
    category ||
    (title.toLowerCase().includes('elec')
      ? 'electricity'
      : title.toLowerCase().includes('transport') || title.toLowerCase().includes('fleet')
      ? 'transportation'
      : title.toLowerCase().includes('waste')
      ? 'waste'
      : 'general')

  const handleAsk = async (question: string) => {
    const q = question.trim()
    if (!q || isProcessing) return

    const userMsg: AiChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsProcessing(true)

    try {
      const response = await onQuery(q)
      setMessages((prev) => [...prev, response])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: 'An error occurred while evaluating your workspace data. Please try another query.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleClear = () => {
    setMessages([])
  }

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#EDF1EB] pb-5">
        <div className="flex items-center gap-3.5">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-[#285943] text-white shadow-xs">
            <BrainCircuit size={20} />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold tracking-[-0.03em] text-[#2F4436]">{title}</h2>
              <Pill tone="green">{badgeText}</Pill>
            </div>
            <p className="mt-1 text-xs text-[#8A978D]">{subtitle}</p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            type="button"
            onClick={handleClear}
            className="flex items-center gap-1.5 self-start sm:self-auto rounded-lg px-2.5 py-1.5 text-xs text-[#7A887D] hover:bg-[#F2F6F0] hover:text-[#285943] cursor-pointer"
          >
            <RotateCcw size={13} />
            <span>Clear conversation</span>
          </button>
        )}
      </div>

      {/* Conversation Thread */}
      <div className="mt-6 rounded-2xl border border-[#E3EAE1] bg-[#FAFCF8] p-4 sm:p-5">
        {messages.length === 0 ? (
          <div className="py-8 text-center">
            <span className="mx-auto grid h-10 w-10 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
              <Sparkles size={18} />
            </span>
            <p className="mt-3 text-sm font-semibold text-[#3D5245]">
              Ask questions grounded in your actual data
            </p>
            <p className="mx-auto mt-1 max-w-[500px] text-xs leading-5 text-[#829286]">
              {emptyStateDescription ||
                'Type your question below. The advisor evaluates your active records and applies verified calculation functions to provide grounded insights.'}
            </p>
            {suggestedQuestions && suggestedQuestions.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-2 justify-center max-w-xl mx-auto">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={isProcessing}
                    onClick={() => handleAsk(q)}
                    className="rounded-full border border-[#D5E4D3] bg-white px-3 py-1.5 text-[11px] font-medium text-[#285943] hover:bg-[#EAF2E7] hover:border-[#285943] transition-colors disabled:opacity-50 cursor-pointer shadow-2xs"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4 max-h-[520px] overflow-y-auto pr-1">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' ? (
                  <div className="w-full max-w-[98%] sm:max-w-[94%]">
                    <AIResponseRenderer
                      response={msg.content}
                      structuredPayload={msg.structuredPayload}
                      category={resolvedCategory}
                      calculationBreakdown={msg.calculationBreakdown}
                      timestamp={msg.timestamp}
                    />
                  </div>
                ) : (
                  <>
                    <div className="max-w-[80%] rounded-2xl rounded-tr-xs bg-[#285943] px-4 py-3 text-xs sm:text-[13px] leading-relaxed text-white font-medium shadow-2xs">
                      <div className="whitespace-pre-line">{msg.content}</div>
                      <p className="mt-1 text-[10px] text-white/70 text-right">{msg.timestamp}</p>
                    </div>
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#DDEBDD] text-[#285943]">
                      <User size={15} />
                    </span>
                  </>
                )}
              </div>
            ))}

            {isProcessing && (
              <div className="flex gap-3 items-center text-xs text-[#7A8B7E] italic py-2">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#285943] text-white">
                  <BrainCircuit size={15} className="animate-spin" />
                </span>
                <span>Calculating response from your workspace records…</span>
              </div>
            )}
          </div>
        )}

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleAsk(input)
          }}
          className="mt-4 flex gap-2 border-t border-[#E8EFE6] pt-4"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask ${title} a question about your data...`}
            disabled={isProcessing}
            className="flex-1 rounded-xl border border-[#DCE4DA] bg-white px-3.5 py-2.5 text-xs text-[#28352D] placeholder-[#9AA59C] outline-none focus:border-[#285943] focus:ring-1 focus:ring-[#285943]"
          />
          <button
            type="submit"
            disabled={!input.trim() || isProcessing}
            className="flex items-center gap-1.5 rounded-xl bg-[#285943] px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-colors hover:bg-[#1F4635] disabled:opacity-50 cursor-pointer"
          >
            <span>Ask</span>
            <ArrowRight size={14} />
          </button>
        </form>
      </div>
    </Card>
  )
}
