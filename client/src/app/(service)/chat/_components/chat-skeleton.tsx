'use client';

import React from 'react';

export function MessageAreaSkeleton() {
  return (
    <div className="flex-1 px-5 py-4 space-y-4">
      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className="space-y-3">
          <div className="flex gap-2">
            <div className="w-8 h-8 bg-red-200 rounded-full animate-pulse flex-shrink-0" />
            <div className="space-y-2 flex-1 max-w-[80%]">
              <div className="h-3 bg-gray-200 rounded w-3/4 animate-pulse" />
              <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
            </div>
          </div>

          {/* 사용자 메시지 스켈레톤 */}
          {index < 2 && (
            <div className="flex justify-end">
              <div className="h-3 bg-gray-300 rounded w-1/3 animate-pulse" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
