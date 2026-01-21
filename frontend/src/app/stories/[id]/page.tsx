"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, Story } from "@/lib/api";
import { ArrowLeft, BookOpen, Sparkles } from "lucide-react";
import Link from "next/link";

export default function StoryDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const storyId = params.id as string;

    const [story, setStory] = useState<Story | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStory();
    }, [storyId]);

    const loadStory = async () => {
        try {
            const data = await api.getStory(storyId);
            setStory(data);
        } catch (error) {
            console.error("Failed to load story:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-600 border-t-transparent"></div>
            </div>
        );
    }

    if (!story) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-800 mb-4">
                        Story Not Found
                    </h1>
                    <Link
                        href="/"
                        className="text-purple-600 hover:text-purple-700 font-semibold"
                    >
                        ← Back to Stories
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
            <div className="container mx-auto px-4 py-12">
                {/* Back Button */}
                <Link
                    href="/"
                    className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700 font-semibold mb-8"
                >
                    <ArrowLeft className="w-5 h-5" />
                    Back to Stories
                </Link>

                {/* Story Details */}
                <div className="bg-white rounded-2xl shadow-xl overflow-hidden max-w-4xl mx-auto">
                    {/* Cover Section */}
                    <div className="relative h-96 bg-gradient-to-br from-purple-400 to-pink-400">
                        {story.cover_image_url ? (
                            <img
                                src={story.cover_image_url}
                                alt={story.title}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <BookOpen className="w-32 h-32 text-white opacity-50" />
                            </div>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-8">
                            <h1 className="text-4xl font-bold text-white mb-2">
                                {story.title}
                            </h1>
                            <div className="flex items-center gap-4">
                                <span className="bg-white px-4 py-2 rounded-full text-lg font-bold text-purple-600">
                                    ${story.price.toFixed(2)}
                                </span>
                                {story.pages && (
                                    <span className="text-white text-sm">
                                        {story.pages.length} pages
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Description */}
                    <div className="p-8">
                        <div className="mb-8">
                            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                                About This Story
                            </h2>
                            <p className="text-gray-600 text-lg leading-relaxed">
                                {story.description || "A magical adventure awaits..."}
                            </p>
                        </div>

                        {/* Page Preview */}
                        {story.pages && story.pages.length > 0 && (
                            <div className="mb-8">
                                <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                                    Page Preview
                                </h2>
                                <div className="grid grid-cols-3 gap-4">
                                    {story.pages.slice(0, 3).map((page) => (
                                        <div
                                            key={page.id}
                                            className="aspect-[4/5] bg-gray-100 rounded-lg overflow-hidden"
                                        >
                                            <img
                                                src={page.template_image_url}
                                                alt={`Page ${page.page_number}`}
                                                className="w-full h-full object-cover"
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* CTA Button */}
                        <div className="flex justify-center">
                            <Link
                                href={`/create?story_id=${story.id}`}
                                className="group relative inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full text-lg font-bold shadow-lg hover:shadow-xl transition-all hover:scale-105"
                            >
                                <Sparkles className="w-6 h-6" />
                                Create This Book
                                <div className="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-20 transition-opacity"></div>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
