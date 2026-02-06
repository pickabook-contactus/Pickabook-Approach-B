"use client";

import React, { useState, Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import UploadZone from '@/components/UploadZone';
import { api, Book } from '@/lib/api';
import { Loader2, BookOpen, UserPlus } from 'lucide-react';

function CreatePageContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    // Dynamic Books
    const [books, setBooks] = useState<Book[]>([]);
    const [selectedBook, setSelectedBook] = useState<string>('magic_of_money'); // Default to Magic of Money

    // Fetch Books
    useEffect(() => {
        api.getBooks().then(data => {
            setBooks(data);
            // Only overwrite if no selection or if strictly needed.
            // Current default is 'magic_of_money' (hardcoded on Line 15).
            // If data doesn't contain it, fallback to first.
            // If data contains it, keep it.
            const hasMagic = data.find(b => b.id === 'magic_of_money');
            if (hasMagic) {
                setSelectedBook('magic_of_money');
            } else if (data.length > 0) {
                setSelectedBook(data[0].id);
            }
        }).catch(err => console.error(err));
    }, []);

    const [childName, setChildName] = useState('');
    const [childPhotoUrl, setChildPhotoUrl] = useState<string | null>(null);

    // Secondary Character (Mom) - Logic: If book matches specific ID or Metadata (hardcoded for now)
    // Actually, backend needs to tell us if Mom photo involves. 
    // For now, let's assume 'magic_of_money' requires Mom.
    const [momName, setMomName] = useState('');
    const [momPhotoUrl, setMomPhotoUrl] = useState<string | null>(null);

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const isMagicBook = selectedBook === 'magic_of_money';

        // Validation
        if (!childName || !childPhotoUrl) return;
        if (isMagicBook && (!momName || !momPhotoUrl)) return;

        setSubmitting(true);
        setError(null);

        try {
            const order = await api.createOrder(
                childName,
                childPhotoUrl,
                selectedBook,
                isMagicBook ? momName : undefined,
                isMagicBook ? momPhotoUrl || undefined : undefined
            );
            router.push(`/orders/${order.id}`);
        } catch (err) {
            setError("Failed to create order. Please try again.");
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-slate-900">Create a Story</h1>
                    <p className="text-slate-500 mt-2">Bring your family into the world of books.</p>
                </div>

                {/* Book Selector (Dynamic) */}
                <div className="grid grid-cols-2 gap-4 mb-8">
                    {books.length === 0 ? (
                        <div className="col-span-2 text-center text-slate-400 py-4">Loading Library...</div>
                    ) : (
                        books.map((book) => (
                            <button
                                key={book.id}
                                type="button"
                                onClick={() => setSelectedBook(book.id)}
                                className={`p-4 rounded-xl border-2 transition-all ${selectedBook === book.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}
                            >
                                <BookOpen className={`w-8 h-8 mb-2 ${selectedBook === book.id ? 'text-blue-500' : 'text-slate-400'}`} />
                                <h3 className="font-semibold text-slate-900">{book.title}</h3>
                                {book.id === 'magic_of_money' && <p className="text-xs text-slate-500">For Kid & Mom</p>}
                            </button>
                        ))
                    )}
                </div>

                <form onSubmit={handleSubmit} className="space-y-8">

                    {/* Character 1: Child */}
                    <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
                        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            👶 The Child
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={childName}
                                    onChange={(e) => setChildName(e.target.value)}
                                    className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none text-slate-900"
                                    placeholder="e.g. Alice"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Photo</label>
                                <UploadZone onUploadComplete={setChildPhotoUrl} />
                            </div>
                        </div>
                    </div>

                    {/* Character 2: Mom (Conditional) */}
                    {selectedBook === 'magic_of_money' && (
                        <div className="bg-pink-50 p-6 rounded-xl border border-pink-100">
                            <h2 className="text-lg font-semibold text-pink-900 mb-4 flex items-center gap-2">
                                👩 The Mother
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-pink-800 mb-1">Name</label>
                                    <input
                                        type="text"
                                        value={momName}
                                        onChange={(e) => setMomName(e.target.value)}
                                        className="w-full px-4 py-2 rounded-lg border border-pink-200 focus:ring-2 focus:ring-pink-500 outline-none text-pink-900"
                                        placeholder="e.g. Sarah"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-pink-800 mb-1">Photo</label>
                                    <UploadZone onUploadComplete={setMomPhotoUrl} />
                                </div>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm text-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={!childName || !childPhotoUrl || submitting}
                        className={`
                            w-full py-4 px-6 rounded-xl text-white font-bold text-lg shadow-lg flex items-center justify-center gap-2
                            transition-all transform active:scale-95
                            ${(!childName || !childPhotoUrl || submitting) ? 'bg-slate-300 cursor-not-allowed text-slate-500' : 'bg-blue-600 hover:bg-blue-700 hover:shadow-xl'}
                        `}
                    >
                        {submitting ? (
                            <>
                                <Loader2 className="animate-spin" /> Creating Magic...
                            </>
                        ) : "Create Storybook"}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default function CreatePage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>}>
            <CreatePageContent />
        </Suspense>
    );
}
