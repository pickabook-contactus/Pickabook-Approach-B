"use client";

import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, Loader2, XCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface UploadZoneProps {
    onUploadComplete: (url: string) => void;
}

interface ValidationChecks {
    face_detected: boolean;
    is_sharp: boolean;
    is_high_res: boolean;
    face_count: number;
    blur_score: number;
    resolution: string;
}

export default function UploadZone({ onUploadComplete }: UploadZoneProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [checks, setChecks] = useState<ValidationChecks | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => {
        setIsDragOver(false);
    };

    const validateFile = (file: File): string | null => {
        if (file.size > 20 * 1024 * 1024) return "File size must be less than 20MB";
        if (!['image/jpeg', 'image/png'].includes(file.type)) return "Only JPEG or PNG images are allowed";
        return null;
    };

    const processFile = async (file: File) => {
        setError(null);
        setSuccess(false);
        setChecks(null);

        const validationError = validateFile(file);
        if (validationError) {
            setError(validationError);
            return;
        }

        setIsUploading(true);
        try {
            const result = await api.uploadPhotos([file]);

            if (result.checks) {
                setChecks(result.checks);
            }

            if (result.valid && result.url) {
                setSuccess(true);
                // Proceed only if valid
                setTimeout(() => onUploadComplete(result.url), 1000);
            } else {
                setError(result.reason || "Photo validation failed.");
            }
        } catch (err: any) {
            setError(err.message || "Failed to upload photo.");
        } finally {
            setIsUploading(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        const files = e.dataTransfer.files;
        if (files?.[0]) processFile(files[0]);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files?.[0]) processFile(files[0]);
    };

    const CheckItem = ({ label, passed, value }: { label: string; passed: boolean; value?: string | number }) => (
        <div className="flex items-center justify-between w-full py-2 border-b border-gray-100 last:border-0">
            <div className="flex items-center gap-2">
                {passed ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                )}
                <span className={`text-sm ${passed ? 'text-gray-700' : 'text-red-500 font-medium'}`}>{label}</span>
            </div>
            {value && <span className="text-xs text-gray-400">{value}</span>}
        </div>
    );

    return (
        <div className="w-full">
            <div
                onClick={() => !isUploading && fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
            border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all
            flex flex-col items-center justify-center gap-4
            ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-slate-400 hover:bg-slate-50'}
            ${isUploading ? 'opacity-50 pointer-events-none' : ''}
            ${error ? 'border-red-300 bg-red-50' : ''}
            ${success ? 'border-green-300 bg-green-50' : ''}
        `}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept="image/jpeg,image/png"
                    className="hidden"
                />

                {isUploading ? (
                    <div className="flex flex-col items-center text-blue-600">
                        <Loader2 className="w-10 h-10 animate-spin mb-2" />
                        <p className="font-medium">Analyzing photo quality...</p>
                    </div>
                ) : checks ? (
                    <div className="w-full max-w-sm">
                        <h4 className={`font-semibold mb-3 ${success ? 'text-green-600' : 'text-red-600'}`}>
                            {success ? "Photo Verified" : "Photo Quality Issues"}
                        </h4>
                        <div className="bg-white rounded-lg p-3 shadow-sm text-left">
                            <CheckItem
                                label="Single Face Detected"
                                passed={checks.face_detected}
                                value={`${checks.face_count} face(s)`}
                            />
                            <CheckItem
                                label="Resolution (>500px)"
                                passed={checks.is_high_res}
                                value={checks.resolution}
                            />
                            <CheckItem
                                label="Sharpness (Not Blurry)"
                                passed={checks.is_sharp}
                                value={`Score: ${checks.blur_score}`}
                            />
                        </div>
                        {!success && (
                            <p className="text-sm text-slate-500 mt-3">Click to try another photo</p>
                        )}
                    </div>
                ) : error ? (
                    <div className="flex flex-col items-center text-red-500">
                        <AlertCircle className="w-10 h-10 mb-2" />
                        <p className="font-medium">{error}</p>
                        <p className="text-sm mt-1 text-slate-500">Click to try again</p>
                    </div>
                ) : (
                    <>
                        <div className="p-4 bg-slate-100 rounded-full">
                            <UploadCloud className="w-8 h-8 text-slate-500" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-700">Click or drag photo here</h3>
                            <p className="text-sm text-slate-500 mt-1">JPEG or PNG, max 20MB</p>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
