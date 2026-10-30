'use client'

import React from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ElectricityData, WasteData } from '@/types/sustainability'

export interface ModuleBarChartProps {
  type: 'electricity' | 'transportation' | 'waste'
  electricityData: ElectricityData[]
  wasteData: WasteData[]
}

export function ModuleBarChart({
  type,
  electricityData,
  wasteData,
}: ModuleBarChartProps) {
  return (
    <div className="mt-6 h-[265px]">
      <ResponsiveContainer width="100%" height="100%">
        {type === 'electricity' ? (
          <BarChart data={electricityData} margin={{ left: -20, right: 0 }}>
            <CartesianGrid vertical={false} stroke="#EEF2ED" />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: '1px solid #E0E7DE',
                fontSize: 12,
              }}
            />
            <Bar
              dataKey="usage"
              name="kWh"
              fill="#8DAE83"
              radius={[5, 5, 0, 0]}
              barSize={22}
            />
          </BarChart>
        ) : type === 'transportation' ? (
          <BarChart data={electricityData} margin={{ left: -20, right: 0 }}>
            <CartesianGrid vertical={false} stroke="#EEF2ED" />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: '1px solid #E0E7DE',
                fontSize: 12,
              }}
            />
            <Bar
              dataKey="usage"
              name="Distance"
              fill="#B6B86B"
              radius={[5, 5, 0, 0]}
              barSize={22}
            />
          </BarChart>
        ) : (
          <BarChart data={wasteData} margin={{ left: -20, right: 0 }}>
            <CartesianGrid vertical={false} stroke="#EEF2ED" />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#94A098' }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: '1px solid #E0E7DE',
                fontSize: 12,
              }}
            />
            <Bar
              dataKey="generated"
              name="Generated"
              fill="#B6B86B"
              radius={[5, 5, 0, 0]}
              barSize={20}
            />
            <Bar
              dataKey="recycled"
              name="Recovered"
              fill="#8DAE83"
              radius={[5, 5, 0, 0]}
              barSize={20}
            />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
