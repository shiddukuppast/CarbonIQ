import { apiClient } from './api-client'
import type {
  AiChatMessage,
  BusRoute,
  ElectricityRecord,
  TransportationRecord,
  WasteRecord,
} from '@/types/sustainability'

/**
 * AI Advisors Service
 * Connects frontend advisor interfaces directly to verified FastAPI /ai endpoints.
 * Enforces zero fake, mock, or simulated LLM answers.
 * When GROQ_API_KEY is not configured on the backend, surfaces the HTTP 503 message directly.
 */

export const aiAdvisorsService = {
  /**
   * Electricity AI Advisor response engine
   */
  async queryElectricityAdvisor(
    question: string,
    ..._args: any[]
  ): Promise<AiChatMessage> {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    try {
      const backendRes = await apiClient.post<any>('/ai/electricity', { question })
      return {
        id: backendRes.id || `ai-elec-${Date.now()}`,
        role: 'assistant',
        content: backendRes.content,
        timestamp: backendRes.timestamp || timestamp,
        calculationBreakdown: backendRes.calculation_breakdown,
        suggestedFollowUps: backendRes.suggested_follow_ups,
        structuredPayload: backendRes.structured_payload,
      }
    } catch (err: any) {
      return {
        id: `err-elec-${Date.now()}`,
        role: 'assistant',
        content: err?.message || 'AI is not configured. Add GROQ_API_KEY to the backend environment and restart the server.',
        timestamp,
      }
    }
  },

  /**
   * Transportation AI Advisor response engine
   */
  async queryTransportationAdvisor(
    question: string,
    ..._args: any[]
  ): Promise<AiChatMessage> {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    try {
      const backendRes = await apiClient.post<any>('/ai/transportation', { question })
      return {
        id: backendRes.id || `ai-trans-${Date.now()}`,
        role: 'assistant',
        content: backendRes.content,
        timestamp: backendRes.timestamp || timestamp,
        calculationBreakdown: backendRes.calculation_breakdown,
        suggestedFollowUps: backendRes.suggested_follow_ups,
        structuredPayload: backendRes.structured_payload,
      }
    } catch (err: any) {
      return {
        id: `err-trans-${Date.now()}`,
        role: 'assistant',
        content: err?.message || 'AI is not configured. Add GROQ_API_KEY to the backend environment and restart the server.',
        timestamp,
      }
    }
  },

  /**
   * Waste Management AI Advisor response engine
   */
  async queryWasteAdvisor(
    question: string,
    ..._args: any[]
  ): Promise<AiChatMessage> {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    try {
      const backendRes = await apiClient.post<any>('/ai/waste', { question })
      return {
        id: backendRes.id || `ai-waste-${Date.now()}`,
        role: 'assistant',
        content: backendRes.content,
        timestamp: backendRes.timestamp || timestamp,
        calculationBreakdown: backendRes.calculation_breakdown,
        suggestedFollowUps: backendRes.suggested_follow_ups,
        structuredPayload: backendRes.structured_payload,
      }
    } catch (err: any) {
      return {
        id: `err-waste-${Date.now()}`,
        role: 'assistant',
        content: err?.message || 'AI is not configured. Add GROQ_API_KEY to the backend environment and restart the server.',
        timestamp,
      }
    }
  },

  /**
   * Cross-category Sustainability AI Insights Advisor
   */
  async queryInsightsAdvisor(question: string): Promise<AiChatMessage> {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    try {
      const backendRes = await apiClient.post<any>('/ai/insights', { question })
      return {
        id: backendRes.id || `ai-ins-${Date.now()}`,
        role: 'assistant',
        content: backendRes.content,
        timestamp: backendRes.timestamp || timestamp,
        calculationBreakdown: backendRes.calculation_breakdown,
        suggestedFollowUps: backendRes.suggested_follow_ups,
        structuredPayload: backendRes.structured_payload,
      }
    } catch (err: any) {
      return {
        id: `err-ins-${Date.now()}`,
        role: 'assistant',
        content: err?.message || 'AI is not configured. Add GROQ_API_KEY to the backend environment and restart the server.',
        timestamp,
      }
    }
  },
}
