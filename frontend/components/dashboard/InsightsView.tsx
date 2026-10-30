'use client'

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  AlertCircle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Compass,
  FileText,
  Lightbulb,
  Loader2,
  Package,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Truck,
  Zap,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { PageTitle } from '@/components/ui/PageTitle'
import { Pill } from '@/components/ui/Pill'
import { AIResponseRenderer } from '@/components/ai/AIResponseRenderer'
import { useAuth } from '@/context/auth-context'
import { apiClient } from '@/services/api-client'

interface StructuredCategory {
  name: string
  emissions_kg: number
  record_count?: number
  percentage_of_gross?: number
  percentage_of_net?: number
  status: 'positive' | 'negative_credit' | 'zero'
  note?: string
}

interface LargestSource {
  category: string
  emissions_kg: number
  percentage_of_gross: number
  percentage_of_net_total?: number
  record_count: number
}

interface KeyFinding {
  title: string
  description: string
  category?: string
}

interface Recommendation {
  title: string
  explanation: string
  expected_benefit: string
  priority: 'High' | 'Medium' | 'Low'
  category: string
  action_url?: string
  action_label?: string
}

interface SustainabilityReport {
  status: string
  title: string
  summary: string
  reporting_period?: string
  total_net_emissions_kg: number
  total_gross_emissions_kg: number
  total_records_analyzed: number
  largest_source?: LargestSource
  categories: StructuredCategory[]
  key_findings: KeyFinding[]
  recommendations: Recommendation[]
  data_limitations?: string[]
}

interface InsightsApiResponse {
  id: string
  role: string
  content: string
  timestamp: string
  calculation_breakdown?: any
  structured_report?: SustainabilityReport
  structured_payload?: any
}

function formatSummaryText(summary?: string): string {
  if (!summary) return ''
  const trimmed = summary.trim()
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const parsed = JSON.parse(trimmed)
      return parsed.summary || parsed.direct_answer || parsed.explanation || trimmed
    } catch {
      const match =
        trimmed.match(/"summary"\s*:\s*"((?:[^"\\]|\\.)*)"/) ||
        trimmed.match(/"direct_answer"\s*:\s*"((?:[^"\\]|\\.)*)"/)
      if (match) return match[1].replace(/\\"/g, '"').replace(/\\n/g, '\n')
    }
  }
  return summary
}

export function InsightsView() {
  const router = useRouter()
  const { session, token } = useAuth()
  const isAuth = Boolean(session.isAuthenticated && token)

  const [report, setReport] = useState<SustainabilityReport | null>(null)
  const [question, setQuestion] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [chatAnswer, setChatAnswer] = useState<string | null>(null)
  const [chatPayload, setChatPayload] = useState<any | null>(null)

  const fetchInsightsReport = useCallback(async (query: string = 'Executive portfolio summary') => {
    if (!isAuth || !token) {
      setIsInitialLoading(false)
      return
    }
    setErrorMessage(null)
    try {
      const res = await apiClient.post<InsightsApiResponse>(
        '/ai/insights',
        { question: query },
        { token }
      )
      if (res && res.structured_report) {
        setReport(res.structured_report)
      } else if (res && res.content) {
        // If content returned without structured report (e.g. empty records)
        if (res.content.toLowerCase().includes('no records available')) {
          setReport(null)
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Unable to generate sustainability report. Please verify your connection.')
    } finally {
      setIsInitialLoading(false)
      setIsLoading(false)
    }
  }, [isAuth, token])

  const hasLoadedRef = useRef(false)
  useEffect(() => {
    if (isAuth && !hasLoadedRef.current) {
      hasLoadedRef.current = true
      fetchInsightsReport()
    } else if (!isAuth) {
      hasLoadedRef.current = false
      setIsInitialLoading(false)
      setReport(null)
    }
  }, [isAuth, fetchInsightsReport])

  const handleAskCustomQuestion = async (q: string) => {
    const trimmed = q.trim()
    if (!trimmed || isLoading) return
    setIsLoading(true)
    setQuestion('')
    setErrorMessage(null)
    try {
      const res = await apiClient.post<InsightsApiResponse>(
        '/ai/insights',
        { question: trimmed },
        { token: token || undefined }
      )
      if (res && res.structured_report) {
        setReport(res.structured_report)
      }
      if (res && res.structured_payload) {
        setChatPayload(res.structured_payload)
      }
      if (res && res.content) {
        setChatAnswer(res.content)
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Error evaluating inquiry with Groq AI.')
    } finally {
      setIsLoading(false)
    }
  }

  // Memoize chart data to avoid recalculation on unrelated re-renders
  const chartData = useMemo(
    () =>
      (report?.categories || []).map((cat) => ({
        name: cat.name,
        emissions_kg: cat.emissions_kg,
        status: cat.status,
      })),
    [report?.categories]
  )

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageTitle
        eyebrow="ENTERPRISE SUSTAINABILITY SUITE"
        title="AI Insights & Analytics Report"
        description="Verified carbon accounting synthesis and grounded decarbonization priorities powered by Groq."
        action={
          <div className="flex items-center gap-2">
            <Pill tone={isAuth ? 'green' : 'amber'}>{isAuth ? 'Verified Workspace' : 'Demo View'}</Pill>
            {report && (
              <Button
                variant="secondary"
                onClick={() => fetchInsightsReport()}
                className="h-8 px-2.5 text-xs text-[#4E6153]"
              >
                <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
                Refresh
              </Button>
            )}
          </div>
        }
      />

      {/* Loading Skeleton */}
      {isInitialLoading && (
        <div className="space-y-5 animate-pulse">
          <div className="h-44 rounded-2xl bg-[#EEF3EC] border border-[#DEE7DC]" />
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="h-36 rounded-xl bg-[#EEF3EC]" />
            <div className="h-36 rounded-xl bg-[#EEF3EC]" />
            <div className="h-36 rounded-xl bg-[#EEF3EC]" />
          </div>
          <div className="h-64 rounded-2xl bg-[#EEF3EC]" />
        </div>
      )}

      {/* Error / AI Configuration Banner */}
      {!isInitialLoading && errorMessage && (
        <Card className="border-[#F1CDCD] bg-[#FFF8F8] p-5">
          <div className="flex items-start gap-3">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#E53E3E] text-white">
              <AlertCircle size={17} />
            </span>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-[#9B2C2C]">AI Insights Service Notice</h3>
              <p className="mt-1 text-xs leading-5 text-[#C53030]">{errorMessage}</p>
              <div className="mt-3 flex items-center gap-2">
                <Button
                  variant="secondary"
                  onClick={() => fetchInsightsReport()}
                  className="h-7 px-3 text-[11px]"
                >
                  Retry Request
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Empty State: No Workspace Records */}
      {!isInitialLoading && !errorMessage && !report && (
        <Card className="p-10 text-center border-dashed border-[#CFDCD0] bg-[#FAFDF8]">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#E7F1E5] text-[#285943]">
            <Sparkles size={22} />
          </span>
          <h2 className="mt-4 text-base font-semibold text-[#28352D]">Awaiting Workspace Emissions Data</h2>
          <p className="mx-auto mt-1.5 max-w-md text-xs leading-5 text-[#6D8072]">
            To generate a comprehensive sustainability analytics report, add records in Electricity,
            Transportation, or Waste. The AI analyst synthesizes your real activity logs without fabricating numbers.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2.5">
            <Button onClick={() => router.push('/dashboard/electricity')} className="text-xs bg-[#285943]">
              <Zap size={14} /> Add Electricity Log
            </Button>
            <Button onClick={() => router.push('/dashboard/transportation')} variant="secondary" className="text-xs">
              <Truck size={14} /> Add Travel Log
            </Button>
            <Button onClick={() => router.push('/dashboard/waste')} variant="secondary" className="text-xs">
              <Package size={14} /> Record Waste Stream
            </Button>
          </div>
        </Card>
      )}

      {/* Structured Sustainability Analytics Report */}
      {!isInitialLoading && report && (
        <div className="space-y-6">
          {/* SECTION A: Executive Summary Banner */}
          <Card className="overflow-hidden border-[#D3E0D1] bg-gradient-to-br from-[#FAFDF9] via-[#F5F9F3] to-[#EEF5EB] p-6 sm:p-7 shadow-xs">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="max-w-2xl space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#285943] text-white">
                    <FileText size={16} />
                  </span>
                  <h2 className="text-lg font-bold tracking-tight text-[#203226]">
                    Your Carbon Footprint Analysis
                  </h2>
                  <Pill tone="green">
                    {report.reporting_period || 'Active Period'}
                  </Pill>
                </div>
                <p className="text-xs leading-6 text-[#4A5E4F] sm:text-sm">
                  {formatSummaryText(report.summary)}
                </p>
                <div className="pt-1 flex items-center gap-3 text-[11px] text-[#7A8C7F]">
                  <span>Scope: Operational Activities</span>
                  <span>•</span>
                  <span>{report.total_records_analyzed} verified activity entries analyzed</span>
                </div>
              </div>

              {/* KPI Badges */}
              <div className="flex flex-wrap gap-3 self-start lg:self-auto">
                <div className="rounded-xl border border-[#D5E3D3] bg-white/80 p-3.5 shadow-2xs backdrop-blur-xs min-w-[150px]">
                  <p className="text-[10px] font-semibold uppercase tracking-[.12em] text-[#7C8E81]">
                    Net Portfolio Total
                  </p>
                  <p className="mt-1 text-2xl font-bold tracking-tight text-[#285943]">
                    {report.total_net_emissions_kg.toLocaleString()}
                    <span className="ml-1 text-xs font-normal text-[#6B7D70]">kg CO₂e</span>
                  </p>
                  <p className="mt-0.5 text-[10px] text-[#849588]">Inclusive of diversion offsets</p>
                </div>

                <div className="rounded-xl border border-[#D5E3D3] bg-white/80 p-3.5 shadow-2xs backdrop-blur-xs min-w-[150px]">
                  <p className="text-[10px] font-semibold uppercase tracking-[.12em] text-[#7C8E81]">
                    Gross Positive Footprint
                  </p>
                  <p className="mt-1 text-2xl font-bold tracking-tight text-[#3E5345]">
                    {report.total_gross_emissions_kg.toLocaleString()}
                    <span className="ml-1 text-xs font-normal text-[#6B7D70]">kg CO₂e</span>
                  </p>
                  <p className="mt-0.5 text-[10px] text-[#849588]">Total active emission streams</p>
                </div>
              </div>
            </div>
          </Card>

          {/* SECTION B: Largest Emission Source Highlight */}
          {report.largest_source && (
            <Card className="border-[#9FC298] bg-[#F9FBF8] p-5 sm:p-6 shadow-xs">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-[.14em] text-[#3D714C] bg-[#E5EFE2] px-2 py-0.5 rounded-md">
                      Largest Emission Source
                    </span>
                    <span className="text-xs text-[#7A8C80]">Primary Abatement Target</span>
                  </div>
                  <h3 className="mt-2 text-xl font-bold text-[#28352D]">
                    {report.largest_source.category}
                  </h3>
                  <p className="mt-1 text-xs text-[#596E60]">
                    Accounts for <strong className="text-[#285943]">{report.largest_source.percentage_of_gross}%</strong> of
                    gross positive operational emissions
                    {report.largest_source.percentage_of_net_total !== undefined && (
                      <span> ({report.largest_source.percentage_of_net_total}% of net portfolio total)</span>
                    )} across {report.largest_source.record_count} recorded log(s).
                  </p>
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold tracking-tight text-[#285943]">
                    {report.largest_source.emissions_kg.toLocaleString()}
                  </span>
                  <span className="text-xs font-medium text-[#7A8D80]">kg CO₂e</span>
                </div>
              </div>

              {/* Explicit Denominator Progress Bar */}
              <div className="mt-4">
                <div className="flex justify-between text-[11px] font-medium text-[#65796C] mb-1.5">
                  <span>Share of Gross Positive Footprint</span>
                  <span>{report.largest_source.percentage_of_gross}% ({report.largest_source.emissions_kg} / {report.total_gross_emissions_kg} kg)</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#E5ECE3]">
                  <div
                    className="h-full rounded-full bg-[#285943] transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, report.largest_source.percentage_of_gross))}%` }}
                  />
                </div>
              </div>
            </Card>
          )}

          {/* SECTION C: Emissions Breakdown (3 Category Cards) */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-[.14em] text-[#788A7D]">
                Emissions Breakdown by Activity
              </h3>
              <span className="text-xs text-[#8A9C8F]">Deterministic backend accounting</span>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              {report.categories.map((cat) => {
                const isNegative = cat.status === 'negative_credit' || cat.emissions_kg < 0
                const isZero = cat.emissions_kg === 0
                return (
                  <Card
                    key={cat.name}
                    className={`flex flex-col justify-between p-5 transition-all ${
                      isNegative
                        ? 'border-[#A3D2A0] bg-[#F5FBF4]'
                        : 'border-[#E0E8DF] bg-white hover:border-[#B5CEB2]'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span
                          className={`grid h-8 w-8 place-items-center rounded-lg ${
                            isNegative
                              ? 'bg-[#E3F4E0] text-[#1E7E34]'
                              : 'bg-[#EEF3ED] text-[#285943]'
                          }`}
                        >
                          {cat.name.toLowerCase().includes('elec') ? (
                            <Zap size={16} />
                          ) : cat.name.toLowerCase().includes('trans') ? (
                            <Truck size={16} />
                          ) : (
                            <Package size={16} />
                          )}
                        </span>
                        <Pill tone={isNegative ? 'green' : isZero ? 'sage' : 'amber'}>
                          {isNegative ? 'Net Diversion Offset' : isZero ? 'Zero Logged' : 'Operational Stream'}
                        </Pill>
                      </div>

                      <h4 className="mt-3 text-sm font-semibold text-[#28352D]">{cat.name}</h4>
                      <p className="mt-1 text-2xl font-bold tracking-tight text-[#28352D]">
                        {isNegative ? '' : ''}
                        {cat.emissions_kg.toLocaleString()}
                        <span className="ml-1 text-xs font-normal text-[#788B7D]">kg CO₂e</span>
                      </p>

                      <p className="mt-2 text-xs leading-5 text-[#5F7365]">
                        {cat.note}
                      </p>
                    </div>

                    <div className="mt-4 border-t border-[#EAEFE8] pt-3 text-[11px] text-[#7A8E80] flex items-center justify-between">
                      <span>
                        {cat.record_count !== undefined
                          ? `${cat.record_count} activity record(s)`
                          : 'Unmetered activity'}
                      </span>
                      {cat.percentage_of_gross !== null && cat.percentage_of_gross !== undefined && (
                        <span className="font-semibold text-[#304739]">
                          {cat.percentage_of_gross}% of gross
                        </span>
                      )}
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>

          {/* SECTION D: Visual Comparison (Horizontal Bar Chart) */}
          <Card className="p-5 sm:p-6">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between border-b border-[#EDF1EB] pb-4">
              <div>
                <h3 className="font-semibold text-[#28352D]">Portfolio Emissions Comparison</h3>
                <p className="text-xs text-[#7A8C80]">
                  Comparative net impact in kg CO₂e (positive emissions vs. recovery offset credits)
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs text-[#6B7D70]">
                <div className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#285943]" />
                  <span>Emissions (kg CO₂e)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#22C55E]" />
                  <span>Circular Offset Credit</span>
                </div>
              </div>
            </div>

            <div className="mt-5 h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#EBEFEA" />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 11, fill: '#7A8C80' }}
                    unit=" kg"
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 12, fill: '#28352D' }}
                    axisLine={false}
                    tickLine={false}
                    width={100}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 12,
                      border: '1px solid #D8E2D6',
                      fontSize: 12,
                      backgroundColor: '#FFFFFF',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                    }}
                    formatter={(val: any) => [`${Number(val).toLocaleString()} kg CO₂e`, 'Emissions Impact']}
                  />
                  <ReferenceLine x={0} stroke="#8AA190" strokeWidth={1.5} />
                  <Bar dataKey="emissions_kg" radius={[0, 4, 4, 0]} barSize={22}>
                    {chartData.map((entry) => (
                      <Cell
                        key={`cell-${entry.name}`}
                        fill={entry.emissions_kg < 0 ? '#22C55E' : '#285943'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* SECTION E: Key Analytical Findings */}
          {report.key_findings && report.key_findings.length > 0 && (
            <Card className="p-5 sm:p-6">
              <div className="flex items-center gap-2.5 mb-4">
                <span className="grid h-7 w-7 place-items-center rounded-md bg-[#EBF3E8] text-[#285943]">
                  <Compass size={15} />
                </span>
                <h3 className="font-semibold text-[#28352D]">Key Sustainability Findings</h3>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {report.key_findings.map((finding, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-[#E3EDE0] bg-[#FAFCF8] p-4 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[#8DA092]">
                        <span className="text-[10px] font-bold tracking-[.12em] uppercase">Insight 0{idx + 1}</span>
                        {finding.category && <Pill tone="sage">{finding.category}</Pill>}
                      </div>
                      <h4 className="mt-2 text-xs font-bold text-[#28352D]">{finding.title}</h4>
                      <p className="mt-1 text-xs leading-5 text-[#5B6F61]">{finding.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* SECTION F: Recommended Abatement Actions */}
          {report.recommendations && report.recommendations.length > 0 && (
            <Card className="p-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <span className="grid h-7 w-7 place-items-center rounded-md bg-[#EBF3E8] text-[#285943]">
                    <Lightbulb size={15} />
                  </span>
                  <div>
                    <h3 className="font-semibold text-[#28352D]">Prioritized Decarbonization Actions</h3>
                    <p className="text-xs text-[#7A8C80]">Tailored interventions based on your verified emission streams</p>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {report.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col justify-between rounded-xl border border-[#DFE7DD] bg-white p-4.5 hover:border-[#98BA93] transition-all shadow-2xs"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <Pill tone={rec.priority === 'High' ? 'amber' : rec.priority === 'Medium' ? 'sage' : 'green'}>
                          {rec.priority} Priority
                        </Pill>
                        <span className="text-[10px] font-medium text-[#7C8F81]">{rec.category}</span>
                      </div>

                      <h4 className="mt-3 text-sm font-semibold text-[#28352D]">{rec.title}</h4>
                      <p className="mt-1 text-xs leading-5 text-[#5F7365]">{rec.explanation}</p>

                      <div className="mt-3 rounded-lg bg-[#F5F8F4] p-2.5 text-[11px] text-[#475C4E]">
                        <span className="font-semibold text-[#285943]">Expected Benefit:</span> {rec.expected_benefit}
                      </div>
                    </div>

                    {rec.action_url && (
                      <div className="mt-4 pt-3 border-t border-[#EEF3ED]">
                        <Button
                          variant="secondary"
                          onClick={() => router.push(rec.action_url!)}
                          className="w-full text-xs justify-between"
                        >
                          <span>{rec.action_label || 'View Module'}</span>
                          <ArrowRight size={13} />
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Interactive AI Query Bar */}
          <Card className="p-5 sm:p-6 bg-[#FAFCF8]">
            <div className="flex items-center gap-3 border-b border-[#EDF1EB] pb-4">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#285943] text-white">
                <BrainCircuit size={17} />
              </span>
              <div>
                <h3 className="font-semibold text-[#28352D]">Interactive Sustainability Analyst</h3>
                <p className="text-xs text-[#7A8C80]">Ask in-depth questions about emission factors, reduction pathways, or period anomalies</p>
              </div>
            </div>

            {/* Answer Display */}
            {chatAnswer && (
              <div className="mt-5">
                <AIResponseRenderer
                  response={chatAnswer}
                  structuredPayload={chatPayload}
                  category="insights"
                />
              </div>
            )}

            {/* Input Form */}
            <div className="mt-4 flex gap-2">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAskCustomQuestion(question)
                }}
                disabled={isLoading}
                placeholder="Ask specific questions about your portfolio emissions..."
                className="field mt-0 bg-white"
              />
              <Button
                onClick={() => handleAskCustomQuestion(question)}
                disabled={isLoading || !question.trim()}
                className="shrink-0 bg-[#285943] text-white"
              >
                {isLoading ? <Loader2 size={15} className="animate-spin" /> : <ArrowRight size={15} />}
              </Button>
            </div>
          </Card>

          {/* Audit Guarantee Footnote */}
          <div className="rounded-xl border border-[#DFEBDD] bg-[#F0F6EE] px-4 py-3 text-xs text-[#586C5C] flex items-center gap-2">
            <CheckCircle2 size={15} className="shrink-0 text-[#285943]" />
            <span>
              <strong>Methodology & Assurance:</strong> Emission totals and category proportions originate exclusively from verified backend calculations (Central Electricity Authority CEA v19, IPCC 2006/2019, GHG Protocol). The language model synthesizes insights without fabricating metrics.
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
