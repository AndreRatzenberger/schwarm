'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const data = [
  { name: 'Agent 1', tasks: 40, errors: 4 },
  { name: 'Agent 2', tasks: 30, errors: 2 },
  { name: 'Agent 3', tasks: 50, errors: 3 },
  { name: 'Agent 4', tasks: 25, errors: 1 },
  { name: 'Agent 5', tasks: 35, errors: 5 },
]

export default function AgentStatistics() {
  return (
    <div className="h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="tasks" fill="#3b82f6" />
          <Bar dataKey="errors" fill="#ef4444" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

