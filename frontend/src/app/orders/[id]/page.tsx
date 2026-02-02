"use client";

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, Order } from '@/lib/api';
import BookViewer from '@/components/BookViewer';
import { Loader2, AlertTriangle } from 'lucide-react';

export default function OrderStatusPage() {
    const params = useParams();
    const id = params.id as string;
    const [order, setOrder] = useState<Order | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [elapsedTime, setElapsedTime] = useState(0);

    useEffect(() => {
        let intervalId: NodeJS.Timeout;
        let timerId: NodeJS.Timeout;

        const fetchOrder = async () => {
            try {
                const data = await api.getOrder(id);
                setOrder(data);

                if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                    setLoading(false);
                    clearInterval(intervalId); // Stop polling
                    clearInterval(timerId); // Stop timer
                } else {
                    setLoading(true);
                }
            } catch (err) {
                console.error(err);
                setError("Failed to fetch order status");
                setLoading(false);
                clearInterval(intervalId);
                clearInterval(timerId);
            }
        };

        // Timer Logic
        const startTime = Date.now();
        timerId = setInterval(() => {
            setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
        }, 1000);

        // Initial fetch
        fetchOrder();

        // Poll every 3 seconds
        intervalId = setInterval(fetchOrder, 3000);

        return () => {
            clearInterval(intervalId);
            clearInterval(timerId);
        };
    }, [id]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="text-center p-8 bg-white rounded-2xl shadow-xl max-w-md">
                    <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-slate-800">Something went wrong</h2>
                    <p className="text-slate-500 mt-2">{error}</p>
                </div>
            </div>
        );
    }

    // Waiting Room
    if (loading || (order && order.status !== 'COMPLETED' && order.status !== 'FAILED')) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-4">
                <div className="text-center space-y-6 max-w-lg">
                    <div className="relative w-24 h-24 mx-auto">
                        <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
                        <Loader2 className="absolute inset-0 m-auto w-10 h-10 text-blue-600 animate-pulse" />
                    </div>

                    <div>
                        <h2 className="text-2xl font-bold text-slate-800">Painting your story...</h2>
                        <p className="text-slate-500 mt-2">
                            {order?.status === 'PROCESSING' ?
                                "Our AI artists are sketching your child's character..." :
                                "Queuing your request..."}
                        </p>
                        <p className="text-xl font-mono text-blue-600 mt-4">{elapsedTime}s</p>
                        <p className="text-xs text-slate-400 mt-1">This takes about 4-5 minutes. Please don't close this tab.</p>
                    </div>
                </div>
            </div>
        );
    }

    // Failed State
    if (order?.status === 'FAILED') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="text-center p-8 bg-white rounded-2xl shadow-xl max-w-md border border-red-100">
                    <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-slate-800">Generation Failed</h2>
                    <p className="text-slate-500 mt-2">We couldn't generate the storybook.</p>
                    {order.failure_reason && <p className="text-sm text-red-400 mt-2 bg-red-50 p-2 rounded">{order.failure_reason}</p>}
                    <button
                        onClick={() => window.location.href = '/create'}
                        className="mt-6 px-6 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    // Completed State
    return (
        <div className="relative">
            <div className="absolute top-4 right-4 bg-white/80 backdrop-blur px-3 py-1 rounded-full text-xs font-medium text-slate-500 shadow-sm z-50">
                Generated in {elapsedTime}s
            </div>
            <BookViewer order={order!} />
        </div>
    );
}
