"use client";

import React from 'react';
import { Order } from '@/lib/api';
import { Download, BookOpen } from 'lucide-react';
import Link from 'next/link';

interface BookViewerProps {
    order: Order;
}

export default function BookViewer({ order }: BookViewerProps) {
    return (
        <div className="min-h-screen bg-slate-50 py-12 px-4">
            <div className="max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <div className="text-center space-y-4">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 text-blue-600 rounded-full mb-4">
                        <BookOpen className="w-8 h-8" />
                    </div>
                    <h1 className="text-4xl font-extrabold text-slate-900">Meet {order.child_name}!</h1>
                    <p className="text-lg text-slate-600">Your personalized storybook is ready.</p>
                </div>

            </div>

            {/* Story Pages Section */}
            <div className="space-y-6">
                <h3 className="text-2xl font-bold text-slate-900 text-center">Your Story Pages</h3>

                {order.generated_pages && order.generated_pages.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {order.generated_pages
                            .sort((a, b) => a.page_number - b.page_number)
                            .map((page) => (
                                <div key={page.page_number} className="bg-white p-4 rounded-xl shadow-lg border border-slate-100 transform hover:scale-[1.02] transition duration-300">
                                    <div className="aspect-[4/5] relative bg-slate-100 rounded-lg overflow-hidden mb-4">
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img
                                            src={`${page.image_url}?t=${Date.now()}`}
                                            alt={`Page ${page.page_number}`}
                                            className="absolute inset-0 w-full h-full object-contain"
                                        />
                                    </div>
                                    <p className="text-center font-bold text-slate-500">Page {page.page_number}</p>
                                </div>
                            ))}
                    </div>
                ) : (
                    <div className="text-center p-12 bg-white rounded-2xl border-2 border-dashed border-slate-200">
                        <p className="text-slate-400">Pages are being assembled...</p>
                    </div>
                )}
            </div>

            {/* Main Character Asset (Moved down or kept as secondary) */}
            <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-slate-100">
                <div className="grid md:grid-cols-2 gap-0">
                    <div className="p-8 md:p-12 flex flex-col justify-center space-y-6">
                        <div>
                            <h3 className="text-xl font-bold text-slate-800 mb-2">The Hero Character</h3>
                            <p className="text-slate-500 leading-relaxed">
                                This is the AI-generated character face used in the story.
                            </p>
                        </div>

                        {/* ... keep existing buttons ... */}
                    </div>

                    <div className="bg-slate-100 flex items-center justify-center p-8">
                        {order.character_asset_url && (
                            <img
                                src={order.character_asset_url}
                                alt="Hero Character"
                                className="w-48 h-48 rounded-full border-4 border-white shadow-lg"
                            />
                        )}
                    </div>
                </div>

                {/* Preview / PDF Section (Mockup for Phase 1/2) */}
                {order.pdf_url && (
                    <div className="bg-blue-900 text-white rounded-2xl p-8 flex items-center justify-between">
                        <div>
                            <h3 className="text-xl font-bold">Full PDF Ready</h3>
                            <p className="text-blue-200">Download the complete 26-page storybook.</p>
                        </div>
                        <a
                            href={order.pdf_url}
                            className="px-8 py-3 bg-white text-blue-900 font-bold rounded-lg hover:bg-blue-50 transition shadow-lg"
                        >
                            Download PDF
                        </a>
                    </div>
                )}
            </div>
        </div>
    );
}
