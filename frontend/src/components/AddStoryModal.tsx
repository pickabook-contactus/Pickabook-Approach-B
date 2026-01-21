"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { X, Upload, Loader2, FileJson, Image as ImageIcon } from "lucide-react";

interface AddStoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export default function AddStoryModal({ isOpen, onClose, onSuccess }: AddStoryModalProps) {
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [coverFile, setCoverFile] = useState<File | null>(null);
    const [pageFiles, setPageFiles] = useState<File[]>([]);
    const [jsonContent, setJsonContent] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!coverFile || pageFiles.length === 0 || !jsonContent) return;

        setLoading(true);
        setError(null);

        try {
            // Validate JSON first
            try {
                JSON.parse(jsonContent);
            } catch (err) {
                throw new Error("Invalid JSON Format. Please check syntax.");
            }

            const formData = new FormData();
            formData.append("title", title);
            formData.append("description", description);
            formData.append("cover_image", coverFile);

            // Append all pages
            pageFiles.forEach((file) => {
                formData.append("page_images", file);
            });

            formData.append("pages_json", jsonContent);

            await api.createStory(formData);
            onSuccess();
            onClose();
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Failed to upload story.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100">
                    <h2 className="text-2xl font-bold text-gray-800">Add New Storybook</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
                        <X className="w-6 h-6 text-gray-500" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">

                    {/* Title & Desc */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Book Title</label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-purple-500 text-slate-900"
                                placeholder="The Magic Forest"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-purple-500 text-slate-900"
                                rows={3}
                                placeholder="A wonderful journey..."
                                required
                            />
                        </div>
                    </div>

                    {/* Setup Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Cover Image */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Cover Image</label>
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition-colors relative">
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={(e) => setCoverFile(e.target.files?.[0] || null)}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                />
                                {coverFile ? (
                                    <div className="flex items-center justify-center gap-2 text-green-600">
                                        <ImageIcon className="w-5 h-5" />
                                        <span className="truncate max-w-[150px]">{coverFile.name}</span>
                                    </div>
                                ) : (
                                    <div className="text-gray-400">
                                        <Upload className="w-8 h-8 mx-auto mb-2" />
                                        <span className="text-sm">Upload Cover</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Pages */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Story Pages</label>
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition-colors relative">
                                <input
                                    type="file"
                                    accept="image/*"
                                    multiple
                                    onChange={(e) => setPageFiles(Array.from(e.target.files || []))}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                />
                                {pageFiles.length > 0 ? (
                                    <div className="flex items-center justify-center gap-2 text-green-600">
                                        <ImageIcon className="w-5 h-5" />
                                        <span>{pageFiles.length} Pages Selected</span>
                                    </div>
                                ) : (
                                    <div className="text-gray-400">
                                        <Upload className="w-8 h-8 mx-auto mb-2" />
                                        <span className="text-sm">Upload Pages</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* JSON Metadata */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <label className="block text-sm font-medium text-gray-700">Face Coordinates JSON</label>
                            <span className="text-xs text-gray-500 font-mono">
                                [{"{"} "filename": "page1.png", "x": 100... {"}"}]
                            </span>
                        </div>
                        <textarea
                            value={jsonContent}
                            onChange={(e) => setJsonContent(e.target.value)}
                            className="w-full px-4 py-2 rounded-lg border font-mono text-xs focus:ring-2 focus:ring-purple-500 text-slate-900 bg-slate-50"
                            rows={6}
                            placeholder={'[\n  {\n    "filename": "page1.png",\n    "x": 380,\n    "y": 125,\n    "w": 385\n  }\n]'}
                            required
                        />
                    </div>

                    {error && (
                        <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading || !coverFile || pageFiles.length === 0}
                            className={`px-6 py-2 rounded-lg text-white font-medium flex items-center gap-2
                ${loading ? 'bg-purple-400' : 'bg-purple-600 hover:bg-purple-700'}
              `}
                        >
                            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                            {loading ? "Uploading..." : "Create Story"}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}
