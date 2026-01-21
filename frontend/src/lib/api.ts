import axios from 'axios';

// Smart API Base: Bypass Next.js Proxy on Localhost to avoid Body Size Limits/Timeouts
// For Ngrok/Production, use relative path to route through Next.js/Nginx
const getApiBase = () => {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  return ''; // Relative path for Proxies
};

const API_BASE = getApiBase();

// Story Types
export interface StoryPage {
  id: string;
  story_id: string;
  page_number: number;
  template_image_url: string;
  face_x: number;
  face_y: number;
  face_width: number;
  face_angle: number;
}

export interface Story {
  id: string;
  title: string;
  description: string | null;
  cover_image_url: string | null;
  price: number;
  created_at: string;
  pages?: StoryPage[];
}

export interface Order {
  id: string;
  status: string;
  created_at: string;
  child_name: string;
  photo_url: string;
  story_id: string | null;
  character_asset_url: string | null;
  pdf_url: string | null;
  failure_reason: string | null;
  generated_pages?: {
    page_number: number;
    image_url: string;
  }[];
}

// API Methods
export const api = {
  // Stories
  async getStories(): Promise<Story[]> {
    const response = await fetch(`${API_BASE}/api/v1/stories`);
    if (!response.ok) throw new Error("Failed to fetch stories");
    return response.json();
  },

  async getStory(storyId: string): Promise<Story> {
    const response = await fetch(`${API_BASE}/api/v1/stories/${storyId}`);
    if (!response.ok) throw new Error("Failed to fetch story");
    return response.json();
  },

  async seedStories(): Promise<{ message: string; story_id: string }> {
    const response = await fetch(`${API_BASE}/api/v1/stories/seed`, {
      method: "POST",
    });
    if (!response.ok) throw new Error("Failed to seed stories");
    return response.json();
  },

  async createStory(formData: FormData): Promise<Story> {
    const response = await fetch(`${API_BASE}/api/v1/stories`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to create story");
    }
    return response.json();
  },

  // Orders
  async uploadPhotos(
    files: File[]
  ): Promise<{
    url: string;
    valid: boolean;
    reason?: string;
    checks?: {
      face_detected: boolean;
      is_sharp: boolean;
      is_high_res: boolean;
      face_count: number;
      blur_score: number;
      resolution: string;
    }
  }> {
    const formData = new FormData();
    // Backend expects 'file' not 'files' and handles single upload
    formData.append("file", files[0]);

    const response = await fetch(`${API_BASE}/api/v1/orders/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed");
    }
    return response.json();
  },

  async createOrder(
    childName: string,
    photoUrl: string,
    storyId?: string,
    momName?: string,
    momPhotoUrl?: string
  ): Promise<Order> {
    const response = await fetch(`${API_BASE}/api/v1/orders/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        child_name: childName,
        photo_url: photoUrl,
        story_id: storyId || null,
        mom_name: momName,
        mom_photo_url: momPhotoUrl,
      }),
    });

    if (!response.ok) throw new Error("Failed to create order");
    return response.json();
  },

  async getOrder(orderId: string): Promise<Order> {
    const response = await fetch(`${API_BASE}/api/v1/orders/${orderId}`);
    if (!response.ok) throw new Error("Failed to fetch order");
    return response.json();
  },
};
