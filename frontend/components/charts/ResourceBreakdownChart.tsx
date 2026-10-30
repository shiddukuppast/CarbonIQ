'use client'

import React from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'
import type { ResourceBreakdown } from '@/types/sustainability'

export interface ResourceBreakdownChartProps {
  data: ResourceBreakdown[]
  totalLabel?: string
  totalSublabel?: string
}

export function ResourceBreakdownChart({
  data,
  totalLabel = '2.48t',
  totalSublabel = 'total CO₂e',
}: ResourceBreakdownChartProps) {
  return (
    <div className="h-[180px] w-[180px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            innerRadius={57}
            outerRadius={78}
            paddingAngle={3}
            strokeWidth={0}
          >
            {data.map((item) => (
              <Cell key={item.name} fill={item.color} />
            ))}
          </Pie>
          <text
            x="50%"
            y="48%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-[#2F4436] text-[22px] font-semibold"
          >
            {totalLabel}
          </text>
          <text
            x="50%"
            y="61%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-[#8A978D] text-[10px]"
          >
            {totalSublabel}
          </text>
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
