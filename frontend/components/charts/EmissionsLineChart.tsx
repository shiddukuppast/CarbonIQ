'use client'

import React from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { COLOR_GREEN } from '@/lib/constants'
import type { MonthlyEmission } from '@/types/sustainability'

export interface ExtendedMonthlyEmission extends MonthlyEmission {
  forecast?: number
  isProjected?: boolean
}

export interface EmissionsLineChartProps {
  data: ExtendedMonthlyEmission[]
  height?: number
  showAxes?: boolean
}

export function EmissionsLineChart({
  data,
  height = 230,
  showAxes = true,
}: EmissionsLineChartProps) {
  return (
    <div style={{ height: `${height}px` }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ left: showAxes ? -20 : 0, right: 4, top: 8, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="#EEF2ED" />
          <XAxis
            dataKey="month"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: showAxes ? 11 : 10, fill: '#94A098' }}
          />
          {showAxes ? (
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
              tickFormatter={(v) => `${v / 1000}k`}
            />
          ) : (
            <YAxis hide />
          )}
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: '1px solid #E0E7DE',
              fontSize: 12,
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            name="Measured Emissions"
            stroke={COLOR_GREEN}
            strokeWidth={showAxes ? 3 : 2.5}
            dot={{ r: showAxes ? 4 : 3, fill: COLOR_GREEN, strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            name="ML Projected Forecast"
            stroke="#C084FC"
            strokeDasharray="4 4"
            strokeWidth={2}
            dot={{ r: 4, fill: '#C084FC', strokeWidth: 2, stroke: '#fff' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
