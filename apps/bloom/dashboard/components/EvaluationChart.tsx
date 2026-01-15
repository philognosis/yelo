'use client';

import React from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';
import Card from './Card';

export interface ChartDataPoint {
  name: string;
  [key: string]: string | number;
}

export interface EvaluationChartProps {
  data: ChartDataPoint[];
  type: 'area' | 'bar' | 'line' | 'pie';
  title?: string;
  description?: string;
  dataKeys?: string[];
  colors?: string[];
  height?: number;
  isLoading?: boolean;
  showLegend?: boolean;
  showGrid?: boolean;
}

const defaultColors = [
  '#3b82f6', // blue
  '#8b5cf6', // purple
  '#10b981', // green
  '#f59e0b', // yellow
  '#ef4444', // red
  '#06b6d4', // cyan
];

export default function EvaluationChart({
  data,
  type,
  title,
  description,
  dataKeys = [],
  colors = defaultColors,
  height = 300,
  isLoading = false,
  showLegend = true,
  showGrid = true,
}: EvaluationChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
          <p className="mb-2 font-semibold text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="space-y-4 text-center">
            <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
            <p className="text-sm text-gray-500">Loading chart data...</p>
          </div>
        </div>
      );
    }

    if (!data || data.length === 0) {
      return (
        <div className="flex items-center justify-center" style={{ height }}>
          <p className="text-sm text-gray-500">No data available</p>
        </div>
      );
    }

    const commonProps = {
      data,
      margin: { top: 10, right: 30, left: 0, bottom: 0 },
    };

    switch (type) {
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart {...commonProps}>
              {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
              <XAxis
                dataKey="name"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              {dataKeys.map((key, index) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.6}
                  strokeWidth={2}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart {...commonProps}>
              {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
              <XAxis
                dataKey="name"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              {dataKeys.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[index % colors.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart {...commonProps}>
              {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
              <XAxis
                dataKey="name"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              {dataKeys.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        const pieDataKey = dataKeys[0] || 'value';
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey={pieDataKey}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <Card>
      {(title || description) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-4"
        >
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          )}
          {description && (
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          )}
        </motion.div>
      )}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {renderChart()}
      </motion.div>
    </Card>
  );
}
