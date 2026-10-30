'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import {
  AlertCircle,
  BrainCircuit,
  Calculator,
  CheckCircle2,
  ChevronRight,
  FileText,
  Lightbulb,
  Package,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Truck,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Pill } from '@/components/ui/Pill'

export type AICategory = 'electricity' | 'transportation' | 'waste' | 'insights' | 'general'

export interface CalculationBreakdown {
  formula: string
  inputs: Record<string, string | number>
  assumptions?: string[]
  result: string
}

export interface MetricItem {
  label: string
  value: string | number
  unit?: string
  subtext?: string
  trend?: 'up' | 'down' | 'neutral'
}

export interface KeyFinding {
  title?: string
  description: string
  category?: string
}

export interface Recommendation {
  title: string
  explanation?: string
  priority?: 'High' | 'Medium' | 'Low' | string
  expected_benefit?: string
  impact?: string
  category?: string
  action_url?: string
  action_label?: string
}

export interface StructuredAIResponse {
  intent?: string
  direct_answer?: string
  summary?: string
  content?: string
  answer?: string
  response?: string
  explanation?: string
  reporting_period?: string
  metrics?: MetricItem[]
  key_findings?: KeyFinding[]
  recommendations?: Recommendation[]
  data_limitations?: string[]
  confidence_score?: string | number
  calculation_breakdown?: CalculationBreakdown
}

export interface AIResponseRendererProps {
  response?: string | StructuredAIResponse | any
  structuredPayload?: StructuredAIResponse | any
  category?: AICategory
  calculationBreakdown?: CalculationBreakdown
  timestamp?: string
  className?: string
  onActionClick?: (url: string) => void
}

/**
 * Safely renders inline markdown tokens (**bold**, *italic*, `code`) as React nodes
 * without using dangerouslySetInnerHTML.
 */
function renderInlineFormatted(text: string): React.ReactNode[] {
  if (!text) return []
  const parts: React.ReactNode[] = []
  const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`)/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index))
    }
    const token = match[0]
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={match.index} className="font-semibold text-[#1A2C1F]">
          {token.slice(2, -2)}
        </strong>
      )
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(
        <em key={match.index} className="italic text-[#374B3E]">
          {token.slice(1, -1)}
        </em>
      )
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={match.index}
          className="rounded bg-[#E7EFE4] px-1 py-0.5 font-mono text-[11px] text-[#285943]"
        >
          {token.slice(1, -1)}
        </code>
      )
    }
    lastIndex = regex.lastIndex
  }
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex))
  }
  return parts
}

/**
 * Parses markdown blocks (paragraphs, bullet lists, numbered lists, headings)
 * into structured, accessible React elements.
 */
function renderMarkdownBlocks(content: string): React.ReactNode {
  if (!content) return null

  const lines = content.split('\n')
  const blocks: React.ReactNode[] = []
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null

  const flushList = (index: number) => {
    if (!currentList) return
    if (currentList.type === 'ul') {
      blocks.push(
        <ul key={`ul-${index}`} className="my-2 space-y-1 pl-1">
          {currentList.items.map((it, i) => (
            <li key={i} className="flex items-start gap-2 text-xs sm:text-[13px] leading-relaxed text-[#2F4335]">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#285943]" />
              <span className="flex-1">{renderInlineFormatted(it)}</span>
            </li>
          ))}
        </ul>
      )
    } else {
      blocks.push(
        <ol key={`ol-${index}`} className="my-2 space-y-1 pl-1">
          {currentList.items.map((it, i) => (
            <li key={i} className="flex items-start gap-2 text-xs sm:text-[13px] leading-relaxed text-[#2F4335]">
              <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-[#E5F0E2] text-[10px] font-bold text-[#285943]">
                {i + 1}
              </span>
              <span className="flex-1">{renderInlineFormatted(it)}</span>
            </li>
          ))}
        </ol>
      )
    }
    currentList = null
  }

  lines.forEach((line, idx) => {
    const trimmed = line.trim()
    if (!trimmed) {
      flushList(idx)
      return
    }

    // Bullet list detection (- item, * item, • item)
    const bulletMatch = trimmed.match(/^[-*•]\s+(.*)$/)
    if (bulletMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList(idx)
        currentList = { type: 'ul', items: [] }
      }
      currentList.items.push(bulletMatch[1])
      return
    }

    // Numbered list detection (1. item, 2. item)
    const numberedMatch = trimmed.match(/^\d+[.)]\s+(.*)$/)
    if (numberedMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList(idx)
        currentList = { type: 'ol', items: [] }
      }
      currentList.items.push(numberedMatch[1])
      return
    }

    flushList(idx)

    // Headings (###, ##, #)
    if (trimmed.startsWith('### ')) {
      blocks.push(
        <h4 key={idx} className="mt-3 mb-1 text-xs sm:text-sm font-bold text-[#285943] tracking-tight">
          {renderInlineFormatted(trimmed.replace(/^###\s+/, ''))}
        </h4>
      )
      return
    }
    if (trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
      blocks.push(
        <h3 key={idx} className="mt-3.5 mb-1.5 text-sm sm:text-base font-bold text-[#203426] tracking-tight">
          {renderInlineFormatted(trimmed.replace(/^#+\s+/, ''))}
        </h3>
      )
      return
    }

    // Standard paragraph
    blocks.push(
      <p key={idx} className="my-1.5 text-xs sm:text-[13px] leading-relaxed text-[#2F4335] break-words">
        {renderInlineFormatted(trimmed)}
      </p>
    )
  })

  flushList(lines.length)
  return <div className="space-y-0.5">{blocks}</div>
}

/**
 * Attempts to repair and parse JSON strings with common LLM anomalies:
 * - Unescaped raw newlines/tabs inside string literals
 * - Trailing commas before closing braces/brackets
 * - Markdown fence wrapping
 * - Single quotes or escaped quote wrappers
 */
function safeJsonParse(input: string): any {
  let cleaned = input.trim()

  // 1. Strip markdown fences if present
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim()
  }

  // 2. If wrapped in outer quotes e.g. "{\"intent\":...}", unwrap one level
  if (cleaned.startsWith('"') && cleaned.endsWith('"') && cleaned.length > 2) {
    try {
      const unwrapped = JSON.parse(cleaned)
      if (typeof unwrapped === 'string') {
        cleaned = unwrapped.trim()
      } else if (typeof unwrapped === 'object') {
        return unwrapped
      }
    } catch {
      // ignore
    }
  }

  // 3. Extract outermost JSON object if surrounded by text
  const firstBrace = cleaned.indexOf('{')
  const lastBrace = cleaned.lastIndexOf('}')
  if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
    cleaned = cleaned.substring(firstBrace, lastBrace + 1)
  }

  // Direct parse attempt
  try {
    return JSON.parse(cleaned)
  } catch {
    // Continue to repair attempts
  }

  // 4. Remove trailing commas before } or ]
  let repaired = cleaned.replace(/,\s*([\]}])/g, '$1')

  try {
    return JSON.parse(repaired)
  } catch {
    // Continue
  }

  // 5. Replace unescaped control characters in string literals
  try {
    repaired = repaired.replace(/"((?:[^"\\]|\\.)*)"/g, (match) => {
      return match
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r')
        .replace(/\t/g, '\\t')
    })
    return JSON.parse(repaired)
  } catch {
    return null
  }
}

/**
 * Checks whether a string contains raw JSON syntax like {"intent": ...}
 */
function isJsonString(val: string): boolean {
  if (!val || typeof val !== 'string') return false
  const trimmed = val.trim()
  return (
    (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
    (trimmed.startsWith('[') && trimmed.endsWith(']')) ||
    (trimmed.startsWith('{') && (trimmed.includes('"direct_answer"') || trimmed.includes('"intent"') || trimmed.includes('"metrics"')))
  )
}

/**
 * Robust normalizer that handles all 6 input cases (Case A to F):
 * - Case A: Native JSON object
 * - Case B: JSON-encoded string
 * - Case C: Plain-text string
 * - Case D: Markdown-formatted text
 * - Case E: Malformed JSON with regex field extraction
 * - Case F: Wrapped response objects
 */
function normalizeAIResponse(
  response?: string | StructuredAIResponse | any,
  structuredPayload?: StructuredAIResponse | any
): {
  intent?: string
  direct_answer: string
  explanation?: string
  key_findings: KeyFinding[]
  recommendations: Recommendation[]
  metrics: MetricItem[]
  data_limitations: string[]
  reporting_period?: string
  confidence_score?: string | number
  calculation_breakdown?: CalculationBreakdown
} {
  const result: ReturnType<typeof normalizeAIResponse> = {
    direct_answer: '',
    key_findings: [],
    recommendations: [],
    metrics: [],
    data_limitations: [],
  }

  // Step 1: Unpack candidates from structuredPayload and response
  let rawCandidate: any = structuredPayload ?? response

  // Handle Case F: Unwrap wrapper objects
  if (rawCandidate && typeof rawCandidate === 'object') {
    if (rawCandidate.structured_payload) {
      rawCandidate = rawCandidate.structured_payload
    } else if (rawCandidate.structuredPayload) {
      rawCandidate = rawCandidate.structuredPayload
    } else if (rawCandidate.structured_report) {
      rawCandidate = rawCandidate.structured_report
    } else if (rawCandidate.data && typeof rawCandidate.data === 'object') {
      rawCandidate = rawCandidate.data
    }
  }

  // If candidate is a string or contains stringified JSON
  let parsedObj: any = null

  if (typeof rawCandidate === 'string') {
    parsedObj = safeJsonParse(rawCandidate)
    if (!parsedObj && isJsonString(rawCandidate)) {
      // Fallback regex extractor for malformed JSON (Case E)
      const directMatch = rawCandidate.match(/"(?:direct_answer|summary|answer|content)"\s*:\s*"((?:[^"\\]|\\.)*)"/)
      const explMatch = rawCandidate.match(/"explanation"\s*:\s*"((?:[^"\\]|\\.)*)"/)
      if (directMatch) {
        result.direct_answer = directMatch[1].replace(/\\"/g, '"').replace(/\\n/g, '\n').trim()
      }
      if (explMatch) {
        result.explanation = explMatch[1].replace(/\\"/g, '"').replace(/\\n/g, '\n').trim()
      }
      if (result.direct_answer) {
        return result
      }
    }
  } else if (rawCandidate && typeof rawCandidate === 'object') {
    parsedObj = rawCandidate
  }

  // If we have an object, populate fields
  if (parsedObj && typeof parsedObj === 'object') {
    result.intent = parsedObj.intent

    let rawDirect =
      parsedObj.direct_answer ||
      parsedObj.summary ||
      parsedObj.content ||
      parsedObj.answer ||
      parsedObj.response ||
      parsedObj.text ||
      ''

    // If direct_answer itself is a serialized JSON string, parse recursively
    if (typeof rawDirect === 'string' && isJsonString(rawDirect)) {
      const innerParsed = safeJsonParse(rawDirect)
      if (innerParsed && typeof innerParsed === 'object') {
        rawDirect = innerParsed.direct_answer || innerParsed.summary || innerParsed.content || innerParsed.answer || ''
        if (!result.explanation && innerParsed.explanation) {
          result.explanation = innerParsed.explanation
        }
        if (result.metrics.length === 0 && Array.isArray(innerParsed.metrics)) {
          parsedObj.metrics = innerParsed.metrics
        }
        if (result.key_findings.length === 0 && Array.isArray(innerParsed.key_findings)) {
          parsedObj.key_findings = innerParsed.key_findings
        }
        if (result.recommendations.length === 0 && Array.isArray(innerParsed.recommendations)) {
          parsedObj.recommendations = innerParsed.recommendations
        }
      } else {
        // Regex extraction from inner string
        const innerMatch = rawDirect.match(/"(?:direct_answer|summary)"\s*:\s*"((?:[^"\\]|\\.)*)"/)
        if (innerMatch) {
          rawDirect = innerMatch[1].replace(/\\"/g, '"').replace(/\\n/g, '\n').trim()
        }
      }
    }

    result.direct_answer = typeof rawDirect === 'string' ? rawDirect.trim() : ''
    result.explanation = typeof parsedObj.explanation === 'string' ? parsedObj.explanation.trim() : undefined
    result.reporting_period = parsedObj.reporting_period || parsedObj.reportingPeriod
    result.confidence_score = parsedObj.confidence_score || parsedObj.confidenceScore
    result.calculation_breakdown = parsedObj.calculation_breakdown || parsedObj.calculationBreakdown

    if (Array.isArray(parsedObj.metrics)) {
      result.metrics = parsedObj.metrics
        .filter((m: any) => m && (m.label || m.name) && m.value !== undefined && m.value !== null)
        .map((m: any) => ({
          label: String(m.label || m.name),
          value: m.value,
          unit: m.unit ? String(m.unit) : undefined,
          subtext: m.subtext || m.note ? String(m.subtext || m.note) : undefined,
          trend: m.trend,
        }))
    }

    if (Array.isArray(parsedObj.key_findings)) {
      result.key_findings = parsedObj.key_findings
        .filter((kf: any) => kf && (kf.title || kf.description))
        .map((kf: any) => ({
          title: kf.title ? String(kf.title) : undefined,
          description: String(kf.description || kf.finding || ''),
          category: kf.category ? String(kf.category) : undefined,
        }))
    }

    if (Array.isArray(parsedObj.recommendations)) {
      result.recommendations = parsedObj.recommendations
        .filter((rec: any) => rec && (rec.title || rec.explanation || rec.description))
        .map((rec: any) => ({
          title: String(rec.title || 'Recommended Action'),
          explanation: String(rec.explanation || rec.description || rec.text || ''),
          expected_benefit: rec.expected_benefit || rec.benefit || rec.impact ? String(rec.expected_benefit || rec.benefit || rec.impact) : undefined,
          priority: rec.priority ? String(rec.priority) : 'Medium',
          category: rec.category ? String(rec.category) : undefined,
          action_url: rec.action_url || rec.actionUrl,
          action_label: rec.action_label || rec.actionLabel,
        }))
    }

    if (Array.isArray(parsedObj.data_limitations)) {
      result.data_limitations = parsedObj.data_limitations.map(String).filter(Boolean)
    }

    // If direct_answer was resolved and is not raw JSON, return
    if (result.direct_answer && !result.direct_answer.startsWith('{')) {
      return result
    }
  }

  // Step 2: Handle raw text / markdown string (Case C and Case D)
  const textRaw = typeof response === 'string' ? response.trim() : typeof rawCandidate === 'string' ? rawCandidate.trim() : ''

  if (textRaw && !isJsonString(textRaw)) {
    result.direct_answer = textRaw
    return result
  }

  // Step 3: Last defense: If direct_answer still contains JSON syntax like `{"intent":...}`
  if (result.direct_answer && result.direct_answer.startsWith('{')) {
    const daMatch = result.direct_answer.match(/"(?:direct_answer|summary|content)"\s*:\s*"((?:[^"\\]|\\.)*)"/)
    if (daMatch) {
      result.direct_answer = daMatch[1].replace(/\\"/g, '"').replace(/\\n/g, '\n').trim()
    } else {
      // Clean leading and trailing brackets and keys
      result.direct_answer = result.direct_answer
        .replace(/^[{\s]+/, '')
        .replace(/[}\s]+$/, '')
        .replace(/^"[^"]+"\s*:\s*"?/, '')
        .replace(/"?$/, '')
        .replace(/\\"/g, '"')
        .trim()
    }
  }

  return result
}

/**
 * Premium, category-aware, responsive AI Sustainability Response Renderer.
 * Adheres strictly to the 4 Core Quality Criteria:
 * 1. Analytical Rigor: Direct answers first without conversational fluff.
 * 2. Data Integrity: Displays verified metrics with clear labels and units.
 * 3. Presentation Standards: Clean typography, rounded cards, no raw JSON or empty sections.
 * 4. Actionability: Meaningful next steps with clear priorities and action triggers.
 */
export function AIResponseRenderer({
  response,
  structuredPayload,
  category = 'general',
  calculationBreakdown,
  timestamp,
  className = '',
  onActionClick,
}: AIResponseRendererProps) {
  const router = useRouter()

  // Memoized normalizer: parses structured response only when response or payload identity changes
  const parsed = React.useMemo(
    () => normalizeAIResponse(response, structuredPayload),
    [response, structuredPayload]
  )
  const effectiveCalculation = calculationBreakdown || parsed.calculation_breakdown

  const handleAction = (url: string) => {
    if (onActionClick) {
      onActionClick(url)
    } else if (url.startsWith('/')) {
      router.push(url)
    }
  }

  // Category Configuration
  const categoryConfig = {
    electricity: {
      icon: Zap,
      label: 'Energy & Emissions Advisory',
      subtitle: 'Kilowatt-hour trends, tariff costs, and CEA grid factor analysis',
      badge: 'Scope 2 Energy',
    },
    transportation: {
      icon: Truck,
      label: 'Transportation AI Assistant',
      subtitle: 'Fleet mileage, passenger occupancy, and fuel efficiency analysis',
      badge: 'Scope 1 Fleet',
    },
    waste: {
      icon: Package,
      label: 'Waste Management AI Assistant',
      subtitle: 'Material diversion, recycling rates, and IPCC circular avoidance',
      badge: 'Circular Diversion',
    },
    insights: {
      icon: BrainCircuit,
      label: 'Interactive Sustainability Analyst',
      subtitle: 'Cross-category carbon accounting synthesis and prioritized decarbonization',
      badge: 'Enterprise Analyst',
    },
    general: {
      icon: Sparkles,
      label: 'Sustainability Advisory',
      subtitle: 'Data-grounded intelligence based on active workspace records',
      badge: 'Data Grounded',
    },
  }[category]

  const CategoryIcon = categoryConfig.icon

  // Check if response has content to display
  const hasContent = Boolean(
    parsed.direct_answer ||
      parsed.key_findings.length > 0 ||
      parsed.recommendations.length > 0 ||
      parsed.metrics.length > 0 ||
      parsed.explanation ||
      effectiveCalculation
  )

  // Empty / Graceful Fallback State
  if (!hasContent) {
    return (
      <div className={`rounded-2xl border border-[#D8E6D5] bg-[#F7FAF5] p-5 text-center ${className}`}>
        <p className="text-xs text-[#5D7062]">
          Evaluating your workspace records. Ask any question regarding consumption, factors, or reduction scenarios.
        </p>
      </div>
    )
  }

  // Intent pill label
  const intentPillLabel = {
    direct: 'Direct Fact',
    comparative: 'Comparative Analysis',
    recommendation: 'Decarbonization Priority',
    analytical: 'Analytical Observation',
    comprehensive: 'Executive Synthesis',
  }[parsed.intent || '']

  // Ensure explanation is distinct from direct_answer
  const hasDistinctExplanation = Boolean(
    parsed.explanation &&
      parsed.explanation.trim() !== parsed.direct_answer.trim() &&
      !parsed.direct_answer.includes(parsed.explanation)
  )

  return (
    <div
      className={`rounded-2xl border border-[#CDE0CC] bg-gradient-to-br from-[#FAFCF8] via-[#F4F9F2] to-[#EEF5EB] p-4.5 sm:p-5.5 text-[#28352D] shadow-xs animate-in fade-in duration-200 ${className}`}
    >
      {/* 1. Header Bar: Category Branded & Clear Metadata */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-[#D8E6D5] pb-3 mb-3.5 gap-2">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#285943] text-white shadow-2xs">
            <CategoryIcon size={16} />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-[#285943] tracking-tight">
                {categoryConfig.label}
              </h3>
              <Pill tone="green">{categoryConfig.badge}</Pill>
              {intentPillLabel && (
                <span className="rounded-full bg-[#EAF2E7] px-2 py-0.5 text-[10px] font-medium text-[#385241] border border-[#D0E2CD]">
                  {intentPillLabel}
                </span>
              )}
            </div>
            <p className="text-[11px] text-[#5A7061]">{categoryConfig.subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          {parsed.reporting_period && (
            <span className="rounded-full bg-white/80 px-2.5 py-0.5 text-[10px] font-semibold text-[#324538] border border-[#D5E3D3]">
              Period: {parsed.reporting_period}
            </span>
          )}
          {parsed.confidence_score && (
            <span className="rounded-full bg-[#E3EFE0] px-2.5 py-0.5 text-[10px] font-semibold text-[#285943] border border-[#BFD9BA]">
              Confidence: {parsed.confidence_score}
            </span>
          )}
          {timestamp && <span className="text-[10px] text-[#7E9182]">{timestamp}</span>}
        </div>
      </div>

      {/* 2. Primary Element: Direct Answer / Executive Insight */}
      {parsed.direct_answer && (
        <div className="rounded-xl border border-[#D5E4D3] bg-white/95 p-3.5 sm:p-4 shadow-2xs">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#285943] mb-1.5">
            <Sparkles size={13} />
            <span>Key Insight</span>
          </div>
          <div className="text-xs sm:text-[13px] leading-relaxed text-[#203325]">
            {renderMarkdownBlocks(parsed.direct_answer)}
          </div>
        </div>
      )}

      {/* 3. Verified Activity Metrics (Compact Cards) */}
      {parsed.metrics.length > 0 && (
        <div className="mt-3.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[#4E6454] mb-2 flex items-center gap-1.5">
            <CheckCircle2 size={13} className="text-[#285943]" />
            <span>Verified Activity Metrics</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {parsed.metrics.map((m, idx) => {
              const valStr = String(m.value)
              const isNegativeOffset = valStr.includes('-')
              return (
                <div
                  key={`metric-${idx}`}
                  className="rounded-xl border border-[#D8E6D6] bg-white/90 p-3 shadow-2xs flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between text-[11px] text-[#637768]">
                    <span className="font-medium truncate">{m.label}</span>
                    {m.trend === 'up' ? (
                      <TrendingUp size={13} className="text-[#B94726] shrink-0" />
                    ) : m.trend === 'down' ? (
                      <TrendingDown size={13} className="text-[#285943] shrink-0" />
                    ) : null}
                  </div>

                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span
                      className={`text-lg font-bold tracking-tight ${
                        isNegativeOffset ? 'text-[#1F5438]' : 'text-[#285943]'
                      }`}
                    >
                      {typeof m.value === 'number' ? m.value.toLocaleString() : m.value}
                    </span>
                    {m.unit && <span className="text-xs font-normal text-[#607366]">{m.unit}</span>}
                  </div>

                  {m.subtext && <p className="mt-1 text-[10px] text-[#819286] leading-tight">{m.subtext}</p>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 4. Supporting Analysis / Why This Matters */}
      {hasDistinctExplanation && (
        <div className="mt-3.5 rounded-xl border border-[#D8E6D5] bg-white/85 p-3.5 text-xs text-[#354A3B] shadow-2xs">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#285943] mb-1.5">
            <FileText size={13} />
            <span>Analysis & Methodology</span>
          </div>
          <div className="leading-relaxed text-[#2C4132] space-y-1">
            {renderMarkdownBlocks(parsed.explanation!)}
          </div>
        </div>
      )}

      {/* 5. Deterministic Assurance & Calculation Engine Proof */}
      {effectiveCalculation && (
        <div className="mt-3.5 rounded-xl border border-[#D9E5D7] bg-[#F7FAF5] p-3.5 text-xs text-[#455A4C]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-semibold text-[#285943]">
              <Calculator size={14} />
              <span>Assurance & Calculation Proof</span>
            </div>
            <span className="rounded bg-[#EAF2E7] px-2 py-0.5 text-[10px] font-medium text-[#285943]">
              Deterministic Calculation
            </span>
          </div>

          <div className="mt-2.5 space-y-1.5 font-mono text-[11px]">
            <div className="rounded-lg bg-white/80 p-2 border border-[#E3ECE0]">
              <span className="font-semibold text-[#304435] font-sans">Formula: </span>
              <span className="text-[#4E6455]">{effectiveCalculation.formula}</span>
            </div>

            {Object.keys(effectiveCalculation.inputs || {}).length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                {Object.entries(effectiveCalculation.inputs).map(([k, v]) => (
                  <div key={k} className="flex justify-between rounded bg-white/60 px-2 py-1 border border-[#E8EFE5]">
                    <span className="text-[#6C7E71] font-sans text-[10px] truncate">{k}:</span>
                    <span className="font-semibold text-[#28352D] text-[11px]">{String(v)}</span>
                  </div>
                ))}
              </div>
            )}

            {effectiveCalculation.result && (
              <div className="rounded-lg bg-[#EBF4E8] p-2 border border-[#CFE1CC] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                <span className="font-sans font-bold text-[#285943]">Calculated Result:</span>
                <span className="font-bold text-[#1F5438]">{effectiveCalculation.result}</span>
              </div>
            )}
          </div>

          {effectiveCalculation.assumptions && effectiveCalculation.assumptions.length > 0 && (
            <div className="mt-2 pt-2 border-t border-[#E5EFE2] text-[10px] text-[#718577]">
              <span className="font-semibold text-[#485C4F]">Model Assumptions:</span>
              <ul className="mt-0.5 list-disc pl-4 space-y-0.5">
                {effectiveCalculation.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 6. Key Analytical Observations */}
      {parsed.key_findings.length > 0 && (
        <div className="mt-3.5 pt-3 border-t border-[#DDE7DA]">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[#4E6454] mb-2 flex items-center gap-1.5">
            <FileText size={13} className="text-[#285943]" />
            <span>Key Analytical Observations</span>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {parsed.key_findings.map((kf, i) => (
              <div
                key={`finding-${i}`}
                className="rounded-xl border border-[#D5E3D3] bg-white/90 p-3 text-xs shadow-2xs"
              >
                <div className="font-semibold text-[#28352D] flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#285943]" />
                  <span>{kf.title || `Observation ${i + 1}`}</span>
                  {kf.category && (
                    <span className="ml-auto rounded bg-[#EDF4EB] px-1.5 py-0.5 text-[9px] font-medium text-[#445849]">
                      {kf.category}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[#4F6354] leading-relaxed break-words">{kf.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Actionable Decarbonization Priorities */}
      {parsed.recommendations.length > 0 && (
        <div className="mt-3.5 pt-3 border-t border-[#DDE7DA]">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[#4E6454] mb-2 flex items-center gap-1.5">
            <Lightbulb size={13} className="text-[#285943]" />
            <span>Actionable Decarbonization Priorities</span>
          </div>

          <div className="space-y-2">
            {parsed.recommendations.map((rec, i) => {
              const isHigh = rec.priority?.toLowerCase() === 'high'
              return (
                <div
                  key={`rec-${i}`}
                  className="rounded-xl border border-[#D2E2D0] bg-white/95 p-3 text-xs shadow-2xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5"
                >
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#28352D]">{rec.title}</span>
                      {rec.priority && (
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                            isHigh
                              ? 'bg-[#F9ECE7] text-[#A63C1E] border border-[#F0D0C7]'
                              : 'bg-[#EBF3E8] text-[#285943] border border-[#CFDFCC]'
                          }`}
                        >
                          {rec.priority} Priority
                        </span>
                      )}
                      {rec.category && (
                        <span className="rounded bg-[#F2F6F0] px-1.5 py-0.5 text-[10px] font-medium text-[#5E7264]">
                          {rec.category}
                        </span>
                      )}
                    </div>

                    {rec.explanation && (
                      <p className="text-[#4F6354] leading-relaxed break-words mt-0.5">{rec.explanation}</p>
                    )}

                    {(rec.expected_benefit || rec.impact) && (
                      <p className="text-[11px] font-medium text-[#285943] flex items-center gap-1 mt-1">
                        <TrendingDown size={12} className="text-[#285943]" />
                        <span>Expected Impact: {rec.expected_benefit || rec.impact}</span>
                      </p>
                    )}
                  </div>

                  {rec.action_url && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleAction(rec.action_url!)}
                      className="shrink-0 text-xs self-start sm:self-center bg-[#F2F7F0] hover:bg-[#E3EFE0] text-[#285943] border-[#CFDFCC] cursor-pointer"
                    >
                      <span>{rec.action_label || 'View Action'}</span>
                      <ChevronRight size={12} className="ml-1" />
                    </Button>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 8. Data Boundary / Limitations */}
      {parsed.data_limitations.length > 0 && (
        <div className="mt-3 rounded-xl border border-[#E7DFCC] bg-[#FDFCF8] p-2.5 text-[11px] text-[#69614C] flex items-start gap-2">
          <AlertCircle size={14} className="shrink-0 text-[#9C8230] mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold text-[#544D3B]">Data Boundary Note: </span>
            <span>{parsed.data_limitations.join(' ')}</span>
          </div>
        </div>
      )}
    </div>
  )
}
