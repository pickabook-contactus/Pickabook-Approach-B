"use client";

import { useEffect, useState } from "react";
import { api, Story } from "@/lib/api";
import Link from "next/link";
import { BookOpen, Sparkles } from "lucide-react";
import AddStoryModal from "@/components/AddStoryModal";

export default function Home() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadStories();
  }, []);

  const loadStories = async () => {
    try {
      const data = await api.getStories();
      setStories(data);
    } catch (error) {
      console.error("Failed to load stories:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedStories = async () => {
    try {
      await api.seedStories();
      await loadStories();
    } catch (error) {
      console.error("Failed to seed stories:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12 relative">
          <div className="absolute top-0 right-0">
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-purple-100 text-purple-700 px-4 py-2 rounded-full font-medium text-sm hover:bg-purple-200 transition-colors flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> Add Story
            </button>
          </div>

          <div className="flex items-center justify-center gap-3 mb-4">
            <BookOpen className="w-12 h-12 text-purple-600" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              PickaBook
            </h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Create magical personalized storybooks where your child is the main
            character—not just by name, but by face.
          </p>
        </div>

        <AddStoryModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            loadStories();
            setShowAddModal(false);
          }}
        />

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-600 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading stories...</p>
          </div>
        )}

        {/* Empty State with Seed Button */}
        {!loading && stories.length === 0 && (
          <div className="text-center py-12 bg-white rounded-2xl shadow-lg max-w-md mx-auto">
            <Sparkles className="w-16 h-16 text-purple-600 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold mb-2">No Stories Yet</h2>
            <p className="text-gray-600 mb-6">
              Get started by seeding demo stories
            </p>
            <button
              onClick={handleSeedStories}
              className="px-6 py-3 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors font-semibold"
            >
              Seed Demo Stories
            </button>
          </div>
        )}

        {/* Story Grid */}
        {!loading && stories.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {stories.map((story) => (
              <Link
                key={story.id}
                href={`/stories/${story.id}`}
                className="group"
              >
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden transition-all hover:shadow-2xl hover:-translate-y-1">
                  {/* Cover Image */}
                  <div className="relative h-64 bg-gradient-to-br from-purple-400 to-pink-400">
                    {story.cover_image_url ? (
                      <img
                        src={story.cover_image_url}
                        alt={story.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <BookOpen className="w-24 h-24 text-white opacity-50" />
                      </div>
                    )}
                    <div className="absolute top-4 right-4 bg-white px-3 py-1 rounded-full text-sm font-semibold text-purple-600">
                      ${story.price.toFixed(2)}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <h2 className="text-2xl font-bold text-gray-800 mb-2 group-hover:text-purple-600 transition-colors">
                      {story.title}
                    </h2>
                    <p className="text-gray-600 line-clamp-3">
                      {story.description || "A magical adventure awaits..."}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
